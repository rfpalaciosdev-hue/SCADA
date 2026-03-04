import json
from fastapi import APIRouter

from config import r

router = APIRouter(tags=["tags"])


@router.get("/tags")
async def get_all_tags():
    """
    Obtiene el valor actual de TODOS los tags desde Redis (el Tag Engine).
    Mucho más rápido que consultar la DB de históricos.
    """
    keys = r.keys("tag_current:*")
    tags = {}
    for key in keys:
        tag_path = key.replace("tag_current:", "")
        tags[tag_path] = json.loads(r.get(key))
    return tags
