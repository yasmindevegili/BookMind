from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..models.annotation import Annotation
from ..models.book import Book

router = APIRouter()


@router.get("/")
async def get_profile(db: AsyncSession = Depends(get_db)):
    books_result = await db.execute(select(Book))
    books = books_result.scalars().all()

    annotations_result = await db.execute(select(Annotation))
    annotations = annotations_result.scalars().all()

    status_counts: dict[str, int] = {}
    genre_counts: dict[str, int] = {}
    rated_books = [b for b in books if b.rating]

    for book in books:
        status_counts[book.status] = status_counts.get(book.status, 0) + 1
        if book.genre:
            genre_counts[book.genre] = genre_counts.get(book.genre, 0) + 1

    embedded_count = sum(1 for a in annotations if a.embedded_at)

    return {
        "total_books": len(books),
        "total_annotations": len(annotations),
        "indexed_annotations": embedded_count,
        "status_distribution": status_counts,
        "favorite_genres": sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        "average_rating": sum(b.rating for b in rated_books) / len(rated_books) if rated_books else None,
    }
