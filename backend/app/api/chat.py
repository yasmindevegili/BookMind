from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.rag import rag_service

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await rag_service.chat(request.query, db)
    return ChatResponse(**result)
