"""Validation utilities for file uploads and inputs."""

from pathlib import Path
from typing import Optional

from pydantic import ValidationError


class ValidationError(Exception):
    """Custom validation error."""

    pass


class FileValidator:
    """Validate uploaded files for transcription."""

    # Allowed extensions
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}
    AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
    ALL_ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

    @classmethod
    def validate_file(
        cls,
        file_path: str | Path,
        max_size_mb: int = 500,
        allowed_extensions: Optional[set[str]] = None,
    ) -> dict:
        """
        Validate a file for transcription.

        Args:
            file_path: Path to file
            max_size_mb: Maximum file size in MB
            allowed_extensions: Set of allowed extensions (with dot)

        Returns:
            Dictionary with validation results

        Raises:
            ValidationError: If validation fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValidationError(f"File does not exist: {file_path}")

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValidationError(
                f"File size ({file_size_mb:.1f}MB) exceeds maximum ({max_size_mb}MB)"
            )

        # Check extension
        ext = file_path.suffix.lower()
        if ext not in cls.ALL_ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File extension '{ext}' not supported. "
                f"Supported: {', '.join(sorted(cls.ALL_ALLOWED_EXTENSIONS))}"
            )

        if allowed_extensions and ext not in allowed_extensions:
            raise ValidationError(
                f"File extension '{ext}' not allowed. "
                f"Allowed: {', '.join(allowed_extensions)}"
            )

        is_video = ext in cls.VIDEO_EXTENSIONS

        # Try to detect MIME type (optional, may not work on all systems)
        mime_type = "video/*" if is_video else "audio/*"
        try:
            import magic
            mime = magic.from_file(str(file_path), mime=True)
            mime_type = mime
        except Exception:
            # Fallback to extension-based detection
            pass

        return {
            "valid": True,
            "mime_type": mime_type,
            "extension": ext,
            "size_mb": file_size_mb,
            "is_video": is_video,
        }

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize a filename for safe storage.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove any path components
        filename = Path(filename).name

        # Replace dangerous characters
        dangerous_chars = ['..', '/', '\\', '\x00']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit length
        name, ext = Path(filename).stem, Path(filename).suffix
        name = name[:200]  # Limit name length

        return f"{name}{ext}"


class SubtitleValidator:
    """Validate subtitle data and formats."""

    @staticmethod
    def validate_timestamp(start: float, end: float) -> bool:
        """
        Validate timestamp values.

        Args:
            start: Start time in seconds
            end: End time in seconds

        Returns:
            True if valid
        """
        return start >= 0 and end > start

    @staticmethod
    def validate_text(text: str, min_length: int = 1) -> bool:
        """
        Validate subtitle text.

        Args:
            text: Subtitle text
            min_length: Minimum text length

        Returns:
            True if valid
        """
        stripped = text.strip()
        return len(stripped) >= min_length

    @classmethod
    def validate_segment_count(cls, count: int, max_count: int = 10000) -> bool:
        """
        Validate number of segments.

        Args:
            count: Number of segments
            max_count: Maximum allowed segments

        Returns:
            True if valid
        """
        return 0 < count <= max_count


class ConfigValidator:
    """Validate configuration values."""

    @staticmethod
    def validate_whisper_model(model: str) -> bool:
        """Validate Whisper model name."""
        valid_models = {
            "tiny",
            "base",
            "small",
            "medium",
            "large-v1",
            "large-v2",
            "large-v3",
            "large",
        }
        return model in valid_models

    @staticmethod
    def validate_language_code(code: Optional[str]) -> bool:
        """
        Validate ISO 639-1 language code.

        Args:
            code: Language code (e.g., "en", "fr", "es")

        Returns:
            True if valid or None (for auto-detect)
        """
        if code is None:
            return True  # Auto-detect
        # Basic validation for ISO 639-1 codes
        return len(code) == 2 and code.isalpha()

    @staticmethod
    def validate_compute_type(compute_type: str) -> bool:
        """Validate Whisper compute type."""
        return compute_type in {"float16", "float32", "int8"}
