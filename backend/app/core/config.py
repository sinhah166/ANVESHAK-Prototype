"""
ANVESHAK — Application Configuration
Loads settings from environment variables and YAML config files.
"""

import os
from pathlib import Path
from typing import Optional

import yaml
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

    # ── Data Mode ──
    data_mode: str = "demo"

    # ── Logging ──
    log_level: str = "INFO"

    # ── ML ──
    ml_model_dir: str = "ml_models"

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


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def load_sources_config(config_path: Optional[str] = None) -> list[dict]:
    """
    Load source configuration from YAML file.

    Args:
        config_path: Path to sources.yaml. Defaults to config/sources.yaml.

    Returns:
        List of source configuration dictionaries.
    """
    if config_path is None:
        # Try multiple locations
        candidates = [
            Path("config/sources.yaml"),
            Path("/app/config/sources.yaml"),
            Path(__file__).parent.parent.parent.parent / "config" / "sources.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                config_path = str(candidate)
                break

    if config_path is None or not Path(config_path).exists():
        # Return default demo config if file not found
        return [
            {
                "id": "synthetic",
                "name": "Synthetic Demo",
                "type": "lightcurve",
                "adapter": "synthetic",
                "enabled": True,
            },
            {
                "id": "radio_demo",
                "name": "Radio Demo",
                "type": "radio",
                "adapter": "radio_demo",
                "enabled": True,
            },
        ]

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config.get("sources", [])


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEMO_DATA_DIR = DATA_DIR / "demo"
ML_MODELS_DIR = PROJECT_ROOT / "ml_models"
