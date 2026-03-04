import json
from datetime import datetime
from fastapi import APIRouter, HTTPException

from config import r, get_db_connection
from models import SensorMetadata

router = APIRouter(prefix="/sensor", tags=["sensors"])


async def get_sensor_context(tag: str):
    """
    Función reutilizable que devuelve el contexto completo de un sensor.
    Es usada tanto por el endpoint GET /sensor/context como por /ai/ask.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Información estructural y metadata
        cur.execute(
            """
            SELECT td.id, td.path, sm.description, sm.process_role,
                   sm.normal_range_min, sm.normal_range_max,
                   sm.critical_range_min, sm.critical_range_max,
                   sm.physical_location, sm.related_system, sm.operating_notes,
                   sm.failure_impact
            FROM tag_definition td
            LEFT JOIN sensor_metadata sm ON td.id = sm.tag_id
            WHERE td.path = %s
            """,
            (tag,),
        )
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
                "failure_impact": row[11],
            },
        }

        # 2. Valor actual (Redis)
        current_data = r.get(f"tag_current:{tag}")
        context["current"] = (
            json.loads(current_data)
            if current_data
            else {"v": 0, "q": 0, "t": datetime.now().isoformat()}
        )

        # 3. Stats 24h (Timescale)
        cur.execute(
            """
            SELECT MIN(value), MAX(value), AVG(value)
            FROM historian
            WHERE tag_id = %s AND time >= NOW() - INTERVAL '24 hours'
            """,
            (row[0],),
        )
        stats_row = cur.fetchone()
        context["stats_24h"] = {
            "min": stats_row[0] if stats_row[0] is not None else 0,
            "max": stats_row[1] if stats_row[1] is not None else 0,
            "avg": float(stats_row[2]) if stats_row[2] is not None else 0,
        }

        # 4. Alarmas activas
        cur.execute(
            """
            SELECT aa.id, aa.active_threshold, ad.priority, aa.start_time, aa.max_value
            FROM alarm_active aa
            JOIN alarm_definition ad ON aa.definition_id = ad.id
            WHERE ad.tag_id = %s
            """,
            (row[0],),
        )
        alarms = cur.fetchall()
        context["active_alarms"] = [
            {
                "id": a[0],
                "threshold": a[1],
                "priority": a[2],
                "since": a[3].isoformat(),
                "max_val": a[4],
            }
            for a in alarms
        ]

        cur.close()
        conn.close()
        return context

    except Exception as e:
        return {"error": str(e)}


@router.get("/context")
async def sensor_context_endpoint(tag: str):
    """
    Devuelve el contexto completo de un sensor: metadata, valor actual, stats y alarmas.
    """
    return await get_sensor_context(tag)


@router.post("/metadata")
async def update_sensor_metadata(metadata: SensorMetadata):
    """
    Actualiza la metadata de un sensor en la base de datos.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM tag_definition WHERE path = %s", (metadata.tag,))
        tag_res = cur.fetchone()
        if not tag_res:
            raise HTTPException(status_code=404, detail="Tag not found")

        tag_id = tag_res[0]

        cur.execute(
            """
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
            """,
            (
                tag_id,
                metadata.description,
                metadata.process_role,
                metadata.normal_range_min,
                metadata.normal_range_max,
                metadata.critical_range_min,
                metadata.critical_range_max,
                metadata.physical_location,
                metadata.related_system,
                metadata.failure_impact,
                metadata.operating_notes,
            ),
        )

        conn.commit()
        return {"status": "success", "tag": metadata.tag}

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()
