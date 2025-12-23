from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import get_current_user
from ..db import get_session
from ..models import Dataset, User

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=schemas.DatasetListResponse)
async def list_datasets(
    source: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    query = select(Dataset)
    if source:
        query = query.where(Dataset.source == source)
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    result = await session.execute(query.offset(offset).limit(limit))
    items = result.scalars().all()
    data = [
        schemas.DatasetItem(
            id=d.id,
            source=d.source,
            title=d.title,
            description=d.description,
            last_updated=d.last_updated.isoformat() if d.last_updated else None,
        )
        for d in items
    ]
    return {"items": data, "total": total or 0}


@router.get("/{dataset_id}", response_model=schemas.DatasetDetail)
async def get_dataset(dataset_id: str, session: AsyncSession = Depends(get_session), _: User = Depends(get_current_user)):
    dataset = await session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {
        "id": dataset.id,
        "source": dataset.source,
        "title": dataset.title,
        "description": dataset.description,
        "schema": dataset.schema,
        "last_updated": dataset.last_updated.isoformat() if dataset.last_updated else None,
        "sample": dataset.sample,
    }

