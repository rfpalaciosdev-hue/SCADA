from fastapi import APIRouter, HTTPException
from models import SensorMetadata
from services.sensors_service import SensorsService

router = APIRouter(prefix="/sensor", tags=["sensors"])
service = SensorsService()


@router.get("/context")
async def sensor_context_endpoint(tag: str):
    try:
        return await service.get_sensor_context(tag)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metadata")
async def update_sensor_metadata(metadata: SensorMetadata):
    try:
        service.update_metadata(metadata)
        return {"status": "success", "tag": metadata.tag}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))