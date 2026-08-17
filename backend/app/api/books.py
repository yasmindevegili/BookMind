from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import AsyncSessionLocal, get_db
from ..models.book import Book, BookStatus
from ..schemas.book import BookCreate, BookResponse, BookStatusUpdate, BookUpdate
from ..services.covers import cover_service
from ..services.embeddings import embedding_service
from ..services.metadata import metadata_service
from ..services.tagger import tagger_service

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
        if book.tags:
            parts.append(", ".join(book.tags))
        if book.description:
            parts.append(book.description)
        book.embedding = await embedding_service.embed(". ".join(parts))
        await db.commit()


async def _enrich_book_metadata(book_id: int) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if not book:
            return
        meta = await metadata_service.fetch(book.title, book.author, book.isbn)
        changed = False
        if meta["description"] and not book.description:
            book.description = meta["description"]
            changed = True
        if meta["year_published"] and not book.year_published:
            book.year_published = meta["year_published"]
            changed = True
        if changed:
            await db.commit()
            await db.refresh(book)
            # Regenera embedding com os metadados enriquecidos
            await _generate_book_embedding(book_id)


async def _tag_book(book_id: int) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if not book:
            return
        tags = await tagger_service.tag(book.title, book.author, book.description, book.isbn)
        if tags:
            book.tags = tags
            await db.commit()
            await _generate_book_embedding(book_id)


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
    result = await db.execute(select(Book).order_by(STATUS_ORDER, Book.title))
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


@router.post("/enrich-descriptions")
async def enrich_descriptions(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Busca descrição e ano no Google Books para livros sem esses campos e regenera embeddings."""
    result = await db.execute(
        select(Book).where((Book.description.is_(None)) | (Book.description == ""))
    )
    pending = result.scalars().all()
    for book in pending:
        background_tasks.add_task(_enrich_book_metadata, book.id)
    return {"queued": len(pending)}


@router.post("/tag-all")
async def tag_all_books(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Gera tags literárias para livros sem tags via Open Library + LLM fallback."""
    result = await db.execute(
        select(Book).where(
            (Book.tags.is_(None)) | (func.cardinality(Book.tags) == 0)
        )
    )
    pending = result.scalars().all()
    for book in pending:
        background_tasks.add_task(_tag_book, book.id)
    return {"queued": len(pending)}


@router.post("/normalize-tags")
async def normalize_tags(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Traduz e normaliza todas as tags para português com acentuação correta.

    Coleta as tags distintas do banco, envia em batches ao LLM para tradução,
    e atualiza todos os livros com as tags corrigidas. Roda de forma síncrona
    e retorna ao final com o resumo do que foi alterado.
    """
    from groq import AsyncGroq

    client = AsyncGroq(api_key=get_settings().GROQ_API_KEY)

    # 1. Coleta todas as tags distintas
    result = await db.execute(
        select(func.unnest(Book.tags)).distinct()
    )
    all_tags = [row[0] for row in result.all() if row[0]]
    if not all_tags:
        return {"message": "Nenhuma tag encontrada.", "updated_books": 0}

    # 2. Traduz em batches de 60 tags por chamada ao LLM
    mapping: dict[str, str] = {}
    batch_size = 60
    for i in range(0, len(all_tags), batch_size):
        batch = all_tags[i:i + batch_size]
        tags_str = "\n".join(f"- {t}" for t in batch)
        prompt = (
            "Traduza e normalize as tags literárias abaixo para português do Brasil, "
            "com acentuação e ortografia corretas, em letras minúsculas. "
            "Mantenha o significado original. Responda APENAS no formato:\n"
            "tag original|tag em português\n\n"
            f"Tags:\n{tags_str}"
        )
        try:
            resp = await client.chat.completions.create(
                model=get_settings().GENERATION_MODEL,
                max_tokens=400,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            for line in resp.choices[0].message.content.strip().splitlines():
                if "|" in line:
                    original, translated = line.split("|", 1)
                    original = original.strip().lstrip("- ")
                    translated = translated.strip().lower()
                    if original and translated:
                        mapping[original] = translated
        except Exception:
            # Se o batch falhar, mantém as tags originais
            for t in batch:
                mapping[t] = t

    # 3. Atualiza os livros cujas tags mudaram
    books_result = await db.execute(
        select(Book).where(func.cardinality(Book.tags) > 0)
    )
    books = books_result.scalars().all()
    updated_ids = []
    for book in books:
        new_tags = [mapping.get(t, t) for t in book.tags]
        if new_tags != book.tags:
            book.tags = new_tags
            updated_ids.append(book.id)
    if updated_ids:
        await db.commit()
        for book_id in updated_ids:
            background_tasks.add_task(_generate_book_embedding, book_id)

    return {
        "distinct_tags_processed": len(all_tags),
        "books_updated": len(updated_ids),
        "sample_translations": dict(list(mapping.items())[:10]),
    }


@router.delete("/{book_id}")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(book)
    await db.commit()
    return {"detail": "deleted"}
