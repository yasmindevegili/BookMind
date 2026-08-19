from datetime import datetime
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
