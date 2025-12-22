"""Core Whisper transcription engine with GPU optimization."""

import gc
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
import torch.cuda as cuda
from faster_whisper import WhisperModel

from ..models.config import Settings
from ..models.job import JobStatus, TranscriptionConfig, TranscriptionJob
from ..models.subtitle import SubtitleSegment, SubtitleTrack

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""

    track: SubtitleTrack
    detected_language: str
    processing_time: float
    vram_used_mb: Optional[int] = None


class GPUMemoryManager:
    """Manages GPU memory allocation and monitoring."""

    def __init__(self, device: str = "cuda:0", memory_fraction: float = 0.85):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.memory_fraction = memory_fraction
        self._initial_memory_allocated = 0

        if self.is_cuda_available:
            self._setup_memory()

    @property
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available."""
        return torch.cuda.is_available()

    @property
    def device_name(self) -> str:
        """Get the device name."""
        if self.is_cuda_available:
            return torch.cuda.get_device_name(self.device)
        return "CPU"

    @property
    def vram_total_mb(self) -> int:
        """Get total VRAM in MB."""
        if self.is_cuda_available:
            return torch.cuda.get_device_properties(self.device).total_memory // (1024 * 1024)
        return 0

    @property
    def vram_used_mb(self) -> int:
        """Get used VRAM in MB."""
        if self.is_cuda_available:
            return torch.cuda.memory_allocated(self.device) // (1024 * 1024)
        return 0

    @property
    def vram_free_mb(self) -> int:
        """Get free VRAM in MB."""
        if self.is_cuda_available:
            props = torch.cuda.get_device_properties(self.device)
            allocated = torch.cuda.memory_allocated(self.device)
            return (props.total_memory - allocated) // (1024 * 1024)
        return 0

    def _setup_memory(self) -> None:
        """Configure GPU memory settings."""
        try:
            # Set memory fraction
            target_memory = int(self.vram_total_mb * self.memory_fraction)
            self._initial_memory_allocated = target_memory * 1024 * 1024

            # Enable memory growth (if supported)
            if hasattr(torch.cuda, 'memory.set_per_process_memory_fraction'):
                torch.cuda.memory.set_per_process_memory_fraction(self.memory_fraction)

            logger.info(
                f"GPU configured: {self.device_name}, "
                f"VRAM: {self.vram_total_mb}MB total, "
                f"{target_memory}MB allocated"
            )
        except Exception as e:
            logger.warning(f"Could not configure GPU memory: {e}")

    def cleanup(self) -> None:
        """Clean up GPU memory."""
        if self.is_cuda_available:
            gc.collect()
            torch.cuda.empty_cache()
            logger.debug("GPU memory cleaned up")

    def get_temperature(self) -> Optional[float]:
        """Get GPU temperature in Celsius (if nvidia-smi available)."""
        if not self.is_cuda_available:
            return None
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        return None


class WhisperTranscriber:
    """Whisper-based transcription engine with GPU optimization."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model: Optional[WhisperModel] = None
        self.gpu_manager = GPUMemoryManager(
            device=settings.gpu_device,
            memory_fraction=settings.gpu_memory_fraction
        )

    def load_model(self) -> None:
        """Load the Whisper model."""
        if self.model is not None:
            return

        model_size = self.settings.whisper_model
        compute_type = self.settings.whisper_compute_type

        # Determine device and compute type
        if self.gpu_manager.is_cuda_available:
            device = "cuda"
            # Use float16 if supported, otherwise float32
            if compute_type == "float16" and not torch.cuda.is_bf16_supported():
                compute_type = "float16"
            logger.info(f"Loading Whisper model '{model_size}' on CUDA with {compute_type}")
        else:
            device = "cpu"
            compute_type = "int8"  # Use int8 on CPU for efficiency
            logger.info(f"Loading Whisper model '{model_size}' on CPU with {compute_type}")

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root="./models",
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def unload_model(self) -> None:
        """Unload the model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self.gpu_manager.cleanup()
            logger.info("Whisper model unloaded from memory")

    def transcribe(
        self,
        audio_path: str | Path,
        config: TranscriptionConfig,
        job: TranscriptionJob,
    ) -> TranscriptionResult:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_path: Path to audio file
            config: Transcription configuration
            job: Job to update with progress

        Returns:
            TranscriptionResult with subtitle track and metadata

        Raises:
            RuntimeError: If transcription fails
        """
        if self.model is None:
            self.load_model()

        import time
        start_time = time.time()

        try:
            job.status = JobStatus.PROCESSING
            job.started_at = None  # Will be set by job manager

            # Prepare transcription parameters
            params = {
                "language": config.language if config.language else None,
                "task": config.task,
                "vad_filter": config.vad_filter,
                "word_timestamps": config.word_timestamps,
                "beam_size": 5,
                "best_of": 5,
            }

            logger.info(f"Starting transcription: {audio_path}")

            # Run transcription
            segments_iter, info = self.model.transcribe(
                str(audio_path),
                **params
            )

            # Collect segments
            segments_data = []
            for segment in segments_iter:
                segments_data.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "avg_logprob": getattr(segment, "avg_logprob", None),
                })

            # Create subtitle track
            track = SubtitleTrack(language=info.language)

            for idx, seg_data in enumerate(segments_data, start=1):
                segment = SubtitleSegment(
                    index=idx,
                    start_time=seg_data["start"],
                    end_time=seg_data["end"],
                    text=seg_data["text"],
                    confidence=1.0 + (seg_data.get("avg_logprob") or -2.0) / 4,
                )
                track.add_segment(segment)

            processing_time = time.time() - start_time
            vram_used = self.gpu_manager.vram_used_mb

            logger.info(
                f"Transcription completed: {track.segment_count} segments, "
                f"{info.language} detected, {processing_time:.2f}s"
            )

            return TranscriptionResult(
                track=track,
                detected_language=info.language,
                processing_time=processing_time,
                vram_used_mb=vram_used,
            )

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}") from e

    def detect_language(self, audio_path: str | Path) -> tuple[str, float]:
        """
        Detect language from audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (language_code, confidence)
        """
        if self.model is None:
            self.load_model()

        # Load audio and detect language
        segments, info = self.model.transcribe(
            str(audio_path),
            language=None,
            vad_filter=False,
            max_length=1,  # Only process first second
        )
        # Consume the generator to trigger detection
        list(segments)

        return info.language, info.language_probability

    @staticmethod
    def extract_audio_from_video(video_path: str | Path, output_path: str | Path) -> Path:
        """
        Extract audio from video file using FFmpeg.

        Args:
            video_path: Path to video file
            output_path: Output path for audio

        Returns:
            Path to extracted audio file
        """
        import subprocess

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # PCM 16-bit
            "-ar", "16000",  # 16kHz sample rate (Whisper's native)
            "-ac", "1",  # Mono
            "-y",  # Overwrite
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5 minute timeout
            )
            logger.info(f"Audio extracted: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio: {e}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio extraction timed out") from None
