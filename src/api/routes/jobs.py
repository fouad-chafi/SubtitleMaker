"""Job management endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...models.job import JobStatus
from ...services.transcription_service import TranscriptionService
from ..schemas import JobListResponse, TranscriptionResponse

router = APIRouter()

# Global service (set by main.py)
_service: TranscriptionService = None


def set_service(service: TranscriptionService):
    """Set the global service instance."""
    global _service
    _service = service


def get_service() -> TranscriptionService:
    """Get the global service instance."""
    if _service is None:
        raise RuntimeError("Service not initialized")
    return _service


def parse_uuid(job_id_str: str) -> uuid.UUID:
    """Parse UUID from string."""
    try:
        return uuid.UUID(job_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> JobListResponse:
    """
    List transcription jobs with optional filtering.
    """
    service = get_service()
    jobs = await service.list_jobs(status=status, limit=limit, offset=offset)

    return JobListResponse(
        jobs=[
            TranscriptionResponse(
                job_id=j.id,
                status=j.status.value,
                progress=j.progress,
                filename=j.filename,
                detected_language=j.detected_language,
                output_path=j.output_path,
                video_output_path=j.video_output_path,
                error_message=j.error_message,
                created_at=j.created_at,
                started_at=j.started_at,
                completed_at=j.completed_at,
                processing_time_seconds=j.processing_time_seconds,
                vram_used_mb=j.vram_used_mb,
            )
            for j in jobs
        ],
        total=len(jobs),
        page=offset // limit + 1,
        page_size=limit,
    )


@router.get("/{job_id}", response_model=TranscriptionResponse)
async def get_job(
    job_id: str,
) -> TranscriptionResponse:
    """
    Get a specific job by ID.
    """
    service = get_service()
    job_id_uuid = parse_uuid(job_id)
    job = await service.get_job(job_id_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return TranscriptionResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        filename=job.filename,
        detected_language=job.detected_language,
        output_path=job.output_path,
        video_output_path=job.video_output_path,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        processing_time_seconds=job.processing_time_seconds,
        vram_used_mb=job.vram_used_mb,
    )


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
):
    """
    Delete a job and its output files.
    """
    service = get_service()
    job_id_uuid = parse_uuid(job_id)
    deleted = await service.delete_job(job_id_uuid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": "Job deleted successfully"}


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
):
    """
    Cancel a running job.
    """
    service = get_service()
    job_id_uuid = parse_uuid(job_id)
    job = await service.cancel_job(job_id_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": "Job cancelled", "status": job.status.value}
