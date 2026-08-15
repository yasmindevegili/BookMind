from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import AsyncSessionLocal, get_db
from ..models.annotation import Annotation
from ..schemas.annotation import AnnotationCreate, AnnotationResponse
from ..services.embeddings import embedding_service

router = APIRouter()


async def _generate_embedding(annotation_id: int) -> None:
    """Background task: generate and store embedding for one annotation.

    Why background? Embedding takes ~200ms. We don't want the user to wait for
    it when saving a highlight — they should get instant confirmation.
    The annotation is still saved; it just won't be searchable until embedded.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Annotation).where(Annotation.id == annotation_id))
        annotation = result.scalar_one_or_none()
        if annotation and not annotation.embedded_at:
            annotation.embedding = await embedding_service.embed(annotation.content)
            annotation.embedded_at = datetime.utcnow()
            await db.commit()


@router.get("/book/{book_id}", response_model=list[AnnotationResponse])
async def list_book_annotations(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Annotation)
        .where(Annotation.book_id == book_id)
        .order_by(Annotation.created_at.asc())
    )
    return result.scalars().all()


@router.post("/", response_model=AnnotationResponse)
async def create_annotation(
    data: AnnotationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    annotation = Annotation(**data.model_dump())
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)
    # Embed in background so the response is instant
    background_tasks.add_task(_generate_embedding, annotation.id)
    return annotation


@router.delete("/{annotation_id}")
async def delete_annotation(annotation_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Annotation).where(Annotation.id == annotation_id))
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    await db.delete(annotation)
    await db.commit()
    return {"detail": "deleted"}


@router.post("/embed-all")
async def embed_all(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger embedding for all annotations that haven't been indexed yet.
    Call this after seeding the database or importing books.
    """
    result = await db.execute(select(Annotation).where(Annotation.embedded_at.is_(None)))
    pending = result.scalars().all()
    for ann in pending:
        background_tasks.add_task(_generate_embedding, ann.id)
    return {"queued": len(pending), "message": f"Indexando {len(pending)} anotações em background"}
