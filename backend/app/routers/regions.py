from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import get_current_user
from ..db import get_session
from ..models import Region, User

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=schemas.RegionListResponse)
async def list_regions(
    state_fips: str | None = None,
    county_fips: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    query = select(Region)
    if state_fips:
        query = query.where(Region.state_fips == state_fips)
    if county_fips:
        query = query.where(Region.county_fips == county_fips)
    if q:
        query = query.where(Region.name.ilike(f"%{q}%"))
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    result = await session.execute(query.offset(offset).limit(limit))
    items = result.scalars().all()
    return {
        "items": [
            {
                "region_id": r.region_id,
                "name": r.name,
                "type": r.type,
                "state_fips": r.state_fips,
                "county_fips": r.county_fips,
            }
            for r in items
        ],
        "total": total or 0,
    }

