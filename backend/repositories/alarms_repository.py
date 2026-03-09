from core.config import get_db_connection


class AlarmRepository:

    def get_configs(self):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT ad.id, ad.tag_id, td.path, ad.operator,
                   ad.threshold, ad.priority, ad.enabled, ad.message
            FROM alarm_definition ad
            JOIN tag_definition td ON ad.tag_id = td.id
        """)
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows


    def insert_or_update_config(self, config):
        conn = get_db_connection()
        cur = conn.cursor()

        if config.id:
            cur.execute("""
                UPDATE alarm_definition
                SET tag_id=%s, operator=%s, threshold=%s,
                    priority=%s, enabled=%s, message=%s
                WHERE id=%s
                RETURNING id
            """, (...))
        else:
            cur.execute("""
                INSERT INTO alarm_definition (...)
                VALUES (...)
                RETURNING id
            """, (...))

        alarm_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()
        return alarm_id


    def delete_config(self, config_id: int):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM alarm_definition WHERE id=%s", (config_id,))
        conn.commit()
        cur.close()
        conn.close()