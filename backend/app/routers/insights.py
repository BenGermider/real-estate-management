from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import get_current_user
from ..db import get_session
from ..models import User
from ..services.metrics import MetricsService

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/region/{region_id}", response_model=schemas.RegionInsight)
async def region_insights(region_id: str, year: int | None = None, session: AsyncSession = Depends(get_session), _: User = Depends(get_current_user)):
    service = MetricsService(session)
    insight = await service.get_insights(region_id, year)
    if not insight:
        raise HTTPException(status_code=404, detail="Not found")
    return insight

