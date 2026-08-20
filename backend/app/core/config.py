"""
ANVESHAK — Application Configuration
Loads settings from environment variables.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── PostgreSQL ──
    postgres_user: str = "anveshak"
    postgres_password: str = "anveshak_dev_2024"
    postgres_db: str = "anveshak"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # ── Redis ──
    redis_host: str = "localhost"
    redis_port: int = 6379

    # ── API ──
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── NASA TAP ──
    nasa_tap_url: str = "https://exoplanetarchive.ipac.caltech.edu/TAP"

    # ── Data Mode ──
    data_mode: str = "demo"  # "demo" or "live"

    # ── App ──
    app_env: str = "development"  # "development", "production"
    log_level: str = "INFO"

    # ── ML ──
    model_storage_path: str = "ml/artifacts"

    @property
    def database_url(self) -> str:
        """Async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync PostgreSQL connection URL (for migrations/scripts)."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parsed list of CORS origins."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# ── Project Paths ──
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # anveshak/
BACKEND_ROOT = Path(__file__).parent.parent.parent  # anveshak/backend/
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLES_DIR = DATA_DIR / "samples"
ML_ARTIFACTS_DIR = PROJECT_ROOT / "ml" / "artifacts"

# Ensure directories exist
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, SAMPLES_DIR, ML_ARTIFACTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
