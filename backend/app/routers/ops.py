from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .. import schemas

router = APIRouter(tags=["ops"])


@router.get("/health", response_model=schemas.HealthResponse)
async def health():
    return {"status": "ok", "version": "1.0.0"}


@router.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

