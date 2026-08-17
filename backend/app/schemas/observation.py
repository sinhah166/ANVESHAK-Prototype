"""
ANVESHAK — Observation Schemas
The common observation schema is the central contract of the architecture.
Every adapter normalizes its output into these models.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class TargetInfo(BaseModel):
    """Sky target information."""
    name: str = Field(..., description="Target designation (e.g., 'TIC 123456')")
    ra: float = Field(..., ge=0, le=360, description="Right ascension in degrees")
    dec: float = Field(..., ge=-90, le=90, description="Declination in degrees")


class ObservationCreate(BaseModel):
    """
    Common observation schema — the central contract.

    Every adapter MUST normalize its output into this model.
    Source-specific scientific information goes in `metadata`.
    """
    source_id: str = Field(..., description="Source identifier (e.g., 'tess', 'radio_demo')")
    record_id: str = Field(..., description="Source-specific unique record ID for deduplication")
    observed_at: datetime = Field(..., description="Timestamp of the observation")
    target: TargetInfo = Field(..., description="Sky target information")
    signal_type: str = Field(..., description="Type of signal (transit, radio_narrowband, etc.)")
    raw_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Untouched original data reference, kept for traceability"
    )
    preliminary_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Preliminary confidence score from adapter, if available"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific scientific metadata (period, frequency, etc.)"
    )

    @field_validator("signal_type")
    @classmethod
    def validate_signal_type(cls, v: str) -> str:
        """Ensure signal_type is lowercase and non-empty."""
        return v.lower().strip()


class ObservationResponse(ObservationCreate):
    """Observation response with database-generated fields."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ObservationListResponse(BaseModel):
    """Paginated list of observations."""
    items: list[ObservationResponse]
    total: int
    page: int
    page_size: int


class ObservationDetail(ObservationResponse):
    """Full observation detail including raw data for visualization."""
    light_curve_data: Optional[dict[str, Any]] = Field(
        None,
        description="Light curve time/flux arrays for charting"
    )
    spectrogram_data: Optional[dict[str, Any]] = Field(
        None,
        description="Spectrogram data for charting"
    )
