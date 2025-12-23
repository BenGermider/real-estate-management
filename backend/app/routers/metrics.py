from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import get_current_user
from ..db import get_session
from ..models import User
from ..services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/region/{region_id}", response_model=schemas.RegionMetrics)
async def get_region_metrics(region_id: str, year: int | None = None, session: AsyncSession = Depends(get_session), _: User = Depends(get_current_user)):
    service = MetricsService(session)
    metric = await service.get_region_metrics(region_id, year)
    if not metric:
        raise HTTPException(status_code=404, detail="Not found")
    if isinstance(metric, dict):
        return {
            "region_id": region_id,
            "year": metric.get("year"),
            "median_household_income": metric.get("median_household_income") or 0,
            "median_gross_rent": metric.get("median_gross_rent") or 0,
            "rent_to_income_ratio": metric.get("rent_to_income_ratio") or 0,
            "vacancy_rate": metric.get("vacancy_rate"),
            "hud_fmr_2br": metric.get("hud_fmr_2br"),
            "population": metric.get("population"),
            "sources": metric.get("sources", ["bigquery"]),
        }
    return {
        "region_id": region_id,
        "year": metric.year,
        "median_household_income": metric.median_household_income or 0,
        "median_gross_rent": metric.median_gross_rent or 0,
        "rent_to_income_ratio": metric.rent_to_income_ratio or 0,
        "vacancy_rate": metric.vacancy_rate,
        "hud_fmr_2br": metric.hud_fmr_2br,
        "population": metric.population,
        "sources": metric.sources if hasattr(metric, "sources") else ["bigquery"],
    }


@router.get("/region/{region_id}/timeseries", response_model=schemas.RegionTimeseriesResponse)
async def get_region_timeseries(
    region_id: str,
    start_year: int | None = None,
    end_year: int | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    service = MetricsService(session)
    series = await service.get_timeseries(region_id, start_year, end_year)
    data = []
    for s in series:
        data.append(
            {
                "year": s.year if hasattr(s, "year") else s.get("year"),
                "median_household_income": s.median_household_income if hasattr(s, "median_household_income") else s.get("median_household_income"),
                "median_gross_rent": s.median_gross_rent if hasattr(s, "median_gross_rent") else s.get("median_gross_rent"),
                "hud_fmr_2br": s.hud_fmr_2br if hasattr(s, "hud_fmr_2br") else s.get("hud_fmr_2br"),
                "rent_to_income_ratio": s.rent_to_income_ratio if hasattr(s, "rent_to_income_ratio") else s.get("rent_to_income_ratio"),
            }
        )
    return {"region_id": region_id, "series": data}

