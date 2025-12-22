"""API dependencies for dependency injection."""

from typing import AsyncGenerator

from fastapi import Depends

from ..models.config import Settings, get_settings
from ..services.transcription_service import TranscriptionService


async def get_settings_dep() -> Settings:
    """Get application settings."""
    return get_settings()


async def get_transcription_service(
    settings: Settings = Depends(get_settings_dep),
) -> AsyncGenerator[TranscriptionService, None]:
    """
    Get transcription service instance.

    Yields:
        TranscriptionService instance
    """
    service = TranscriptionService(settings)
    try:
        yield service
    finally:
        # Cleanup if needed
        pass
