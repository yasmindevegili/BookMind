from datetime import datetime

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from ..core.database import AsyncSessionLocal, get_db
from ..models.book import Book, BookStatus
from ..schemas.book import BookCreate, BookResponse, BookStatusUpdate, BookUpdate
from ..services.covers import cover_service
from ..services.embeddings import embedding_service

router = APIRouter()

STATUS_ORDER = case(
    (Book.status == BookStatus.want_to_read, 0),
    (Book.status == BookStatus.reading, 1),
    (Book.status == BookStatus.read, 2),
    (Book.status == BookStatus.abandoned, 3),
    (Book.status == BookStatus.none, 4),
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
        select(Book).options(defer(Book.embedding)).where(Book.tags.any(tag)).order_by(Book.title)
    )
    return result.scalars().all()


@router.get("/by-status/{status}", response_model=list[BookResponse])
async def books_by_status(status: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).options(defer(Book.embedding)).where(Book.status == status).order_by(Book.title)
    )
    return result.scalars().all()


@router.get("/", response_model=list[BookResponse])
async def list_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).options(defer(Book.embedding)).order_by(STATUS_ORDER, Book.title)
    )
    return result.scalars().all()


@router.get("/discover", response_model=list[BookResponse])
async def discover_books(
    limit: int = 56,
    recently_viewed: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    recently_ids = {int(x) for x in recently_viewed.split(",") if x.strip().isdigit()}

    # Carrega apenas os livros que formam o perfil de gosto (conjunto pequeno)
    profile_statuses = [BookStatus.read, BookStatus.want_to_read]
    profile_filter = Book.status.in_(profile_statuses)
    if recently_ids:
        from sqlalchemy import or_
        profile_filter = or_(profile_filter, Book.id.in_(recently_ids))

    profile_result = await db.execute(
        select(Book).where(profile_filter).where(Book.embedding.is_not(None))
    )
    profile_books = profile_result.scalars().all()

    if not profile_books:
        # Sem perfil: fallback para want_to_read primeiro, depois alfabético
        fallback = await db.execute(
            select(Book)
            .options(defer(Book.embedding))
            .where(Book.status.notin_([BookStatus.read, BookStatus.reading, BookStatus.abandoned]))
            .order_by(STATUS_ORDER, Book.title)
            .limit(limit)
        )
        return fallback.scalars().all()

    # Computa o vetor de gosto ponderado em Python (poucos livros)
    weights_map = {BookStatus.read: 1.0, BookStatus.want_to_read: 0.6}
    profile: list[tuple[list[float], float]] = []
    for b in profile_books:
        w = weights_map.get(b.status, 0.4 if b.id in recently_ids else 0.0)
        if w > 0:
            profile.append((b.embedding, w))

    vecs = np.array([v for v, _ in profile], dtype=np.float32)
    weights = np.array([w for _, w in profile], dtype=np.float32)
    taste = np.average(vecs, axis=0, weights=weights)
    norm = np.linalg.norm(taste)
    if norm > 0:
        taste /= norm

    # Ranking feito pelo pgvector no banco — zero loop Python sobre candidatos
    exclude = [BookStatus.read, BookStatus.reading, BookStatus.abandoned]
    ranked = await db.execute(
        select(Book)
        .options(defer(Book.embedding))
        .where(Book.status.notin_(exclude))
        .where(Book.embedding.is_not(None))
        .order_by(Book.embedding.cosine_distance(taste.tolist()))
        .limit(limit)
    )
    return ranked.scalars().all()


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
