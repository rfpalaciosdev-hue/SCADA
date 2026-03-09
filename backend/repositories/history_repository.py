from core.config import get_db_connection


class HistoryRepository:

    def get_tag_id_by_path(self, tag_path: str):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM tag_definition WHERE path = %s", (tag_path,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        return result[0] if result else None


    def get_history(self, tag_id, start=None, end=None, hours=1.0):
        conn = get_db_connection()
        cur = conn.cursor()

        if start and end:
            query = """
                SELECT time, value, quality
                FROM historian
                WHERE tag_id = %s AND time BETWEEN %s AND %s
                ORDER BY time ASC
            """
            params = (tag_id, start, end)

        elif start:
            query = """
                SELECT time, value, quality
                FROM historian
                WHERE tag_id = %s AND time >= %s
                ORDER BY time ASC
            """
            params = (tag_id, start)

        else:
            query = """
                SELECT time, value, quality
                FROM historian
                WHERE tag_id = %s
                AND time >= NOW() - %s * INTERVAL '1 hour'
                ORDER BY time ASC
            """
            params = (tag_id, hours)

        cur.execute(query, params)
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return rows