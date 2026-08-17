"""
ANVESHAK — Source Schemas
Source configuration and status models.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    """Source configuration as loaded from sources.yaml."""
    id: str = Field(..., description="Unique source identifier")
    name: str = Field(..., description="Display name")
    type: str = Field(..., description="Source type (lightcurve, radio)")
    adapter: str = Field(..., description="Adapter class to use")
    enabled: bool = Field(default=True, description="Whether this source is active")


class SourceStatus(BaseModel):
    """Source with runtime status information."""
    id: str
    name: str
    type: str
    adapter: str
    enabled: bool
    health: str = "unknown"
    last_seen: Optional[datetime] = None
    observation_count: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SourceListResponse(BaseModel):
    """List of all configured sources."""
    sources: list[SourceStatus]


class StatsResponse(BaseModel):
    """Aggregated pipeline statistics."""
    total_observations: int = 0
    total_candidates: int = 0
    high_confidence_candidates: int = 0
    active_sources: int = 0
    classification_distribution: dict[str, int] = Field(default_factory=dict)
    signal_type_distribution: dict[str, int] = Field(default_factory=dict)
    source_distribution: dict[str, int] = Field(default_factory=dict)
    recent_activity: list[dict] = Field(default_factory=list)


class PipelineStageStatus(BaseModel):
    """Status of a single pipeline stage."""
    stage: str
    status: str = "idle"
    last_run: Optional[datetime] = None
    processed_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    """Full pipeline status across all stages."""
    stages: list[PipelineStageStatus]
    is_running: bool = False
    current_mode: str = "demo"


class SystemStatusResponse(BaseModel):
    """System health dashboard data."""
    backend: str = "healthy"
    postgres: str = "unknown"
    redis: str = "unknown"
    websocket_connections: int = 0
    data_mode: str = "demo"
    version: str = "1.0.0-mvp"
    uptime_seconds: float = 0
