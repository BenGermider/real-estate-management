from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..logger import get_logger
from ..models import MetricsCache, Region
from .bq import BigQueryClient

logger = get_logger(__name__)


class MetricsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bq = BigQueryClient()

    async def get_region_metrics(self, region_id: str, year: Optional[int]):
        query = select(MetricsCache).where(MetricsCache.region_id == region_id)
        if year:
            query = query.where(MetricsCache.year == year)
        else:
            query = query.order_by(MetricsCache.year.desc())
        result = await self.session.execute(query)
        metric = result.scalars().first()
        if metric:
            return metric
        # fallback to BigQuery if not found
        bq_row = await self.bq.fetch_latest_metrics(region_id)
        return bq_row

    async def get_timeseries(self, region_id: str, start_year: Optional[int], end_year: Optional[int]):
        query = select(MetricsCache).where(MetricsCache.region_id == region_id)
        if start_year:
            query = query.where(MetricsCache.year >= start_year)
        if end_year:
            query = query.where(MetricsCache.year <= end_year)
        query = query.order_by(MetricsCache.year)
        result = await self.session.execute(query)
        items = result.scalars().all()
        if items:
            return items
        return await self.bq.fetch_timeseries(region_id, start_year, end_year)

    async def get_insights(self, region_id: str, year: Optional[int]):
        metrics = await self.get_region_metrics(region_id, year)
        if not metrics:
            return None
        rent_to_income = metrics.get("rent_to_income_ratio") if isinstance(metrics, dict) else metrics.rent_to_income_ratio
        rent_to_income = rent_to_income or 0
        affordability_quartile = "Q4"
        if rent_to_income <= 0.2:
            affordability_quartile = "Q1"
        elif rent_to_income <= 0.25:
            affordability_quartile = "Q2"
        elif rent_to_income <= 0.3:
            affordability_quartile = "Q3"
        trend = "stable"
        metric_year = metrics.get("year") if isinstance(metrics, dict) else metrics.year
        series = await self.get_timeseries(region_id, (metric_year or 0) - 3, metric_year)
        if series and len(series) >= 2:
            deltas = []
            for s in series:
                val = s.rent_to_income_ratio if hasattr(s, "rent_to_income_ratio") else s.get("rent_to_income_ratio")
                if val:
                    deltas.append(val)
            if len(deltas) >= 2:
                if deltas[-1] < deltas[0]:
                    trend = "improving"
                elif deltas[-1] > deltas[0]:
                    trend = "worsening"
        callouts = [
            {"metric": "rent_to_income_ratio", "delta": rent_to_income, "direction": "up" if rent_to_income > 0.3 else "down"},
        ]
        narrative = f"Rent-to-income ratio is {rent_to_income:.2f}, placing the region in {affordability_quartile} affordability."
        return {
            "region_id": region_id,
            "year": metric_year,
            "affordability_quartile": affordability_quartile,
            "trend": trend,
            "callouts": callouts,
            "narrative": narrative,
        }

    async def compare_regions(self, region_ids: List[str], year: Optional[int]):
        query = select(MetricsCache).where(MetricsCache.region_id.in_(region_ids))
        if year:
            query = query.where(MetricsCache.year == year)
        result = await self.session.execute(query)
        metrics = result.scalars().all()
        regions = await self.session.execute(select(Region).where(Region.region_id.in_(region_ids)))
        region_map = {r.region_id: r for r in regions.scalars().all()}
        response = []
        for m in metrics:
            region = region_map.get(m.region_id)
            response.append(
                {
                    "region_id": m.region_id,
                    "name": region.name if region else m.region_id,
                    "year": m.year,
                    "median_household_income": m.median_household_income,
                    "median_gross_rent": m.median_gross_rent,
                    "hud_fmr_2br": m.hud_fmr_2br,
                    "rent_to_income_ratio": m.rent_to_income_ratio,
                }
            )
        return response

