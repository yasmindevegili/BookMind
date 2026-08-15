from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    # type: "highlight" | "note" | "quote" | "reflection"
    type: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    page: Mapped[Optional[int]] = mapped_column(Integer)
    chapter: Mapped[Optional[str]] = mapped_column(String(200))
    # 384 dimensions = paraphrase-multilingual-MiniLM-L12-v2 (fastembed, local, sem API)
    # Modelo multilingual: funciona bem em português e inglês
    # This vector is what makes RAG possible: similar texts → similar vectors → findable by cosine distance
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(384))
    embedded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    book: Mapped["Book"] = relationship(back_populates="annotations")
