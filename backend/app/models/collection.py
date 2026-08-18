from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base
from .associations import collection_books


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    # 'curadoria' = lista editorial automática (prêmios, etc.)
    # 'personal'  = criada pelo usuário (implementado na T14)
    type: Mapped[str] = mapped_column(String(50), default="curadoria")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    books: Mapped[list["Book"]] = relationship(  # noqa: F821
        secondary=collection_books,
        back_populates="collections",
    )
