from fastapi import APIRouter
from services.tags_service import TagsService

router = APIRouter(tags=["tags"])


@router.get("/tags")
async def get_all_tags():
    """
    Obtiene el valor actual de TODOS los tags desde Redis (Tag Engine).
    Mucho más rápido que consultar históricos en DB.
    """
    return await TagsService.get_all_tags()