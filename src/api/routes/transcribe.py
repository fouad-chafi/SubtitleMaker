"""Transcription endpoints."""

import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ...models.job import TranscriptionConfig
from ...models.subtitle import SubtitleFormat
from ...services.transcription_service import TranscriptionService
from ..schemas import (
    BurnInRequest,
    TranscriptionRequest,
    TranscriptionResponse,
    UploadResponse,
)

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


@router.post("/transcribe", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    language: str | None = None,
    task: str = "transcribe",
    vad_filter: str = "True",  # FormData sends strings
    word_timestamps: str = "True",
    subtitle_format: str = "srt",
    num_speakers: int | None = None,
    # Auto burn-in options
    auto_burn_in: str = "False",
    burn_in_style_id: str = "professional",
    burn_in_output_format: str = "mp4",
    burn_in_quality: str = "high",
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
    service = get_service()
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

    # Convert string booleans to actual booleans
    def parse_bool(value: str) -> bool:
        return value.lower() in ("true", "1", "yes", "on")

    # TEMPORARY: Force auto_burn_in to True for testing
    force_auto_burn_in = True

    # Create job
    config = TranscriptionConfig(
        language=language,
        task=task,
        vad_filter=parse_bool(vad_filter),
        word_timestamps=parse_bool(word_timestamps),
        num_speakers=num_speakers,
        auto_burn_in=force_auto_burn_in,  # Forced for testing
        burn_in_style_id=burn_in_style_id,
        burn_in_output_format=burn_in_output_format,
        burn_in_quality=burn_in_quality,
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
    job_id: str,
) -> TranscriptionResponse:
    """
    Get the status of a transcription job.
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


@router.get("/transcribe/{job_id}/download")
async def download_subtitle(
    job_id: str,
):
    """
    Download the generated subtitle file.
    """
    from fastapi.responses import FileResponse

    service = get_service()
    job_id_uuid = parse_uuid(job_id)
    job = await service.get_job(job_id_uuid)
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


@router.get("/transcribe/{job_id}/video")
async def download_video(
    job_id: str,
):
    """
    Download the video with burned-in subtitles.
    """
    from fastapi.responses import FileResponse

    service = get_service()
    job_id_uuid = parse_uuid(job_id)
    job = await service.get_job(job_id_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status.name != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job.video_output_path:
        raise HTTPException(status_code=400, detail="No video file available. Enable auto burn-in to generate video with subtitles.")

    video_path = Path(job.video_output_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Get file extension
    extension = video_path.suffix.lstrip('.')
    media_type = f"video/{extension}"

    filename = f"{Path(job.filename).stem}_subtitled.{extension}"

    return FileResponse(
        path=str(video_path),
        media_type=media_type,
        filename=filename,
    )


@router.post("/transcribe/{job_id}/burn-in")
async def burn_subtitles(
    job_id: str,
    request: BurnInRequest,
):
    """
    Burn subtitles into video (hard-subs).

    Creates a new video with subtitles permanently embedded.
    """
    from fastapi.responses import FileResponse
    from ...models.subtitle import SubtitleStyle
    from ...core.video_processor import VideoProcessor, VideoCodec

    service = get_service()
    job_id_uuid = parse_uuid(job_id)
    job = await service.get_job(job_id_uuid)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status.name != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job.output_path:
        raise HTTPException(status_code=400, detail="No subtitle file available")

    # Get style
    if request.custom_style:
        style = SubtitleStyle(
            name=request.custom_style.name,
            font_family=request.custom_style.font_family,
            font_size=request.custom_style.font_size,
            font_color=request.custom_style.font_color,
            background_color=request.custom_style.background_color,
            background_opacity=request.custom_style.background_opacity,
            outline_color=request.custom_style.outline_color,
            outline_width=request.custom_style.outline_width,
            position=request.custom_style.position,
            alignment=request.custom_style.alignment,
        )
    else:
        # Load style from presets
        import yaml
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "styles.yaml"
        with config_path.open("r") as f:
            styles_config = yaml.safe_load(f)

        style_data = styles_config.get("styles", {}).get(request.style_id, {})
        style = SubtitleStyle(**style_data)

    # Generate output path
    output_dir = Path("./output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_video_path = output_dir / f"{job_id}_burned.{request.output_format}"

    # Determine codec based on quality
    codec_map = {
        "low": VideoCodec.H264,
        "medium": VideoCodec.H264,
        "high": VideoCodec.H265,
    }
    codec = codec_map.get(request.quality, VideoCodec.H264)

    # Burn subtitles
    video_processor = VideoProcessor()
    input_video = Path(job.file_path)

    await asyncio.to_thread(
        video_processor.burn_subtitles,
        input_video,
        job.output_path,
        output_video_path,
        style,
        codec,
    )

    return FileResponse(
        path=str(output_video_path),
        media_type=f"video/{request.output_format}",
        filename=f"{Path(job.filename).stem}_subtitled.{request.output_format}",
    )
 
