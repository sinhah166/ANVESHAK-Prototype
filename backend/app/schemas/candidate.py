"""
ANVESHAK — Candidate Schemas
Candidate models for detected astronomical signal candidates.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TransitFeatures(BaseModel):
    """Extracted features for transit-type candidates."""
    period: Optional[float] = Field(None, description="Orbital period in days")
    period_uncertainty: Optional[float] = Field(None, description="Period uncertainty in days")
    depth: Optional[float] = Field(None, description="Transit depth (fractional flux decrease)")
    duration: Optional[float] = Field(None, description="Transit duration in hours")
    transit_time: Optional[float] = Field(None, description="Mid-transit time (BJD)")
    detection_power: Optional[float] = Field(None, description="TLS/BLS detection statistic (SDE/power)")
    snr: Optional[float] = Field(None, description="Signal-to-noise ratio")
    n_transits: Optional[int] = Field(None, description="Number of observed transits")
    odd_even_mismatch: Optional[float] = Field(None, description="Odd/even transit depth ratio")


class RadioFeatures(BaseModel):
    """Extracted features for radio-type candidates."""
    frequency_mhz: Optional[float] = Field(None, description="Center frequency in MHz")
    bandwidth_hz: Optional[float] = Field(None, description="Signal bandwidth in Hz")
    duration_seconds: Optional[float] = Field(None, description="Signal duration in seconds")
    signal_strength: Optional[float] = Field(None, description="Peak signal strength (S/N)")
    integrated_power: Optional[float] = Field(None, description="Integrated signal power")
    drift_rate: Optional[float] = Field(None, description="Frequency drift rate in Hz/s")


class CandidateCreate(BaseModel):
    """Schema for creating a new candidate."""
    observation_id: int = Field(..., description="FK to the parent observation")
    candidate_type: str = Field(..., description="Type of candidate (transit, radio_narrowband, etc.)")
    classification: str = Field(..., description="Classification label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    status: str = Field(default="new", description="Review status")
    model_name: str = Field(..., description="Name of the model/classifier that produced this result")
    transit_features: Optional[TransitFeatures] = None
    radio_features: Optional[RadioFeatures] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CandidateResponse(BaseModel):
    """Candidate response with full details."""
    id: int
    observation_id: int
    candidate_type: str
    classification: str
    confidence: float
    status: str
    model_name: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Joined observation fields for convenience
    source_id: Optional[str] = None
    record_id: Optional[str] = None
    target_name: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    signal_type: Optional[str] = None
    observed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CandidateDetail(CandidateResponse):
    """Full candidate detail including features and chart data."""
    transit_features: Optional[TransitFeatures] = None
    radio_features: Optional[RadioFeatures] = None
    light_curve_data: Optional[dict[str, Any]] = None
    phase_folded_data: Optional[dict[str, Any]] = None
    spectrogram_data: Optional[dict[str, Any]] = None


class CandidateListResponse(BaseModel):
    """Paginated list of candidates."""
    items: list[CandidateResponse]
    total: int
    page: int
    page_size: int


class CandidateEvent(BaseModel):
    """WebSocket event for a new candidate."""
    event: str = "candidate_detected"
    candidate_id: int
    source_id: str
    target_name: str
    classification: str
    confidence: float
    signal_type: str
    timestamp: datetime
    model_name: str
