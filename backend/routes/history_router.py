from fastapi import APIRouter, HTTPException
from services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])
service = HistoryService()


@router.get("/{tag_path:path}")
async def get_tag_history(tag_path: str, hours: float = 1.0):
    try:
        data = service.get_tag_history(tag_path, hours=hours)
        return {"path": tag_path, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))