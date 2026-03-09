import json
from core.config import r
from repositories.alarms_repository import AlarmRepository


class AlarmService:

    def __init__(self):
        self.repo = AlarmRepository()


    def get_configs(self):
        rows = self.repo.get_configs()

        return [
            {
                "id": r[0],
                "tag_id": r[1],
                "tag_path": r[2],
                "operator": r[3],
                "threshold": r[4],
                "priority": r[5],
                "enabled": r[6],
                "message": r[7],
            }
            for r in rows
        ]


    def save_config(self, config):
        alarm_id = self.repo.insert_or_update_config(config)

        # lógica de dominio
        r.publish("live_updates",
                  json.dumps({"type": "ALARM_CONFIG_CHANGED"}))

        return alarm_id


    def acknowledge_alarm(self, alarm_id: int, source: str):
        table = "alarm_active" if source == "ACTIVE" else "alarm_history"

        updated = self.repo.acknowledge_alarm(alarm_id, table)

        if not updated:
            raise ValueError("Alarm not found")

        r.publish("live_updates",
                  json.dumps({"type": "ALARM_ACK", "alarm_id": alarm_id}))