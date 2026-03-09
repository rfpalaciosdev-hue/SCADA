import json
from datetime import datetime

from core.config import r
from repositories.sensors_repository import SensorsRepository


class SensorsService:

    def __init__(self):
        self.repo = SensorsRepository()


    async def get_sensor_context(self, tag: str):
        row = self.repo.get_tag_definition_with_metadata(tag)

        if not row:
            raise ValueError("Tag not found in definition")

        tag_id = row[0]

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

        # Redis (valor actual)
        current_data = r.get(f"tag_current:{tag}")
        context["current"] = (
            json.loads(current_data)
            if current_data
            else {"v": 0, "q": 0, "t": datetime.now().isoformat()}
        )

        # Stats 24h
        stats_row = self.repo.get_24h_stats(tag_id)
        context["stats_24h"] = {
            "min": stats_row[0] if stats_row[0] is not None else 0,
            "max": stats_row[1] if stats_row[1] is not None else 0,
            "avg": float(stats_row[2]) if stats_row[2] is not None else 0,
        }

        # Alarmas activas
        alarms = self.repo.get_active_alarms(tag_id)
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

        return context


    def update_metadata(self, metadata):
        row = self.repo.get_tag_definition_with_metadata(metadata.tag)

        if not row:
            raise ValueError("Tag not found")

        tag_id = row[0]
        self.repo.upsert_metadata(tag_id, metadata)