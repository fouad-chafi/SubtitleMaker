"""Job models for transcription tasks."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of a transcription job."""

    PENDING = "pending"
    UPLOADING = "uploading"
    QUEUED = "queued"
    PROCESSING = "processing"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    """Priority level for jobs."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TranscriptionConfig(BaseModel):
    """Configuration for a transcription job."""

    language: Optional[str] = Field(
        default=None, description="Language code (auto-detect if null)"
    )
    task: str = Field(default="transcribe", description="Task: transcribe or translate")
    vad_filter: bool = Field(default=True, description="Use VAD filter")
    word_timestamps: bool = Field(default=True, description="Include word-level timestamps")
    num_speakers: Optional[int] = Field(
        default=None, ge=1, le=10, description="Number of speakers for diarization"
    )

    # Auto burn-in options
    auto_burn_in: bool = Field(default=False, description="Automatically burn subtitles into video")
    burn_in_style_id: str = Field(default="professional", description="Style preset for burn-in")
    burn_in_output_format: str = Field(default="mp4", description="Output video format: mp4, mkv, webm")
    burn_in_quality: str = Field(default="high", description="Quality: low, medium, high")


class TranscriptionJob(BaseModel):
    """A transcription job representation."""

    id: UUID = Field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    progress: float = Field(default=0.0, ge=0.0, le=100.0)

    # Input
    filename: str
    file_path: str
    file_size_bytes: int
    duration_seconds: Optional[float] = None

    # Configuration
    config: TranscriptionConfig = Field(default_factory=TranscriptionConfig)

    # Output
    subtitle_format: str = "srt"
    output_path: Optional[str] = None
    video_output_path: Optional[str] = None  # Path to video with burned-in subtitles
    detected_language: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # GPU metrics
    vram_used_mb: Optional[int] = None
    processing_time_seconds: Optional[float] = None

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)

    @property
    def elapsed_time_seconds(self) -> Optional[float]:
        """Get elapsed processing time in seconds."""
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            return (end_time - self.started_at).total_seconds()
        return None

    @property
    def real_time_factor(self) -> Optional[float]:
        """Get real-time factor (processing time / audio duration)."""
        if self.processing_time_seconds and self.duration_seconds:
            return self.processing_time_seconds / self.duration_seconds
        return None


class JobUpdate(BaseModel):
    """Update for a job's progress."""

    job_id: UUID
    status: Optional[JobStatus] = None
    progress: Optional[float] = None
    error_message: Optional[str] = None
    vram_used_mb: Optional[int] = None


class JobListResponse(BaseModel):
    """Response for job list endpoint."""

    jobs: list[TranscriptionJob]
    total: int
    page: int
    page_size: int
