from core.config import get_db_connection


class SensorsRepository:

    def get_tag_definition_with_metadata(self, tag: str):
        conn = get_db_connection()
        cur = conn.cursor()

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

        cur.close()
        conn.close()
        return row


    def get_24h_stats(self, tag_id: int):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT MIN(value), MAX(value), AVG(value)
            FROM historian
            WHERE tag_id = %s AND time >= NOW() - INTERVAL '24 hours'
            """,
            (tag_id,),
        )
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row


    def get_active_alarms(self, tag_id: int):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT aa.id, aa.active_threshold, ad.priority,
                   aa.start_time, aa.max_value
            FROM alarm_active aa
            JOIN alarm_definition ad ON aa.definition_id = ad.id
            WHERE ad.tag_id = %s
            """,
            (tag_id,),
        )

        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows


    def upsert_metadata(self, tag_id: int, metadata):
        conn = get_db_connection()
        cur = conn.cursor()

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
        cur.close()
        conn.close()