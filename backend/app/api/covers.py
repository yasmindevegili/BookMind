from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..services.babel import babel_client

router = APIRouter()


@router.get("/babel/{babel_id}")
async def babel_cover(babel_id: int):
    """Proxy autenticado para capas do Calibre-Web (Babel)."""
    content = await babel_client.get_cover(babel_id)
    if not content:
        raise HTTPException(status_code=404, detail="Capa não encontrada no Babel")
    return Response(content=content, media_type="image/jpeg")
