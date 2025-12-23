import asyncio
import csv
import io
from datetime import datetime
from typing import List, Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..db import SessionLocal
from ..logger import get_logger
from ..models import Dataset, IngestJob, MetricsCache, Region
from .pubsub import PubSubPublisher

settings = Settings()
logger = get_logger(__name__)

ACS_VARS = ["NAME", "B19013_001E", "B25064_001E", "B01003_001E", "vacancy_rate"]


class IngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.pubsub = PubSubPublisher()

    async def _record_job(self, job: IngestJob):
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def ingest_acs(self, year: int, states: List[str], county_fips: Optional[str] = None, force: bool = False) -> IngestJob:
        if not states:
            states = settings.bootstrap_states
        if not states:
            raise ValueError("At least one state_fips is required for ACS ingestion")
        job = IngestJob(type="acs", status="queued", params={"year": year, "states": states, "county_fips": county_fips, "force": force})
        await self._record_job(job)
        self.pubsub.publish_ingestion({"job_id": str(job.id), "type": "acs", "params": job.params, "requested_at": datetime.utcnow().isoformat()})
        asyncio.create_task(self._run_acs(job, year, states, county_fips, force))
        return job

    async def _run_acs(self, job: IngestJob, year: int, states: List[str], county_fips: Optional[str], force: bool):
        async with SessionLocal() as session:
            await session.execute(update(IngestJob).where(IngestJob.id == job.id).values(status="running", started_at=datetime.utcnow()))
            await session.commit()
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                for state in states:
                    params = {
                        "get": "NAME,B19013_001E,B25064_001E,B01003_001E",
                        "for": f"county:{county_fips or '*'}",
                        "in": f"state:{state}",
                    }
                    url = f"https://api.census.gov/data/{year}/acs/acs5"
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    header = data[0]
                    for row in data[1:]:
                        record = dict(zip(header, row))
                        county = record.get("county")
                        region_id = f"{state}{county}"
                        name = record.get("NAME")
                        income = float(record.get("B19013_001E")) if record.get("B19013_001E") not in (None, "") else None
                        rent = float(record.get("B25064_001E")) if record.get("B25064_001E") not in (None, "") else None
                        population = int(record.get("B01003_001E")) if record.get("B01003_001E") not in (None, "") else None
                        await self._upsert_region(session, region_id, name, "county", state, county)
                        await self._upsert_metrics(session, region_id, year, income, rent, population, None, source="acs", force=force)
            await self._update_job_status(session, job.id, "succeeded", message="ACS ingestion completed")
        except Exception as exc:
            logger.error("ACS ingestion failed", error=str(exc))
            async with SessionLocal() as session:
                await self._update_job_status(session, job.id, "failed", message=str(exc))

    async def ingest_hud(self, year: int, force: bool = False) -> IngestJob:
        job = IngestJob(type="hud", status="queued", params={"year": year, "force": force})
        await self._record_job(job)
        self.pubsub.publish_ingestion({"job_id": str(job.id), "type": "hud", "params": job.params, "requested_at": datetime.utcnow().isoformat()})
        asyncio.create_task(self._run_hud(job, year, force))
        return job

    async def _run_hud(self, job: IngestJob, year: int, force: bool):
        async with SessionLocal() as session:
            await session.execute(update(IngestJob).where(IngestJob.id == job.id).values(status="running", started_at=datetime.utcnow()))
            await session.commit()
        try:
            url = f"https://www.huduser.gov/portal/datasets/fmr/fmr{year}/FY{year}_FMRs.csv"
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                text = resp.text
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                state = row.get("StateFIPS")
                county = row.get("CountyFIPS")
                region_id = f"{state}{county}"
                name = row.get("CountyName")
                fmr = row.get("FMR2")
                hud_fmr_2br = float(fmr) if fmr else None
                await self._upsert_region(session, region_id, name, "county", state, county)
                await self._upsert_metrics(session, region_id, year, None, None, None, hud_fmr_2br, source="hud", force=force)
            await self._update_job_status(session, job.id, "succeeded", message="HUD ingestion completed")
        except Exception as exc:
            logger.error("HUD ingestion failed", error=str(exc))
            async with SessionLocal() as session:
                await self._update_job_status(session, job.id, "failed", message=str(exc))

    async def _upsert_region(self, session: AsyncSession, region_id: str, name: str, region_type: str, state_fips: str, county_fips: Optional[str]):
        result = await session.execute(select(Region).where(Region.region_id == region_id))
        region = result.scalar_one_or_none()
        if region:
            return
        region = Region(region_id=region_id, name=name, type=region_type, state_fips=state_fips, county_fips=county_fips)
        session.add(region)
        await session.commit()

    async def _upsert_metrics(
        self,
        session: AsyncSession,
        region_id: str,
        year: int,
        income: Optional[float],
        rent: Optional[float],
        population: Optional[int],
        hud_fmr_2br: Optional[float],
        source: str,
        force: bool = False,
    ):
        result = await session.execute(
            select(MetricsCache).where(MetricsCache.region_id == region_id, MetricsCache.year == year)
        )
        metric = result.scalar_one_or_none()
        rent_to_income = None
        if income and rent:
            rent_to_income = rent * 12 / income
        sources = [source]
        if metric:
            if not force:
                # merge sources and keep existing values if already present
                sources = list(set(metric.sources or []) | set([source]))
                income = income or metric.median_household_income
                rent = rent or metric.median_gross_rent
                population = population or metric.population
                hud_fmr_2br = hud_fmr_2br or metric.hud_fmr_2br
                rent_to_income = rent_to_income or metric.rent_to_income_ratio
            metric.median_household_income = income
            metric.median_gross_rent = rent
            metric.population = population
            metric.hud_fmr_2br = hud_fmr_2br
            metric.rent_to_income_ratio = rent_to_income
            metric.sources = sources
        else:
            metric = MetricsCache(
                region_id=region_id,
                year=year,
                median_household_income=income,
                median_gross_rent=rent,
                population=population,
                hud_fmr_2br=hud_fmr_2br,
                rent_to_income_ratio=rent_to_income,
                sources=sources,
            )
            session.add(metric)
        await session.commit()

    async def _update_job_status(self, session: AsyncSession, job_id, status: str, message: Optional[str] = None, output_uri: Optional[str] = None):
        await session.execute(
            update(IngestJob)
            .where(IngestJob.id == job_id)
            .values(status=status, finished_at=datetime.utcnow(), message=message, output_uri=output_uri)
        )
        await session.commit()

    async def ensure_dataset_catalog(self):
        datasets = [
            Dataset(
                id="acs",
                source="acs",
                title="American Community Survey (ACS)",
                description="US Census ACS 5-year estimates",
                schema={"fields": ["NAME", "B19013_001E", "B25064_001E", "B01003_001E"]},
                last_updated=datetime.utcnow(),
            ),
            Dataset(
                id="hud_fmr",
                source="hud",
                title="HUD Fair Market Rent",
                description="HUD FMR by county",
                schema={"fields": ["StateFIPS", "CountyFIPS", "FMR2"]},
                last_updated=datetime.utcnow(),
            ),
        ]
        for ds in datasets:
            existing = await self.session.get(Dataset, ds.id)
            if existing:
                continue
            self.session.add(ds)
        await self.session.commit()

