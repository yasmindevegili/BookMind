from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import AsyncSessionLocal, get_db
from ..models.book import Book, BookStatus
from ..schemas.book import BookCreate, BookResponse, BookStatusUpdate, BookUpdate
from ..services.covers import cover_service
from ..services.embeddings import embedding_service

router = APIRouter()

STATUS_ORDER = case(
    (Book.status == BookStatus.none, 0),
    (Book.status == BookStatus.want_to_read, 1),
    (Book.status == BookStatus.reading, 2),
    (Book.status == BookStatus.read, 3),
    (Book.status == BookStatus.abandoned, 4),
    else_=5,
)


async def _generate_book_embedding(book_id: int) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if not book:
            return
        parts = [book.title, book.author]
        if book.genre:
            parts.append(book.genre)
        if book.description:
            parts.append(book.description)
        book.embedding = await embedding_service.embed(". ".join(parts))
        await db.commit()


async def _fetch_book_cover(book_id: int) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if not book or book.cover_url:
            return
        url = await cover_service.fetch(book.title, book.author, book.isbn)
        if url:
            book.cover_url = url
            await db.commit()


@router.get("/tags", response_model=list[str])
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(func.unnest(Book.tags)).distinct().order_by(func.unnest(Book.tags))
    )
    return [row[0] for row in result.all() if row[0]]


@router.get("/by-tag/{tag}", response_model=list[BookResponse])
async def books_by_tag(tag: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).where(Book.tags.any(tag)).order_by(Book.title)
    )
    return result.scalars().all()


@router.get("/by-status/{status}", response_model=list[BookResponse])
async def books_by_status(status: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).where(Book.status == status).order_by(Book.title)
    )
    return result.scalars().all()


@router.get("/", response_model=list[BookResponse])
async def list_books(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    q = select(Book).order_by(STATUS_ORDER, Book.title)
    if settings.DEBUG_BOOK_LIMIT > 0:
        q = q.limit(settings.DEBUG_BOOK_LIMIT)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=BookResponse)
async def create_book(
    data: BookCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    book = Book(**data.model_dump())
    db.add(book)
    await db.commit()
    await db.refresh(book)
    background_tasks.add_task(_generate_book_embedding, book.id)
    if not book.cover_url:
        background_tasks.add_task(_fetch_book_cover, book.id)
    return book


@router.get("/{book_id}/similar", response_model=list[BookResponse])
async def similar_books(book_id: int, limit: int = 5, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.embedding is None:
        return []
    similar = await db.execute(
        select(Book)
        .where(Book.id != book_id)
        .where(Book.embedding.is_not(None))
        .order_by(Book.embedding.cosine_distance(book.embedding))
        .limit(limit)
    )
    return similar.scalars().all()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, data: BookUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    await db.commit()
    await db.refresh(book)
    return book


@router.patch("/{book_id}/status", response_model=BookResponse)
async def update_book_status(book_id: int, data: BookStatusUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.status = data.status
    await db.commit()
    await db.refresh(book)
    return book


@router.post("/fetch-missing-covers")
async def fetch_missing_covers(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Busca capas para todos os livros que ainda não têm cover_url."""
    result = await db.execute(
        select(Book).where((Book.cover_url.is_(None)) | (Book.cover_url == ""))
    )
    pending = result.scalars().all()
    for book in pending:
        background_tasks.add_task(_fetch_book_cover, book.id)
    return {"queued": len(pending)}


@router.post("/embed-all-books")
async def embed_all_books(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Gera embeddings para todos os livros que ainda não têm vetor. Uso único após migração."""
    result = await db.execute(select(Book).where(Book.embedding.is_(None)))
    pending = result.scalars().all()
    for book in pending:
        background_tasks.add_task(_generate_book_embedding, book.id)
    return {"queued": len(pending)}


@router.delete("/{book_id}")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(book)
    await db.commit()
    return {"detail": "deleted"}
