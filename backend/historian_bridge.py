import paho.mqtt.client as mqtt
import psycopg2
import json
import uuid
import time
import redis
from datetime import datetime, timezone

import os

# Configuración (Usa variables de entorno para Docker, fallback a localhost)
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "scada_user"),
    "password": os.getenv("DB_PASS", "scada_admin"),
    "dbname": os.getenv("DB_NAME", "scada_db")
}

REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": 0
}

# Conexión a Redis
r = redis.Redis(**REDIS_CONFIG, decode_responses=True)

# Conexión Global a la DB
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error conectando a TimescaleDB: {e}")
        return None

# Caché local para evitar consultas constantes a la DB
tag_cache = {}

def setup_database():
    conn = get_db_connection()
    if not conn: 
        return
    cur = conn.cursor()
    
    # 1. Tabla de Definición de Tags
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tag_definition (
            id SERIAL PRIMARY KEY,
            path TEXT UNIQUE NOT NULL,
            area TEXT,
            equipment TEXT,
            sensor_name TEXT,
            unit TEXT,
            data_type TEXT
        );
    """)
    
    # 2. Tabla de Históricos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historian (
            time TIMESTAMPTZ NOT NULL,
            tag_id INTEGER NOT NULL,
            value DOUBLE PRECISION,
            quality INTEGER
        );
    """)
    
    # 3. Tabla de Definición de Alarmas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alarm_definition (
            id SERIAL PRIMARY KEY,
            tag_id INTEGER REFERENCES tag_definition(id) ON DELETE CASCADE,
            operator TEXT NOT NULL DEFAULT '>',
            threshold DOUBLE PRECISION NOT NULL,
            priority TEXT DEFAULT 'MEDIUM',
            enabled BOOLEAN DEFAULT TRUE,
            message TEXT,
            UNIQUE(tag_id, operator, threshold)
        );
    """)

    # 4. Tabla de Alarmas Activas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alarm_active (
            id SERIAL PRIMARY KEY,
            definition_id INTEGER REFERENCES alarm_definition(id) ON DELETE CASCADE,
            start_time TIMESTAMPTZ NOT NULL,
            current_value DOUBLE PRECISION,
            max_value DOUBLE PRECISION,
            active_operator TEXT,
            active_threshold DOUBLE PRECISION,
            acknowledged BOOLEAN DEFAULT FALSE,
            ack_time TIMESTAMPTZ,
            UNIQUE(definition_id)
        );
    """)

    # 5. Histórico de Alarmas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alarm_history (
            id SERIAL PRIMARY KEY,
            definition_id INTEGER REFERENCES alarm_definition(id),
            start_time TIMESTAMPTZ NOT NULL,
            end_time TIMESTAMPTZ,
            max_value DOUBLE PRECISION,
            current_value DOUBLE PRECISION,
            priority TEXT,
            event_operator TEXT,
            event_threshold DOUBLE PRECISION,
            acknowledged BOOLEAN DEFAULT FALSE,
            ack_time TIMESTAMPTZ
        );
    """)

    # 6. Metadata de Sensores (movida desde backend_api)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_metadata (
            tag_id INTEGER PRIMARY KEY REFERENCES tag_definition(id) ON DELETE CASCADE,
            description TEXT,
            process_role TEXT,
            normal_range_min DOUBLE PRECISION,
            normal_range_max DOUBLE PRECISION,
            critical_range_min DOUBLE PRECISION,
            critical_range_max DOUBLE PRECISION,
            physical_location TEXT,
            related_system TEXT,
            failure_impact TEXT,
            operating_notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 7. Convertir historian en hypertable e índice
    try:
        cur.execute("SELECT create_hypertable('historian', 'time', if_not_exists => TRUE);")
    except:
        pass
        
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_tag_time 
        ON historian (tag_id, time DESC);
    """)
        
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base de Datos Industrial configurada completamente")

def get_tag_id(tag_path, unit=None):
    # Si está en caché, lo devolvemos inmediatamente
    if tag_path in tag_cache:
        return tag_cache[tag_path]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Buscar el Tag
    cur.execute("SELECT id FROM tag_definition WHERE path = %s", (tag_path,))
    result = cur.fetchone()
    
    if result:
        tag_id = result[0]
    else:
        # --- AUTO-PARSING DE JERARQUÍA ---
        # Formato esperado: planta/area/equipo/sensor
        parts = tag_path.split('/')
        area = parts[1] if len(parts) > 1 else 'General'
        equipment = parts[2] if len(parts) > 2 else 'General'
        sensor = parts[3] if len(parts) > 3 else parts[-1]
        
        print(f"🆕 Registrando Activo: [{area}] -> [{equipment}] -> Sensor: {sensor}")
        
        cur.execute(
            "INSERT INTO tag_definition (path, area, equipment, sensor_name, unit) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (tag_path, area, equipment, sensor, unit)
        )
        tag_id = cur.fetchone()[0]
        conn.commit()
    
    cur.close()
    conn.close()
    
    # Guardar en caché
    tag_cache[tag_path] = tag_id
    return tag_id

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic
        
        # 1. Obtener ID numérico del Tag (Usa caché interior)
        tag_id = get_tag_id(topic, payload.get("u"))
        
        # 2. Extraer datos
        val = payload.get("v")
        quality = payload.get("q", 192)
        ts = payload.get("t", datetime.now(timezone.utc).isoformat())
        
        # 3. Guardar en la DB usando el ID
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO historian (time, tag_id, value, quality) VALUES (%s, %s, %s, %s)",
                (ts, tag_id, val, quality)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            # --- NUECO: ACTUALIZAR EL TAG ENGINE (REDIS) ---
            # Guardamos el último valor y metadatos para acceso instantáneo
            redis_key = f"tag_current:{topic}"
            print(f"DEBUG: Saving key {redis_key} with ID {tag_id}")
            r.set(redis_key, json.dumps({
                "id": tag_id,
                "v": val,
                "q": quality,
                "t": ts,
                "u": payload.get("u")
            }))
            print(f"DEBUG: Saved to Redis: {r.get(redis_key)}")
            # También publicamos en un canal para WebSockets en tiempo real
            r.publish("live_updates", json.dumps({"topic": topic, "val": val, "ts": ts, "q": quality, "id": tag_id}))
            
            # --- ALARM ENGINE ---
            check_alarms(tag_id, val, ts)
            
            print(f"💾 [DB+Redis] {topic} = {val}")
            
    except Exception as e:
        print(f"⚠️ Error procesando mensaje: {e}")

def check_alarms(tag_id, value, ts):
    try:
        conn = get_db_connection()
        if not conn: return
        cur = conn.cursor()
        
        # 1. Obtener reglas para este tag (Usando el nuevo esquema de operador)
        cur.execute("SELECT id, operator, threshold, priority, message FROM alarm_definition WHERE tag_id = %s AND enabled = TRUE", (tag_id,))
        rules = cur.fetchall()
        
        for rule_id, op, threshold, priority, msg in rules:
            is_triggered = False
            # Evaluación dinámica
            if op == '>': is_triggered = (value > threshold)
            elif op == '<': is_triggered = (value < threshold)
            elif op == '>=': is_triggered = (value >= threshold)
            elif op == '<=': is_triggered = (value <= threshold)
            elif op == '==': is_triggered = (value == threshold)
            elif op == '!=': is_triggered = (value != threshold)
            
            # 2. Gestionar estado de alarma
            cur.execute("SELECT id, acknowledged, ack_time, max_value, start_time, active_operator, active_threshold FROM alarm_active WHERE definition_id = %s", (rule_id,))
            active_info = cur.fetchone()
            
            if is_triggered:
                if not active_info:
                    # Nueva Alarma: Se crea SIEMPRE que no haya una activa para esta regla
                    # Guardamos el operador y el umbral ACTIVOS en este preciso instante
                    cur.execute(
                        "INSERT INTO alarm_active (definition_id, start_time, current_value, max_value, active_operator, active_threshold) VALUES (%s, %s, %s, %s, %s, %s)",
                        (rule_id, ts, value, value, op, threshold)
                    )
                    r.publish("live_updates", json.dumps({
                        "type": "ALARM_OPEN", 
                        "tag_id": tag_id, 
                        "priority": priority,
                        "msg": msg
                    }))
                else:
                    # Alarma ya existente: Actualizamos el pico
                    active_id, is_ack, last_ack_time, old_max, start_t, active_op, active_thr = active_info
                    new_max = old_max
                    if op in ['>', '>=']: new_max = max(old_max, value) if old_max is not None else value
                    elif op in ['<', '<=']: new_max = min(old_max, value) if old_max is not None else value
                    else: new_max = value
                    
                    cur.execute("UPDATE alarm_active SET current_value = %s, max_value = %s WHERE id = %s", (value, new_max, active_id))
            
            elif active_info:
                # LA CONDICIÓN VOLVIÓ A LA NORMALIDAD: Cerramos el evento inmediatamente
                active_id, is_ack, last_ack_time, peak_value, start_time, active_op, active_thr = active_info
                
                # 1. Eliminar de activos
                cur.execute("DELETE FROM alarm_active WHERE id = %s", (active_id,))
                
                # 2. Mover a histórico preservando el estado de la regla QUE DISPARÓ la alarma
                cur.execute("""
                    INSERT INTO alarm_history (definition_id, start_time, end_time, max_value, priority, acknowledged, ack_time, current_value, event_operator, event_threshold) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (rule_id, start_time, ts, peak_value, priority, is_ack, last_ack_time, value, active_op, active_thr))
                
                # 3. Notificar cierre
                r.publish("live_updates", json.dumps({"type": "ALARM_CLOSE", "tag_id": tag_id}))

        conn.commit()
    except Exception as e:
        print(f"⚠️ Alarm Engine Error: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

def sync_tags_to_redis():
    """Carga todos los tags de la DB a Redis al arrancar para que el Front los vea."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, path, unit FROM tag_definition")
        tags = cur.fetchall()
        for t_id, t_path, t_unit in tags:
            redis_key = f"tag_current:{t_path}"
            # Solo creamos si no existe para no pisar valores reales
            if not r.exists(redis_key):
                r.set(redis_key, json.dumps({
                    "id": t_id,
                    "v": 0,
                    "q": 0, # Calidad mala inicial hasta que llegue MQTT
                    "t": datetime.now(timezone.utc).isoformat(),
                    "u": t_unit
                }))
            else:
                # Si existe, aseguramos que tenga el ID
                data = json.loads(r.get(redis_key))
                data["id"] = t_id
                r.set(redis_key, json.dumps(data))
        cur.close()
        conn.close()
        print(f"🔄 Sincronizados {len(tags)} tags de DB a Redis.")
    except Exception as e:
        print(f"⚠️ Error en Sincronización: {e}")

# Iniciar
setup_database()
sync_tags_to_redis()

client_id = f"SCADA_HISTORIAN_BRIDGE_{uuid.uuid4().hex[:4]}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.on_message = on_message

print(f"📡 Suscribiéndose a topics de planta...")
while True:
    try:
        print(f"📡 Intentando conectar al broker MQTT en {MQTT_BROKER}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        break
    except Exception as e:
        print(f"❌ Falló conexión al broker ({e}). Reintentando en 5s...")
        time.sleep(5)

client.subscribe("planta_central/#")
client.loop_forever()
