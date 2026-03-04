from typing import Optional
from fastapi import APIRouter

from config import get_db_connection

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{tag_path:path}/stats")
async def get_tag_stats(
    tag_path: str,
    hours: float = 1.0,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
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
                MIN(value)    as min_v,
                MAX(value)    as max_v,
                AVG(value)    as avg_v,
                COUNT(value)  as count_v,
                STDDEV(value) as stddev_v,
                VARIANCE(value) as var_v,
                SUM(value)    as sum_v,
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
                "min":      row[0] if row[0] is not None else 0,
                "max":      row[1] if row[1] is not None else 0,
                "avg":      float(row[2]) if row[2] is not None else 0,
                "count":    int(row[3])   if row[3] is not None else 0,
                "stddev":   float(row[4]) if row[4] is not None else 0,
                "variance": float(row[5]) if row[5] is not None else 0,
                "sum":      float(row[6]) if row[6] is not None else 0,
                "median":   float(row[7]) if row[7] is not None else 0,
                "range": (row[1] - row[0])
                    if (row[0] is not None and row[1] is not None)
                    else 0,
            },
        }

    except Exception as e:
        return {"error": str(e)}


@router.get("/{tag_path:path}")
async def get_tag_history(
    tag_path: str,
    hours: float = 1.0,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
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
