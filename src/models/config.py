"""Configuration models using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "SubtitleMaker"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True

    # Server
    server_host: str = "127.0.0.1"
    server_port: int = 8000

    # Security
    secret_key: str = Field(
        default="change-me-in-production",
        min_length=32,
    )
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    # GPU
    gpu_enabled: bool = True
    gpu_device: str = "cuda:0"
    gpu_memory_fraction: float = Field(default=0.85, ge=0.1, le=1.0)

    # Whisper
    whisper_model: Literal[
        "tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3", "large"
    ] = "large-v3"
    whisper_compute_type: Literal["float16", "float32", "int8"] = "float16"
    whisper_batch_size: int = Field(default=8, ge=1, le=32)

    # Upload
    upload_max_file_size_mb: int = Field(default=500, ge=1, le=5000)
    upload_temp_dir: Path = Field(default=Path("./temp"))

    # Cache
    cache_enabled: bool = True
    cache_dir: Path = Field(default=Path("./cache"))
    cache_max_size_gb: int = Field(default=20, ge=1, le=100)

    # Database
    database_url: str = "sqlite+aiosqlite:///./subtitle_maker.db"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: Path = Field(default=Path("./logs/app.log"))

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @field_validator("upload_temp_dir", "cache_dir", "log_file")
    @classmethod
    def create_directory(cls, v: Path) -> Path:
        """Ensure directory exists."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
