from sqlalchemy import Column, ForeignKey, Integer, Table

from ..core.database import Base

collection_books = Table(
    "collection_books",
    Base.metadata,
    Column("collection_id", Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
)
