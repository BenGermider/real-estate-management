from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import get_current_user
from ..db import get_session
from ..models import User
from ..services.metrics import MetricsService

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("/regions", response_model=schemas.CompareRegionsResponse)
async def compare_regions(region_ids: str, year: int | None = None, session: AsyncSession = Depends(get_session), _: User = Depends(get_current_user)):
    ids = [r.strip() for r in region_ids.split(",") if r.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="region_ids required")
    service = MetricsService(session)
    regions = await service.compare_regions(ids, year)
    return {"regions": regions}

