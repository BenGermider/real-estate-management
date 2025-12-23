import asyncio
from datetime import datetime

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings
from .db import Base, engine, SessionLocal, get_session
from .auth import get_password_hash
from .logger import configure_logging, get_logger
from .models import User, MetricsCache
from .routers import auth, datasets, ingestion, regions, metrics, insights, compare, ops
from .services.ingestion import IngestionService

settings = Settings()
configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Real Estate Management Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(ingestion.router)
app.include_router(regions.router)
app.include_router(metrics.router)
app.include_router(insights.router)
app.include_router(compare.router)
app.include_router(ops.router)


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # seed admin user and datasets
    async with SessionLocal() as session:
        await ensure_admin(session)
        service = IngestionService(session)
        await service.ensure_dataset_catalog()
        if settings.bootstrap_enabled:
            await schedule_bootstrap(session)


async def ensure_admin(session: AsyncSession):
    result = await session.execute(select(User).where(User.email == settings.admin_email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=settings.admin_email, password_hash=get_password_hash(settings.admin_password), roles=["admin"])
        session.add(user)
        await session.commit()
        logger.info("Seeded admin user", email=settings.admin_email)


async def schedule_bootstrap(session: AsyncSession):
    # avoid re-ingesting if data already present for latest year
    latest_year = settings.acs_latest_year
    exists = await session.execute(
        select(func.count()).select_from(MetricsCache).where(MetricsCache.year == latest_year)
    )
    if (exists.scalar() or 0) > 0:
        logger.info("Bootstrap ingestion skipped; data already present", year=latest_year)
        return
    service = IngestionService(session)
    states = settings.bootstrap_states or []
    logger.info("Triggering bootstrap ingestion", states=states, acs_year=latest_year, hud_year=settings.hud_latest_year)
    await service.ingest_acs(latest_year, states=states, force=False)
    await service.ingest_hud(settings.hud_latest_year, force=False)

