"""Transcription service orchestrating the workflow."""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.subtitle_formatter import SubtitleFormatter
from ..core.transcriber import WhisperTranscriber
from ..core.video_processor import VideoProcessor
from ..models.config import Settings
from ..models.job import JobStatus, TranscriptionConfig, TranscriptionJob
from ..models.subtitle import SubtitleFormat, SubtitleTrack
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TranscriptionService:
    """Service for managing transcription jobs."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.transcriber = WhisperTranscriber(settings)
        self.video_processor = VideoProcessor()
        self.formatter = SubtitleFormatter()

        # Job storage (in-memory, replace with database in production)
        self._jobs: dict[uuid.UUID, TranscriptionJob] = {}
        self._lock = asyncio.Lock()

    async def create_job(
        self,
        file_path: str | Path,
        filename: str,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionJob:
        """
        Create a new transcription job.

        Args:
            file_path: Path to input file
            filename: Original filename
            config: Transcription configuration

        Returns:
            Created job
        """
        file_path = Path(file_path)
        file_size = file_path.stat().st_size

        job = TranscriptionJob(
            filename=filename,
            file_path=str(file_path),
            file_size_bytes=file_size,
            config=config or TranscriptionConfig(),
        )

        # Get video duration
        try:
            duration = self.video_processor.get_video_duration(file_path)
            job.duration_seconds = duration
        except Exception as e:
            logger.warning(f"Could not get video duration: {e}")

        async with self._lock:
            self._jobs[job.id] = job

        logger.info(f"Created job {job.id} for {filename}")
        return job

    async def get_job(self, job_id: uuid.UUID) -> Optional[TranscriptionJob]:
        """Get a job by ID."""
        async with self._lock:
            return self._jobs.get(job_id)

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TranscriptionJob]:
        """
        List jobs with optional filtering.

        Args:
            status: Filter by status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of jobs
        """
        async with self._lock:
            jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by created time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return jobs[offset : offset + limit]

    async def process_job(self, job_id: uuid.UUID) -> TranscriptionJob:
        """
        Process a transcription job.

        Args:
            job_id: Job ID to process

        Returns:
            Updated job

        Raises:
            ValueError: If job not found
            RuntimeError: If processing fails
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise ValueError(f"Job not found: {job_id}")

        job.started_at = datetime.utcnow()
        job.status = JobStatus.PROCESSING
        job.progress = 0.0

        try:
            # Step 1: Extract audio if video
            job.progress = 10.0
            logger.info(f"Processing job {job_id}: extracting audio")

            input_path = Path(job.file_path)
            audio_path = input_path

            # Check if video file
            video_info = self.video_processor.get_video_info(input_path)
            is_video = video_info.get("codec") != "unknown"

            if is_video:
                temp_audio_path = self.settings.upload_temp_dir / f"{job_id}.wav"
                audio_path = self.video_processor.extract_audio(
                    input_path,
                    temp_audio_path,
                )

            # Step 2: Transcribe
            job.progress = 30.0
            logger.info(f"Processing job {job_id}: transcribing")

            result = await asyncio.to_thread(
                self.transcriber.transcribe,
                audio_path,
                job.config,
                job,
            )

            job.detected_language = result.detected_language
            job.progress = 80.0

            # Step 3: Format and save
            logger.info(f"Processing job {job_id}: formatting")
            output_dir = Path("./output")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / f"{job_id}.{job.subtitle_format}"

            self.formatter.format(
                result.track,
                SubtitleFormat(job.subtitle_format),
                output_path,
            )

            job.output_path = str(output_path)
            job.vram_used_mb = result.vram_used_mb
            job.processing_time_seconds = result.processing_time
            job.progress = 100.0
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()

            logger.info(f"Job {job_id} completed successfully")

            # Clean up temporary audio
            if audio_path != input_path and audio_path.exists():
                audio_path.unlink()

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

            # Clean up temporary audio
            if audio_path != input_path and audio_path.exists():
                try:
                    audio_path.unlink()
                except Exception:
                    pass

            raise RuntimeError(f"Transcription failed: {e}") from e

        return job

    async def cancel_job(self, job_id: uuid.UUID) -> Optional[TranscriptionJob]:
        """
        Cancel a job.

        Args:
            job_id: Job ID to cancel

        Returns:
            Cancelled job or None if not found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            if job.status in {JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING}:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow()
                logger.info(f"Job {job_id} cancelled")

        return job

    async def delete_job(self, job_id: uuid.UUID) -> bool:
        """
        Delete a job and its files.

        Args:
            job_id: Job ID to delete

        Returns:
            True if deleted
        """
        async with self._lock:
            job = self._jobs.pop(job_id, None)
            if not job:
                return False

        # Delete output file
        if job.output_path:
            output_path = Path(job.output_path)
            if output_path.exists():
                output_path.unlink()

        logger.info(f"Job {job_id} deleted")
        return True

    async def get_job_status(self, job_id: uuid.UUID) -> Optional[dict]:
        """
        Get job status information.

        Args:
            job_id: Job ID

        Returns:
            Dictionary with status info or None
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        return {
            "id": str(job.id),
            "status": job.status.value,
            "progress": job.progress,
            "filename": job.filename,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "detected_language": job.detected_language,
            "output_path": job.output_path,
            "error_message": job.error_message,
            "vram_used_mb": job.vram_used_mb,
            "processing_time_seconds": job.processing_time_seconds,
        }
