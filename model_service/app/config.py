"""
Application Configuration Module.

Loads and validates settings from environment variables using Pydantic Settings.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Metadata
    app_name: str = Field(default="ml-inference-platform", description="Application name")
    app_env: str = Field(default="production", description="Environment: dev, staging, production")
    app_version: str = Field(default="v1.0.0", description="Application semantic version")
    model_version: str = Field(default="v1.0.0", description="Active ML model version")

    # Model Configuration
    model_path: str = Field(
        default="model_service/model/model.joblib",
        description="Path to serialized joblib model artifact",
    )
    expected_features_count: int = Field(
        default=4,
        description="Expected number of input numerical features",
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host bind address")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    graceful_timeout: int = Field(default=30, description="Graceful shutdown timeout in seconds")

    # Logging & Observability
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARN, ERROR)")
    log_format: str = Field(default="json", description="Log format (json or text)")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics endpoint")

    # Security & CORS
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origin domains",
    )
    allowed_hosts: list[str] = Field(
        default=["*"],
        description="Allowed HTTP host headers",
    )


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached singleton application settings instance."""
    return Settings()
