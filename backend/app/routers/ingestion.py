from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import get_current_user
from ..db import get_session
from ..models import IngestJob, User
from ..services.ingestion import IngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/acs", response_model=schemas.IngestJobResponse, status_code=202)
async def ingest_acs(request: schemas.IngestRequestACS, session: AsyncSession = Depends(get_session), _: User = Depends(get_current_user)):
    service = IngestionService(session)
    try:
        job = await service.ingest_acs(request.year, states=[request.state_fips] if request.state_fips else [], county_fips=request.county_fips, force=request.force or False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"job_id": str(job.id), "status": job.status}


@router.post("/hud", response_model=schemas.IngestJobResponse, status_code=202)
async def ingest_hud(request: schemas.IngestRequestHUD, session: AsyncSession = Depends(get_session), _: User = Depends(get_current_user)):
    service = IngestionService(session)
    job = await service.ingest_hud(request.year, force=request.force or False)
    return {"job_id": str(job.id), "status": job.status}


@router.get("/jobs/{job_id}", response_model=schemas.IngestJobResponse)
async def get_job(job_id: str, session: AsyncSession = Depends(get_session), _: User = Depends(get_current_user)):
    job = await session.get(IngestJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": str(job.id),
        "type": job.type,
        "status": job.status,
        "submitted_at": job.submitted_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "message": job.message,
        "output_uri": job.output_uri,
    }

