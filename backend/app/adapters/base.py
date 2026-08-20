"""
ANVESHAK — Base Data Adapter & Adapter Registry
Defines the adapter interface for extensible astronomical data source integration.

To add a new data source:
1. Create a new adapter file implementing BaseDataAdapter
2. Register it using @register_adapter("name")
3. The adapter will be automatically available in the ingestion pipeline
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import pandas as pd

from app.core.logging import get_logger

logger = get_logger("adapter.base")


class BaseDataAdapter(ABC):
    """
    Abstract base adapter for astronomical data sources.

    Every data source must implement this interface to integrate
    with the ANVESHAK ingestion and analysis pipeline.
    """

    def __init__(self, source_id: str, config: dict[str, Any] | None = None):
        self.source_id = source_id
        self.config = config or {}
        self.logger = get_logger(f"adapter.{source_id}")

    @abstractmethod
    async def fetch_schema(self, table: str) -> pd.DataFrame:
        """Inspect the table schema/metadata."""
        ...

    @abstractmethod
    async def fetch_data(
        self,
        table: str,
        max_records: int = 2000,
        where: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch raw data from the source."""
        ...

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Validate a DataFrame.
        Returns validation report with issues found.
        """
        ...

    @abstractmethod
    def normalize(self, df: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
        """
        Normalize column names from source schema to internal schema.
        """
        ...

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """Return source metadata (name, type, URL, etc.)."""
        ...

    async def health_check(self) -> dict[str, Any]:
        """Check if the data source is reachable."""
        return {"healthy": True, "source_id": self.source_id}


# ── Adapter Registry ──
ADAPTER_REGISTRY: dict[str, type[BaseDataAdapter]] = {}


def register_adapter(name: str):
    """
    Decorator to register an adapter class.

    Usage:
        @register_adapter("nasa_exoplanet_archive")
        class NASAExoplanetArchiveAdapter(BaseDataAdapter):
            ...
    """
    def decorator(cls: type[BaseDataAdapter]):
        ADAPTER_REGISTRY[name] = cls
        return cls
    return decorator


def get_adapter(name: str, source_id: str, config: dict | None = None) -> BaseDataAdapter:
    """
    Factory method to create an adapter instance.

    Args:
        name: Adapter name as registered.
        source_id: Source identifier.
        config: Optional configuration.

    Returns:
        Initialized adapter instance.

    Raises:
        ValueError: If adapter name is not registered.
    """
    if name not in ADAPTER_REGISTRY:
        raise ValueError(
            f"Unknown adapter '{name}'. Available: {list(ADAPTER_REGISTRY.keys())}"
        )
    return ADAPTER_REGISTRY[name](source_id=source_id, config=config)


def list_adapters() -> list[str]:
    """Return list of registered adapter names."""
    return list(ADAPTER_REGISTRY.keys())
