import uuid
from unittest.mock import AsyncMock

from backend.app.models import IngestJob


def test_ingest_acs_unauthorized(client):
    resp = client.post("/ingest/acs", json={"year": 2022, "state_fips": "06"})
    assert resp.status_code == 401


def test_ingest_acs_success(client, auth_token, monkeypatch):
    fake_job = IngestJob(id=uuid.uuid4(), type="acs", status="queued", params={"year": 2022})
    async_mock = AsyncMock(return_value=fake_job)
    from backend.app import services

    monkeypatch.setattr(services.ingestion.IngestionService, "ingest_acs", async_mock)
    resp = client.post(
        "/ingest/acs",
        json={"year": 2022, "state_fips": "06"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"


def test_ingest_hud_success(client, auth_token, monkeypatch):
    fake_job = IngestJob(id=uuid.uuid4(), type="hud", status="queued", params={"year": 2024})
    async_mock = AsyncMock(return_value=fake_job)
    from backend.app import services

    monkeypatch.setattr(services.ingestion.IngestionService, "ingest_hud", async_mock)
    resp = client.post(
        "/ingest/hud",
        json={"year": 2024},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 202


def test_get_job_not_found(client, auth_token):
    resp = client.get(f"/ingest/jobs/{uuid.uuid4()}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 404

