import json
from fastapi import APIRouter, HTTPException

from config import r, get_db_connection
from models import AlarmConfig

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.get("/config")
async def get_alarm_configs():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ad.id, ad.tag_id, td.path, ad.operator, ad.threshold, ad.priority, ad.enabled, ad.message
        FROM alarm_definition ad
        JOIN tag_definition td ON ad.tag_id = td.id
        """
    )
    rows = cur.fetchall()
    configs = [
        {
            "id": r[0], "tag_id": r[1], "tag_path": r[2],
            "operator": r[3], "threshold": r[4],
            "priority": r[5], "enabled": r[6], "message": r[7],
        }
        for r in rows
    ]
    cur.close()
    conn.close()
    return configs


@router.post("/config")
async def create_alarm_config(config: AlarmConfig):
    print(f"📡 Recibida petición POST /alarms/config: {config}")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if config.id:
            print(f"📝 Actualizando alarma con ID: {config.id}")
            cur.execute(
                """
                UPDATE alarm_definition
                SET tag_id = %s, operator = %s, threshold = %s,
                    priority = %s, enabled = %s, message = %s
                WHERE id = %s
                RETURNING id
                """,
                (config.tag_id, config.operator, config.threshold,
                 config.priority, config.enabled, config.message, config.id),
            )
            row = cur.fetchone()
            if not row:
                print(f"⚠️ Alarma no encontrada para actualizar: {config.id}")
                raise HTTPException(status_code=404, detail="Alarm not found")
            alarm_id = row[0]
        else:
            print(f"🆕 Creando nueva alarma para tag_id: {config.tag_id}")
            cur.execute(
                """
                INSERT INTO alarm_definition (tag_id, operator, threshold, priority, enabled, message)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tag_id, operator, threshold)
                DO UPDATE SET priority = EXCLUDED.priority, enabled = EXCLUDED.enabled, message = EXCLUDED.message
                RETURNING id
                """,
                (config.tag_id, config.operator, config.threshold,
                 config.priority, config.enabled, config.message),
            )
            alarm_id = cur.fetchone()[0]

        conn.commit()
        print(f"✅ Alarma guardada con éxito. ID: {alarm_id}")
        return {"id": alarm_id, "status": "saved"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en POST /alarms/config: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()


@router.delete("/config/{config_id}")
async def delete_alarm_config(config_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM alarm_definition WHERE id = %s", (config_id,))
        conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()


@router.get("/active")
async def get_active_alarms():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
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
        """
    )
    rows = cur.fetchall()
    active = [
        {
            "id": r[0], "path": r[1], "operator": r[2], "threshold": r[3],
            "priority": r[4], "since": r[5].isoformat(), "val": r[6],
            "ack": r[7], "source": r[8], "raw_id": r[9],
        }
        for r in rows
    ]
    cur.close()
    conn.close()
    return active


@router.post("/acknowledge/{alarm_id}")
async def acknowledge_alarm(alarm_id: int, source: str = "ACTIVE"):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        table = "alarm_active" if source == "ACTIVE" else "alarm_history"
        cur.execute(
            f"UPDATE {table} SET acknowledged = TRUE, ack_time = NOW() WHERE id = %s RETURNING id",
            (alarm_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Evento de alarma no encontrado")

        conn.commit()
        r.publish("live_updates", json.dumps({"type": "ALARM_ACK", "alarm_id": alarm_id}))
        return {"status": "acknowledged"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/history")
async def get_alarm_history(limit: int = 100):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ah.id, td.path, ah.event_operator, ah.event_threshold,
               ah.priority, ah.start_time, ah.end_time, ah.max_value, ah.acknowledged
        FROM alarm_history ah
        JOIN alarm_definition ad ON ah.definition_id = ad.id
        JOIN tag_definition td ON ad.tag_id = td.id
        ORDER BY ah.start_time DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    history = [
        {
            "id": r[0], "path": r[1], "operator": r[2], "threshold": r[3],
            "priority": r[4], "start": r[5].isoformat(),
            "end": r[6].isoformat() if r[6] else None,
            "max_val": r[7], "ack": r[8],
        }
        for r in rows
    ]
    cur.close()
    conn.close()
    return history


@router.post("/history/acknowledge-all")
async def acknowledge_all_history():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE alarm_history SET acknowledged = TRUE, ack_time = NOW() WHERE acknowledged = FALSE"
        )
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
