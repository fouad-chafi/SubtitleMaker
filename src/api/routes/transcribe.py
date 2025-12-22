"""Transcription endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ...models.job import TranscriptionConfig
from ...models.subtitle import SubtitleFormat
from ...services.transcription_service import TranscriptionService
from ..dependencies import get_transcription_service
from ..schemas import TranscriptionRequest, TranscriptionResponse, UploadResponse

router = APIRouter()


@router.post("/transcribe", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    language: str | None = None,
    task: str = "transcribe",
    vad_filter: bool = True,
    word_timestamps: bool = True,
    subtitle_format: str = "srt",
    num_speakers: int | None = None,
    service: TranscriptionService = Depends(get_transcription_service),
) -> UploadResponse:
    """
    Upload a file and create a transcription job.

    Supported formats: MP4, MOV, AVI, MKV, WEBM, FLV, MP3, WAV, M4A
    """
    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate subtitle format
    try:
        SubtitleFormat(subtitle_format)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid subtitle format. Supported: {', '.join([f.value for f in SubtitleFormat])}",
        )

    # Save uploaded file
    upload_dir = Path(service.settings.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_filename = file.filename
    file_path = upload_dir / safe_filename

    try:
        with file_path.open("wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}") from e

    # Validate file
    try:
        from ...utils.validators import FileValidator

        validation = FileValidator.validate_file(
            file_path,
            max_size_mb=service.settings.upload_max_file_size_mb,
        )
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Create job
    config = TranscriptionConfig(
        language=language,
        task=task,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
        num_speakers=num_speakers,
    )

    job = await service.create_job(file_path, safe_filename, config)
    job.subtitle_format = subtitle_format

    # Start processing in background
    import asyncio

    asyncio.create_task(service.process_job(job.id))

    return UploadResponse(
        job_id=job.id,
        filename=safe_filename,
        file_size_mb=validation["size_mb"],
        status=job.status.value,
        created_at=job.created_at,
    )


@router.get("/transcribe/{job_id}", response_model=TranscriptionResponse)
async def get_transcription_status(
    job_id: uuid.UUID,
    service: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionResponse:
    """
    Get the status of a transcription job.
    """
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return TranscriptionResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        filename=job.filename,
        detected_language=job.detected_language,
        output_path=job.output_path,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        processing_time_seconds=job.processing_time_seconds,
        vram_used_mb=job.vram_used_mb,
    )


@router.get("/transcribe/{job_id}/download")
async def download_subtitle(
    job_id: uuid.UUID,
    service: TranscriptionService = Depends(get_transcription_service),
):
    """
    Download the generated subtitle file.
    """
    from fastapi.responses import FileResponse

    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status.name != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job.output_path:
        raise HTTPException(status_code=400, detail="No output file available")

    output_path = Path(job.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    media_type = {
        "srt": "text/plain",
        "vtt": "text/vtt",
        "ass": "text/x-ssa",
        "txt": "text/plain",
        "json": "application/json",
    }.get(job.subtitle_format, "text/plain")

    filename = f"{Path(job.filename).stem}.{job.subtitle_format}"

    return FileResponse(
        path=str(output_path),
        media_type=media_type,
        filename=filename,
    )
