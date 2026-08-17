from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models.collection import Collection
from ..schemas.book import BookResponse

router = APIRouter()


@router.get("/", response_model=list[dict])
async def list_collections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collection).order_by(Collection.name)
    )
    collections = result.scalars().all()
    return [
        {"id": c.id, "name": c.name, "slug": c.slug, "type": c.type}
        for c in collections
    ]


@router.get("/{slug}/books", response_model=list[BookResponse])
async def collection_books(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collection)
        .where(Collection.slug == slug)
        .options(selectinload(Collection.books))
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection.books
