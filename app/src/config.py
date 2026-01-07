"""
Configuration management for Newport Demo application.

Uses Pydantic Settings for environment-based configuration.
"""
import logging
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = Field(default="Newport Demo", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")

    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    redis_channels: List[str] = Field(
        default=["detections", "summaries", "pipeline_status"],
        description="Redis channels to subscribe to"
    )

    # WebSocket settings
    ws_heartbeat_interval: int = Field(
        default=30,
        description="WebSocket heartbeat interval in seconds"
    )

    # VLM settings
    vlm_inference_interval: float = Field(
        default=10.0,
        description="Interval between VLM inferences per stream (seconds)"
    )
    vlm_debounce_count: int = Field(
        default=2,
        description="Number of consecutive classifications before status change"
    )

    # Frame settings
    frame_dir: str = Field(
        default="/shared/frames",
        description="Directory for shared frame data"
    )
    frame_jpeg_quality: int = Field(
        default=85,
        description="JPEG quality for saved frames (1-100)"
    )

    # CORS settings
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("frame_jpeg_quality")
    @classmethod
    def validate_jpeg_quality(cls, v: int) -> int:
        """Validate JPEG quality is within valid range."""
        if not 1 <= v <= 100:
            raise ValueError(f"JPEG quality must be between 1 and 100, got {v}")
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


def configure_logging(settings: Optional[Settings] = None) -> None:
    """
    Configure application logging based on settings.

    Args:
        settings: Settings instance (uses get_settings() if not provided)
    """
    if settings is None:
        settings = get_settings()

    log_level = getattr(logging, settings.log_level)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)

    # Reduce noise from some libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {settings.log_level} level")
