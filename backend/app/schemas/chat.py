from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str


class Source(BaseModel):
    book: str
    author: str
    type: str
    content: str
    chapter: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
