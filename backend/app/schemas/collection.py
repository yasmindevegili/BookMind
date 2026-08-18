from typing import Optional

from pydantic import BaseModel


class CollectionSummary(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    type: str
    book_count: int

    model_config = {"from_attributes": True}


class ExternalBook(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    source: str  # "nyt" ou "google_books"
