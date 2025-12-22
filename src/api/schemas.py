"""API request and response schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    gpu_available: bool
    gpu_device_name: Optional[str] = None


class UploadResponse(BaseModel):
    """Response for file upload."""

    job_id: UUID
    filename: str
    file_size_mb: float
    status: str
    created_at: datetime


class TranscriptionRequest(BaseModel):
    """Request to start transcription."""

    language: Optional[str] = Field(
        default=None, description="ISO 639-1 language code (auto-detect if null)"
    )
    task: str = Field(default="transcribe", description="transcribe or translate")
    vad_filter: bool = Field(default=True, description="Use VAD filter")
    word_timestamps: bool = Field(default=True, description="Include word timestamps")
    subtitle_format: str = Field(default="srt", description="Output format")
    num_speakers: Optional[int] = Field(default=None, ge=1, le=10)


class TranscriptionResponse(BaseModel):
    """Response for transcription status."""

    job_id: UUID
    status: str
    progress: float
    filename: str
    detected_language: Optional[str] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    vram_used_mb: Optional[int] = None


class JobListResponse(BaseModel):
    """Response for job list."""

    jobs: list[TranscriptionResponse]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None


class SupportedLanguagesResponse(BaseModel):
    """Response for supported languages."""

    languages: dict[str, str]


class SubtitleStyleRequest(BaseModel):
    """Request for subtitle style."""

    name: str
    font_family: str = "Arial"
    font_size: int = Field(default=24, ge=10, le=72)
    font_color: str = "#FFFFFF"
    background_color: str = "#000000"
    background_opacity: float = Field(default=0.0, ge=0.0, le=1.0)
    outline_color: str = "#000000"
    outline_width: int = Field(default=2, ge=0, le=5)
    position: str = "bottom"
    alignment: str = "center"


class SubtitleStyleResponse(BaseModel):
    """Response for subtitle style."""

    styles: list[dict]


class GPUInfoResponse(BaseModel):
    """Response for GPU information."""

    available: bool
    device_name: Optional[str] = None
    vram_total_mb: int
    vram_used_mb: int
    vram_free_mb: int
    temperature_c: Optional[float] = None
