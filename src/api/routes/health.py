"""Health check endpoints."""

from fastapi import APIRouter, Depends

from ...models.config import Settings, get_settings
from ...services.transcription_service import TranscriptionService
from ..schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Health check endpoint.

    Returns application status and GPU information.
    """
    gpu_available = False
    gpu_device_name = None

    try:
        import torch

        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_device_name = torch.cuda.get_device_name(0)
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        gpu_available=gpu_available,
        gpu_device_name=gpu_device_name,
    )


@router.get("/health/gpu")
async def gpu_info(
    settings: Settings = Depends(get_settings),
):
    """
    Get detailed GPU information.
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return {
                "available": False,
                "device_name": None,
                "vram_total_mb": 0,
                "vram_used_mb": 0,
                "vram_free_mb": 0,
                "temperature_c": None,
            }

        device = torch.device("cuda:0")
        props = torch.cuda.get_device_properties(device)

        return {
            "available": True,
            "device_name": torch.cuda.get_device_name(0),
            "vram_total_mb": props.total_memory // (1024 * 1024),
            "vram_used_mb": torch.cuda.memory_allocated(device) // (1024 * 1024),
            "vram_free_mb": (props.total_memory - torch.cuda.memory_allocated(device))
            // (1024 * 1024),
            "temperature_c": None,  # Requires nvidia-smi
        }
    except Exception as e:
        return {"error": str(e)}
