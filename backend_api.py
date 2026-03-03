from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
import redis
import json
import asyncio
import psycopg2
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
from chatbot_service import process_chat
from scada_nlp import resolve_tag, detect_stat, is_conceptual_question
import time
from fastapi.responses import HTMLResponse

app = FastAPI(title="SCADA Real-Time API")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción poner la URL del front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models para Admin Panel
class AlarmConfig(BaseModel):
    id: Optional[int] = None
    tag_id: int
    operator: str  # '>', '<', etc
    threshold: float
    priority: str
    enabled: bool = True
    message: str

class SensorMetadata(BaseModel):
    tag: str
    description: Optional[str] = None
    process_role: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    critical_range_min: Optional[float] = None
    critical_range_max: Optional[float] = None
    physical_location: Optional[str] = None
    related_system: Optional[str] = None
    failure_impact: Optional[str] = None
    operating_notes: Optional[str] = None

# Configuración de Redis
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": 0,
    "decode_responses": True
}

r = redis.Redis(**REDIS_CONFIG)

# Configuración de TimescaleDB
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "scada_user"),
    "password": os.getenv("DB_PASS", "scada_admin"),
    "dbname": os.getenv("DB_NAME", "scada_db")
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = []

@app.on_event("startup")
async def startup_event():
    """
    Crea la tabla sensor_metadata si no existe al iniciar.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
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
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Base de datos verificada: tabla sensor_metadata lista.")
    except Exception as e:
        print(f"❌ Error creando tabla sensor_metadata: {e}")

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        answer = process_chat(request.message, request.history)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sensor/context")
async def get_sensor_context(tag: str):
    """
    Devuelve el contexto completo de un sensor: estructural, metadata, valor actual, stats y alarmas.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Información estructural y metadata
        cur.execute("""
            SELECT td.id, td.path, sm.description, sm.process_role, 
                   sm.normal_range_min, sm.normal_range_max, 
                   sm.critical_range_min, sm.critical_range_max,
                   sm.physical_location, sm.related_system, sm.operating_notes,
                   sm.failure_impact
            FROM tag_definition td
            LEFT JOIN sensor_metadata sm ON td.id = sm.tag_id
            WHERE td.path = %s
        """, (tag,))
        row = cur.fetchone()
        
        if not row:
            cur.close()
            conn.close()
            return {"error": "Tag not found in definition"}
            
        context = {
            "id": row[0],
            "path": row[1],
            "metadata": {
                "description": row[2],
                "process_role": row[3],
                "normal_range": [row[4], row[5]],
                "critical_range": [row[6], row[7]],
                "location": row[8],
                "system": row[9],
                "notes": row[10],
                "failure_impact": row[11]
            }
        }
        
        # 2. Valor actual (Redis)
        current_data = r.get(f"tag_current:{tag}")
        if current_data:
            context["current"] = json.loads(current_data)
        else:
            context["current"] = {"v": 0, "q": 0, "t": datetime.now().isoformat()}

        # 3. Stats 24h (Timescale)
        cur.execute("""
            SELECT MIN(value), MAX(value), AVG(value)
            FROM historian 
            WHERE tag_id = %s AND time >= NOW() - INTERVAL '24 hours'
        """, (row[0],))
        stats_row = cur.fetchone()
        context["stats_24h"] = {
            "min": stats_row[0] if stats_row[0] is not None else 0,
            "max": stats_row[1] if stats_row[1] is not None else 0,
            "avg": float(stats_row[2]) if stats_row[2] is not None else 0
        }

        # 4. Alarmas activas
        cur.execute("""
            SELECT aa.id, aa.active_threshold, ad.priority, aa.start_time, aa.max_value
            FROM alarm_active aa
            JOIN alarm_definition ad ON aa.definition_id = ad.id
            WHERE ad.tag_id = %s
        """, (row[0],))
        alarms = cur.fetchall()
        context["active_alarms"] = [
            {"id": a[0], "threshold": a[1], "priority": a[2], "since": a[3].isoformat(), "max_val": a[4]}
            for a in alarms
        ]

        cur.close()
        conn.close()
        return context
    except Exception as e:
        return {"error": str(e)}

@app.post("/sensor/metadata")
async def update_sensor_metadata(metadata: SensorMetadata):
    """
    Actualiza la metadata de un sensor en la base de datos.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Obtener el ID del tag
        cur.execute("SELECT id FROM tag_definition WHERE path = %s", (metadata.tag,))
        tag_res = cur.fetchone()
        if not tag_res:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        tag_id = tag_res[0]
        
        cur.execute('''
            INSERT INTO sensor_metadata (
                tag_id, description, process_role, 
                normal_range_min, normal_range_max, 
                critical_range_min, critical_range_max, 
                physical_location, related_system, 
                failure_impact, operating_notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tag_id) DO UPDATE SET
                description = EXCLUDED.description,
                process_role = EXCLUDED.process_role,
                normal_range_min = EXCLUDED.normal_range_min,
                normal_range_max = EXCLUDED.normal_range_max,
                critical_range_min = EXCLUDED.critical_range_min,
                critical_range_max = EXCLUDED.critical_range_max,
                physical_location = EXCLUDED.physical_location,
                related_system = EXCLUDED.related_system,
                failure_impact = EXCLUDED.failure_impact,
                operating_notes = EXCLUDED.operating_notes,
                updated_at = NOW()
        ''', (
            tag_id, metadata.description, metadata.process_role,
            metadata.normal_range_min, metadata.normal_range_max,
            metadata.critical_range_min, metadata.critical_range_max,
            metadata.physical_location, metadata.related_system,
            metadata.failure_impact, metadata.operating_notes
        ))
        
        conn.commit()
        return {"status": "success", "tag": metadata.tag}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

class AIAskRequest(BaseModel):
    tag: Optional[str] = None
    question: str

@app.post("/ai/ask")
async def ai_ask(request: AIAskRequest):
    start_time = time.time()
    resolved_tag = request.tag
    
    # Si no hay tag, intentar resolverlo de la pregunta
    if not resolved_tag:
        resolved_tag = resolve_tag(request.question)
    
    context_data = None
    if resolved_tag:
        context_data = await get_sensor_context(resolved_tag)
    
    # Constructor de prompt industrial
    prompt = "You are an industrial SCADA assistant.\nRules:\n- Use only provided data.\n- Do not invent technical details.\n- If information is missing, say 'Data not available'.\n- Keep answers concise and operational.\n\n"
    
    if context_data and "error" not in context_data:
        path_parts = context_data["path"].split('/')
        prompt += f"Sensor Path: {context_data['path']}\n"
        prompt += f"Area: {path_parts[1] if len(path_parts) > 1 else 'N/A'}\n"
        prompt += f"Equipment: {path_parts[2] if len(path_parts) > 2 else 'N/A'}\n"
        prompt += f"Sensor: {path_parts[-1]}\n"
        prompt += f"Unit: {context_data['current'].get('u', 'N/A')}\n"
        prompt += f"Description: {context_data['metadata']['description'] or 'N/A'}\n"
        prompt += f"Process Role: {context_data['metadata']['process_role'] or 'N/A'}\n"
        prompt += f"Physical Location: {context_data['metadata']['location'] or 'N/A'}\n"
        prompt += f"Related System: {context_data['metadata']['system'] or 'N/A'}\n"
        prompt += f"Failure Impact: {context_data['metadata']['failure_impact'] or 'N/A'}\n"
        prompt += f"Operational Ranges:\n"
        prompt += f"Normal Range: {context_data['metadata']['normal_range'][0]} - {context_data['metadata']['normal_range'][1]}\n"
        prompt += f"Critical Range: {context_data['metadata']['critical_range'][0]} - {context_data['metadata']['critical_range'][1]}\n"
        prompt += f"Current Status:\n"
        prompt += f"Current Value: {context_data['current'].get('v', 0)}\n"
        prompt += f"Alarm Active: {'YES' if context_data['active_alarms'] else 'NO'}\n"
        prompt += f"24h Min: {context_data['stats_24h']['min']}\n"
        prompt += f"24h Max: {context_data['stats_24h']['max']}\n"
        prompt += f"24h Avg: {context_data['stats_24h']['avg']}\n"
        prompt += f"Operating Notes: {context_data['metadata']['notes'] or 'N/A'}\n\n"
    else:
        prompt += "CONTEXT NOT FOUND OR TAG NOT RESOLVED.\n\n"
    
    prompt += f"User Question: {request.question}\n"
    
    # Llamada a la IA (reutilizando ChatBot logic o directo)
    try:
        # Reutilizamos process_chat pero con el prompt inyectado como contexto de sistema
        # Para simplificar, pasamos el prompt completo como mensaje si el modelo lo permite
        # o lo usamos como 'system' mensaje si el backend de chatbot lo soporta.
        response = process_chat(f"{prompt}\nAI Response:", [])
    except Exception as e:
        response = f"Error processing AI: {str(e)}"
    
    duration = time.time() - start_time
    
    # Logging
    print(f"--- AI INTERACTION ---")
    print(f"Question: {request.question}")
    print(f"Resolved Tag: {resolved_tag}")
    print(f"Prompt Generated: \n{prompt}")
    print(f"Response: {response}")
    print(f"Duration: {duration:.2f}s")
    print(f"-----------------------")
    
    return {
        "tag": resolved_tag,
        "prompt": prompt,
        "answer": response,
        "duration": duration
    }

@app.get("/ai-panel", response_class=HTMLResponse)
async def ai_panel_page():
    with open("ai_panel.html", "r") as f:
        return f.read()

@app.get("/history/{tag_path:path}/stats")
async def get_tag_stats(tag_path: str, hours: float = 1.0, start: Optional[str] = None, end: Optional[str] = None):
    """
    Calcula estadísticas analíticas (Min, Max, Avg, StdDev, Median, etc.) en el backend.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM tag_definition WHERE path = %s", (tag_path,))
        tag_result = cur.fetchone()
        
        if not tag_result:
            return {"error": "Tag not found"}
        
        tag_id = tag_result[0]
        
        if start and end:
            where_clause = "WHERE tag_id = %s AND time BETWEEN %s AND %s"
            params = (tag_id, start, end)
        elif start:
            where_clause = "WHERE tag_id = %s AND time >= %s"
            params = (tag_id, start)
        else:
            where_clause = "WHERE tag_id = %s AND time >= NOW() - %s * INTERVAL '1 hour'"
            params = (tag_id, hours)

        query = f"""
            SELECT 
                MIN(value) as min_v, 
                MAX(value) as max_v, 
                AVG(value) as avg_v, 
                COUNT(value) as count_v,
                STDDEV(value) as stddev_v,
                VARIANCE(value) as var_v,
                SUM(value) as sum_v,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY value) as median_v
            FROM historian 
            {where_clause}
        """
        
        cur.execute(query, params)
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "path": tag_path,
            "stats": {
                "min": row[0] if row[0] is not None else 0,
                "max": row[1] if row[1] is not None else 0,
                "avg": float(row[2]) if row[2] is not None else 0,
                "count": int(row[3]) if row[3] is not None else 0,
                "stddev": float(row[4]) if row[4] is not None else 0,
                "variance": float(row[5]) if row[5] is not None else 0,
                "sum": float(row[6]) if row[6] is not None else 0,
                "median": float(row[7]) if row[7] is not None else 0,
                "range": (row[1] - row[0]) if (row[0] is not None and row[1] is not None) else 0
            }
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/history/{tag_path:path}")
async def get_tag_history(tag_path: str, hours: float = 1.0, start: Optional[str] = None, end: Optional[str] = None):
    """
    Obtiene el historial de un tag específico desde TimescaleDB.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM tag_definition WHERE path = %s", (tag_path,))
        tag_result = cur.fetchone()
        
        if not tag_result:
            return {"error": "Tag not found"}
        
        tag_id = tag_result[0]
        
        if start and end:
            query = "SELECT time, value, quality FROM historian WHERE tag_id = %s AND time BETWEEN %s AND %s ORDER BY time ASC"
            params = (tag_id, start, end)
        elif start:
            query = "SELECT time, value, quality FROM historian WHERE tag_id = %s AND time >= %s ORDER BY time ASC"
            params = (tag_id, start)
        else:
            query = "SELECT time, value, quality FROM historian WHERE tag_id = %s AND time >= NOW() - %s * INTERVAL '1 hour' ORDER BY time ASC"
            params = (tag_id, hours)

        cur.execute(query, params)
        
        rows = cur.fetchall()
        history = [
            {"t": row[0].isoformat(), "v": row[1], "q": row[2]} 
            for row in rows
        ]
        
        cur.close()
        conn.close()
        return {"path": tag_path, "data": history}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/alarms/config")
async def get_alarm_configs():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ad.id, ad.tag_id, td.path, ad.operator, ad.threshold, ad.priority, ad.enabled, ad.message 
        FROM alarm_definition ad
        JOIN tag_definition td ON ad.tag_id = td.id
    """)
    rows = cur.fetchall()
    configs = [
        {"id": r[0], "tag_id": r[1], "tag_path": r[2], "operator": r[3], "threshold": r[4], "priority": r[5], "enabled": r[6], "message": r[7]}
        for r in rows
    ]
    cur.close()
    conn.close()
    return configs

@app.post("/alarms/config")
async def create_alarm_config(config: AlarmConfig):
    print(f"📡 Recibida petición POST /alarms/config: {config}")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if config.id:
            print(f"📝 Actualizando alarma con ID: {config.id}")
            cur.execute("""
                UPDATE alarm_definition 
                SET tag_id = %s, operator = %s, threshold = %s, priority = %s, enabled = %s, message = %s
                WHERE id = %s
                RETURNING id
            """, (config.tag_id, config.operator, config.threshold, config.priority, config.enabled, config.message, config.id))
            row = cur.fetchone()
            if not row:
                print(f"⚠️ Alarma no encontrada para actualizar: {config.id}")
                raise HTTPException(status_code=404, detail="Alarm not found")
            id = row[0]
        else:
            print(f"🆕 Creando nueva alarma para tag_id: {config.tag_id}")
            cur.execute("""
                INSERT INTO alarm_definition (tag_id, operator, threshold, priority, enabled, message)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tag_id, operator, threshold) 
                DO UPDATE SET priority = EXCLUDED.priority, enabled = EXCLUDED.enabled, message = EXCLUDED.message
                RETURNING id
            """, (config.tag_id, config.operator, config.threshold, config.priority, config.enabled, config.message))
            id = cur.fetchone()[0]
            
        conn.commit()
        print(f"✅ Alarma guardada con éxito. ID: {id}")
        return {"id": id, "status": "saved"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en POST /alarms/config: {e}")
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.delete("/alarms/config/{config_id}")
async def delete_alarm_config(config_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM alarm_definition WHERE id = %s", (config_id,))
        conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/alarms/active")
async def get_active_alarms():
    conn = get_db_connection()
    cur = conn.cursor()
    # Unión de Alarmas en tiempo real + Alarmas pasadas pero no reconocidas
    # Prefixamos los IDs para evitar colisiones en el Front y saber exactamente qué tabla actualizar
    cur.execute("""
        SELECT 
            'act_' || aa.id as global_id, 
            td.path, 
            COALESCE(aa.active_operator, ad.operator) as op, 
            COALESCE(aa.active_threshold, ad.threshold) as thr, 
            ad.priority, 
            aa.start_time, 
            aa.max_value, 
            aa.acknowledged, 
            'ACTIVE' as source,
            aa.id as raw_id
        FROM alarm_active aa
        JOIN alarm_definition ad ON aa.definition_id = ad.id
        JOIN tag_definition td ON ad.tag_id = td.id
        UNION ALL
        SELECT 
            'his_' || ah.id as global_id, 
            td.path, 
            COALESCE(ah.event_operator, ad.operator) as op, 
            COALESCE(ah.event_threshold, ad.threshold) as thr, 
            ah.priority, 
            ah.start_time, 
            ah.max_value, 
            ah.acknowledged, 
            'HISTORY' as source,
            ah.id as raw_id
        FROM alarm_history ah
        JOIN alarm_definition ad ON ah.definition_id = ad.id
        JOIN tag_definition td ON ad.tag_id = td.id
        WHERE ah.acknowledged = FALSE
        ORDER BY priority DESC, start_time DESC
    """)
    rows = cur.fetchall()
    active = [
        {
            "id": r[0], "path": r[1], "operator": r[2], "threshold": r[3], 
            "priority": r[4], "since": r[5].isoformat(), "val": r[6], 
            "ack": r[7], "source": r[8], "raw_id": r[9]
        }
        for r in rows
    ]
    cur.close()
    conn.close()
    return active

@app.post("/alarms/acknowledge/{alarm_id}")
async def acknowledge_alarm(alarm_id: int, source: str = 'ACTIVE'):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        table = "alarm_active" if source == 'ACTIVE' else "alarm_history"
        cur.execute(f"UPDATE {table} SET acknowledged = TRUE, ack_time = NOW() WHERE id = %s RETURNING id", (alarm_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Evendo de alarma no encontrado")
        
        conn.commit()
        r.publish("live_updates", json.dumps({"type": "ALARM_ACK", "alarm_id": alarm_id}))
        return {"status": "acknowledged"}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/alarms/history")
async def get_alarm_history(limit: int = 100):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ah.id, td.path, ah.event_operator, ah.event_threshold, ah.priority, ah.start_time, ah.end_time, ah.max_value, ah.acknowledged
        FROM alarm_history ah
        JOIN alarm_definition ad ON ah.definition_id = ad.id
        JOIN tag_definition td ON ad.tag_id = td.id
        ORDER BY ah.start_time DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    history = [
        {
            "id": r[0], "path": r[1], "operator": r[2], "threshold": r[3], 
            "priority": r[4], "start": r[5].isoformat(), 
            "end": r[6].isoformat() if r[6] else None, 
            "max_val": r[7], "ack": r[8]
        }
        for r in rows
    ]
    cur.close()
    conn.close()
    return history

@app.post("/alarms/history/acknowledge-all")
async def acknowledge_all_history():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE alarm_history SET acknowledged = TRUE, ack_time = NOW() WHERE acknowledged = FALSE")
        count = cur.rowcount
        conn.commit()
        r.publish("live_updates", json.dumps({"type": "ALARM_ACK_ALL"}))
        return {"status": "success", "count": count}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/")
async def root():
    return {"message": "SCADA Backend is running"}

@app.get("/tags")
async def get_all_tags():
    """
    Obtiene el valor actual de TODOS los tags desde Redis (el Tag Engine).
    Esto es mucho más rápido que pegarle a la DB de históricos.
    """
    keys = r.keys("tag_current:*")
    tags = {}
    for key in keys:
        tag_path = key.replace("tag_current:", "")
        tags[tag_path] = json.loads(r.get(key))
    return tags

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Cliente conectado al WebSocket")
    pubsub = r.pubsub()
    pubsub.subscribe("live_updates")
    try:
        while True:
            # get_message es no bloqueante por defecto si no pasas timeout
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message['data'])
            await asyncio.sleep(0.1) # Pequeña espera para no saturar la CPU
    except Exception as e:
        print(f"❌ WS Dissconnected/Error: {e}")
    finally:
        pubsub.unsubscribe("live_updates")
        pubsub.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
