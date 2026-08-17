"""
ANVESHAK — Source Service
Manages data sources, their configurations, and health statuses.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import get_adapter, list_adapters
from app.core.config import get_settings, load_sources_config
from app.core.logging import get_logger
from app.models.source import Source
from app.schemas.source import SourceConfig, SourceStatus

logger = get_logger("service.source")


class SourceService:
    """Service for managing astronomical data sources."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def initialize_sources(self) -> None:
        """Load sources from config and sync with database."""
        config_sources = load_sources_config()
        
        for source_data in config_sources:
            try:
                # Check if it already exists
                stmt = select(Source).where(Source.source_key == source_data["id"])
                result = await self.db.execute(stmt)
                existing_source = result.scalar_one_or_none()
                
                if existing_source:
                    # Update existing
                    existing_source.name = source_data["name"]
                    existing_source.type = source_data["type"]
                    existing_source.adapter = source_data["adapter"]
                    existing_source.enabled = source_data.get("enabled", True)
                else:
                    # Create new
                    new_source = Source(
                        source_key=source_data["id"],
                        name=source_data["name"],
                        type=source_data["type"],
                        adapter=source_data["adapter"],
                        enabled=source_data.get("enabled", True),
                    )
                    self.db.add(new_source)
                
            except Exception as e:
                logger.error("failed_to_initialize_source", source=source_data.get("id"), error=str(e))
                
        await self.db.commit()
        logger.info("sources_initialized", count=len(config_sources))

    async def get_all_sources(self) -> list[SourceStatus]:
        """Get all configured sources with their current status."""
        stmt = select(Source).order_by(Source.name)
        result = await self.db.execute(stmt)
        sources = result.scalars().all()
        
        return [SourceStatus.model_validate(source) for source in sources]

    async def get_source(self, source_id: str) -> Optional[SourceStatus]:
        """Get a specific source by its ID."""
        stmt = select(Source).where(Source.source_key == source_id)
        result = await self.db.execute(stmt)
        source = result.scalar_one_or_none()
        
        if source:
            return SourceStatus.model_validate(source)
        return None

    async def check_source_health(self, source_id: str) -> dict:
        """Run a health check on a specific source adapter."""
        stmt = select(Source).where(Source.source_key == source_id)
        result = await self.db.execute(stmt)
        source = result.scalar_one_or_none()
        
        if not source:
            return {"healthy": False, "message": f"Source '{source_id}' not found"}
            
        if not source.enabled:
            return {"healthy": False, "message": "Source is disabled"}

        try:
            adapter = get_adapter(source.adapter, source.source_key)
            health_status = await adapter.health_check()
            
            # Update database status
            source.status = "healthy" if health_status.get("healthy") else "unhealthy"
            source.error_message = health_status.get("message")
            source.last_seen = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            return health_status
            
        except Exception as e:
            logger.error("source_health_check_failed", source=source_id, error=str(e))
            
            # Update database with error
            if source:
                source.status = "unhealthy"
                source.error_message = str(e)
                await self.db.commit()
                
            return {"healthy": False, "message": str(e)}

    async def update_observation_count(self, source_id: str, count: int = 1) -> None:
        """Increment the observation count for a source."""
        stmt = select(Source).where(Source.source_key == source_id)
        result = await self.db.execute(stmt)
        source = result.scalar_one_or_none()
        
        if source:
            source.observation_count += count
            source.last_seen = datetime.now(timezone.utc)
            await self.db.commit()
