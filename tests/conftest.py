import os
import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure test-safe environment before importing the app
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "Password123!")
os.environ.setdefault("BOOTSTRAP_ENABLED", "false")
os.environ.setdefault("PUBSUB_EMULATOR_HOST", "pubsub:8085")
os.environ.setdefault("POSTGRES_USER", "rem")
os.environ.setdefault("POSTGRES_PASSWORD", "rem")
os.environ.setdefault("POSTGRES_DB", "rem")
os.environ.setdefault("POSTGRES_HOST", "postgres")
os.environ.setdefault("POSTGRES_PORT", "5432")

from backend.app.main import app  # noqa: E402
from backend.app.db import Base, get_session, engine, SessionLocal  # noqa: E402
from backend.app.models import Region, MetricsCache  # noqa: E402
from backend.app.services import ingestion as ingestion_module  # noqa: E402
from backend.app.services import bq as bq_module  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
async def session():
    async with SessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
def mock_external(monkeypatch):
    class DummyPubSub:
        def publish_ingestion(self, message):  # pragma: no cover - trivial
            return None

        def publish_status(self, message):  # pragma: no cover - trivial
            return None

    class DummyBQ:
        async def fetch_latest_metrics(self, region_id):
            return None

        async def fetch_timeseries(self, region_id, start_year, end_year):
            return []

    monkeypatch.setattr(ingestion_module, "PubSubPublisher", lambda: DummyPubSub())
    monkeypatch.setattr(bq_module, "BigQueryClient", lambda: DummyBQ())
    return


@pytest.fixture
def client(session, monkeypatch):
    async def override_get_session() -> AsyncSession:
        async with SessionLocal() as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(client):
    resp = client.post("/auth/login", json={"email": os.environ["ADMIN_EMAIL"], "password": os.environ["ADMIN_PASSWORD"]})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
async def seeded_region(session):
    region = Region(region_id="06037", name="Los Angeles County, California", type="county", state_fips="06", county_fips="037")
    session.add(region)
    await session.commit()
    return region


@pytest.fixture
async def seeded_metrics(session, seeded_region):
    metric = MetricsCache(
        region_id=seeded_region.region_id,
        year=2022,
        median_household_income=80000,
        median_gross_rent=2000,
        rent_to_income_ratio=0.30,
        hud_fmr_2br=2300,
        population=10000000,
        sources=["acs", "hud"],
    )
    session.add(metric)
    await session.commit()
    return metric

