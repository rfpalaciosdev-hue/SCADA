from fastapi import APIRouter, HTTPException
from services.alarms_service import AlarmService
from models import AlarmConfig

router = APIRouter(prefix="/alarms", tags=["alarms"])
service = AlarmService()


@router.get("/config")
async def get_alarm_configs():
    return service.get_configs()


@router.post("/config")
async def create_alarm_config(config: AlarmConfig):
    try:
        alarm_id = service.save_config(config)
        return {"id": alarm_id, "status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))