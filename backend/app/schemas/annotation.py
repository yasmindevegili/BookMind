from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnnotationCreate(BaseModel):
    book_id: int
    type: str  # highlight, note, quote, reflection
    content: str
    page: Optional[int] = None
    chapter: Optional[str] = None


class AnnotationResponse(BaseModel):
    id: int
    book_id: int
    type: str
    content: str
    page: Optional[int] = None
    chapter: Optional[str] = None
    embedded_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
