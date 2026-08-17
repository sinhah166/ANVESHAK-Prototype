"""
ANVESHAK — Base Adapter & Adapter Registry
Defines the adapter interface and factory for extensible data source integration.

To add a new telescope/instrument:
1. Create a new adapter file implementing BaseAdapter
2. Register it in ADAPTER_REGISTRY
3. Add configuration to config/sources.yaml
4. Restart the application
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.logging import get_logger
from app.schemas.observation import ObservationCreate

logger = get_logger("adapter.base")


class BaseAdapter(ABC):
    """
    Abstract base adapter for astronomical data sources.

    Every data source (telescope, instrument, synthetic generator) must
    implement this interface to integrate with the ANVESHAK pipeline.
    """

    def __init__(self, source_id: str, config: dict[str, Any] | None = None):
        """
        Initialize the adapter.

        Args:
            source_id: Unique source identifier.
            config: Optional configuration dictionary.
        """
        self.source_id = source_id
        self.config = config or {}
        self.logger = get_logger(f"adapter.{source_id}")

    @abstractmethod
    async def fetch_new(self, **kwargs) -> list[dict[str, Any]]:
        """
        Fetch new raw data from the source.

        Returns:
            List of raw data dictionaries in source-specific format.
        """
        ...

    @abstractmethod
    async def normalize(self, raw_data: dict[str, Any]) -> ObservationCreate:
        """
        Normalize a single raw data record into the common schema.

        Args:
            raw_data: Source-specific raw data dictionary.

        Returns:
            Normalized ObservationCreate instance.
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Check the health of this data source.

        Returns:
            Dict with at least 'healthy' (bool) and 'message' (str).
        """
        ...

    async def fetch_and_normalize(self, **kwargs) -> list[ObservationCreate]:
        """
        Fetch new data and normalize all records.

        This is the primary method called by the pipeline.
        Errors in individual record normalization are isolated.
        """
        try:
            raw_records = await self.fetch_new(**kwargs)
            self.logger.info("fetched_records", count=len(raw_records))
        except Exception as e:
            self.logger.error("fetch_failed", error=str(e))
            return []

        observations = []
        for raw in raw_records:
            try:
                obs = await self.normalize(raw)
                observations.append(obs)
            except Exception as e:
                self.logger.warning(
                    "normalization_failed",
                    record=str(raw)[:200],
                    error=str(e),
                )
                continue

        self.logger.info("normalized_records", count=len(observations))
        return observations


# ── Adapter Registry ──

ADAPTER_REGISTRY: dict[str, type[BaseAdapter]] = {}


def register_adapter(name: str):
    """
    Decorator to register an adapter class.

    Usage:
        @register_adapter("tess")
        class TessAdapter(BaseAdapter):
            ...
    """
    def decorator(cls: type[BaseAdapter]):
        ADAPTER_REGISTRY[name] = cls
        return cls
    return decorator


def get_adapter(name: str, source_id: str, config: dict | None = None) -> BaseAdapter:
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
