# Real Estate Management Backend

Backend implementation for the AI-powered real estate analytics system described in Prompt 1. Runs locally with `docker-compose` and automatically bootstraps ACS and HUD FMR data into Postgres on first start.

## Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.11+ if you want to run without containers

## Quickstart (local, via docker-compose)
1) Copy the sample environment:
```
cp env.example .env
```
2) Start services:
```
docker-compose up --build
```
This launches Postgres, Pub/Sub emulator, and the FastAPI backend. On first startup the backend seeds the admin user and automatically ingests ACS (states in `BOOTSTRAP_STATES`) and HUD FMR for the configured years, so the frontend can show real data without manual actions.

3) Access API docs (after startup completes):
- OpenAPI: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Auth
- Login with the seeded admin user (from `.env`):
```
POST /auth/login
{ "email": "admin@example.com", "password": "Password123!" }
```
Use the returned Bearer token for protected endpoints.

## Testing ingestion and metrics (manual)
- Trigger ACS ingestion (optional because bootstrap already ran):
```
curl -X POST http://localhost:8000/ingest/acs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2022, "state_fips": "06"}'
```
- Check job status:
```
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/ingest/jobs/<job_id>
```
- Fetch metrics for a region (replace with ingested region_id, e.g., 06037 for Los Angeles County):
```
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/metrics/region/06037
```

## Environment Variables
- All configuration lives in `.env` (see `env.example` for defaults). Key values:
  - `DATABASE_URL` (Async SQLAlchemy URL)
  - `JWT_SECRET`, `JWT_EXPIRES_SECONDS`
  - `PUBSUB_EMULATOR_HOST`, `GCP_PROJECT`, `PUBSUB_TOPIC_INGESTION`
  - `BIGQUERY_PROJECT`, `BIGQUERY_DATASET`
  - `ACS_LATEST_YEAR`, `HUD_LATEST_YEAR`, `BOOTSTRAP_STATES`, `BOOTSTRAP_ENABLED`

## Development (outside Docker)
```
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export $(cat .env | xargs)
uvicorn backend.app.main:app --reload
```

## Notes
- The backend adheres strictly to the API contract from Prompt 1; no additional endpoints were added.
- Bootstrapped ingestion is idempotent—restart of containers will not duplicate data.
- Pub/Sub publishing is wired to the emulator in docker-compose; swap to real Pub/Sub by removing `PUBSUB_EMULATOR_HOST` and setting proper credentials for GCP deployment.
