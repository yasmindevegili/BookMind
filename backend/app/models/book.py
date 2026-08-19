import enum
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base
from .associations import collection_books  # noqa: F401 — necessário para o relationship


class BookStatus(str, enum.Enum):
    none = "none"
    want_to_read = "want_to_read"
    reading = "reading"
    read = "read"
    abandoned = "abandoned"


book_status_type = Enum(BookStatus, name="bookstatus", native_enum=True)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str] = mapped_column(String(200))
    genre: Mapped[Optional[str]] = mapped_column(String(100))
    isbn: Mapped[Optional[str]] = mapped_column(String(20))
    cover_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    year_published: Mapped[Optional[int]] = mapped_column(Integer)
    rating: Mapped[Optional[float]] = mapped_column(Float)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=list, server_default='{}')
    title_en: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[BookStatus] = mapped_column(book_status_type, default=BookStatus.none)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(384))

    annotations: Mapped[list["Annotation"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    collections: Mapped[list["Collection"]] = relationship(  # noqa: F821
        secondary=collection_books,
        back_populates="books",
    )
