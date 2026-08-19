from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from ..core.database import get_db
from ..models.associations import collection_books
from ..models.book import Book
from ..models.collection import Collection
from ..schemas.book import BookResponse
from ..schemas.collection import CollectionSummary

router = APIRouter()

# Prêmios literários: nome canônico → palavras-chave para busca em título/descrição
_AWARD_KEYWORDS: dict[str, list[str]] = {
    "Nobel de Literatura": ["nobel"],
    "Prêmio Jabuti": ["jabuti"],
    "Booker Prize": ["booker"],
    "Prêmio Pulitzer": ["pulitzer"],
    "Prêmio Camões": ["camões", "camoes"],
}

def _slug(name: str) -> str:
    import re
    import unicodedata
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower().strip()).strip("-")


@router.get("/", response_model=list[CollectionSummary])
async def list_collections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collection, func.count(collection_books.c.book_id).label("book_count"))
        .outerjoin(collection_books, Collection.id == collection_books.c.collection_id)
        .where(Collection.type == "curadoria")
        .group_by(Collection.id)
        .order_by(Collection.name)
    )
    return [
        CollectionSummary(
            id=col.id,
            name=col.name,
            slug=col.slug,
            description=col.description,
            type=col.type,
            book_count=count,
        )
        for col, count in result.all()
    ]


@router.get("/{slug}/books", response_model=list[BookResponse])
async def get_collection_books(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book)
        .options(defer(Book.embedding))
        .join(collection_books, Book.id == collection_books.c.book_id)
        .join(Collection, Collection.id == collection_books.c.collection_id)
        .where(Collection.slug == slug)
        .order_by(Book.title)
    )
    return result.scalars().all()


@router.post("/initialize")
async def initialize_collections(db: AsyncSession = Depends(get_db)):
    """
    Escaneia títulos e descrições de todos os livros para detectar menções a prêmios
    literários e popula as coleções de curadoria automaticamente.
    Seguro para executar múltiplas vezes (usa ON CONFLICT DO NOTHING).
    """
    stats: dict[str, int] = {}

    for award_name, keywords in _AWARD_KEYWORDS.items():
        slug = _slug(award_name)

        # Cria a coleção se não existir
        col_result = await db.execute(select(Collection).where(Collection.slug == slug))
        collection = col_result.scalar_one_or_none()
        if not collection:
            collection = Collection(name=award_name, slug=slug, type="curadoria")
            db.add(collection)
            await db.flush()

        # Monta filtro ILIKE para cada keyword no título ou descrição
        conditions = []
        for kw in keywords:
            like = f"%{kw}%"
            conditions.append(Book.title.ilike(like))
            conditions.append(Book.description.ilike(like))

        books_result = await db.execute(
            select(Book.id).where(or_(*conditions))
        )
        book_ids = [row[0] for row in books_result.all()]

        if book_ids:
            await db.execute(
                pg_insert(collection_books)
                .values([{"collection_id": collection.id, "book_id": bid} for bid in book_ids])
                .on_conflict_do_nothing()
            )

        stats[award_name] = len(book_ids)

    await db.commit()
    return {"initialized": stats}
