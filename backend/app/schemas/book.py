from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ..models.book import BookStatus


class BookCreate(BaseModel):
    title: str
    author: str
    genre: Optional[str] = None
    isbn: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    year_published: Optional[int] = None
    rating: Optional[float] = None
    tags: Optional[list[str]] = None
    status: BookStatus = BookStatus.none
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    isbn: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    year_published: Optional[int] = None
    rating: Optional[float] = None
    tags: Optional[list[str]] = None
    status: Optional[BookStatus] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class BookStatusUpdate(BaseModel):
    status: BookStatus


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    genre: Optional[str] = None
    isbn: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    year_published: Optional[int] = None
    rating: Optional[float] = None
    tags: Optional[list[str]] = None
    status: BookStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
