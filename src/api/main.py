"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..models.config import Settings, get_settings
from .routes import health, jobs, transcribe, styles
from ..utils.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()

    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        log_format="json" if settings.is_production else "text",
    )

    # Load Whisper model on startup
    from ..services.transcription_service import TranscriptionService

    service = TranscriptionService(settings)
    try:
        service.transcriber.load_model()
    except Exception as e:
        print(f"Warning: Could not load Whisper model: {e}")

    yield

    # Cleanup
    service.transcriber.unload_model()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered subtitle generator optimized for RTX 4070 Super",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(transcribe.router, prefix="/api/v1", tags=["transcription"])
    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
    app.include_router(styles.router, prefix="/api/v1", tags=["styles"])

    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return JSONResponse(
            status_code=400,
            content={"error": "Bad Request", "detail": str(exc)},
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "detail": str(exc)},
        )

    return app


app = create_app()
