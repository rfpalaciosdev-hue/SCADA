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

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        answer = process_chat(request.message, request.history)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
