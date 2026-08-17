"""
ANVESHAK — Candidate Database Models
Includes Candidate, TransitFeature, and RadioFeature tables.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.models.database import Base


class Candidate(Base):
    """Candidate table — detected astronomical signal candidates."""

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    observation_id = Column(
        Integer, ForeignKey("observations.id", ondelete="CASCADE"), nullable=False
    )
    candidate_type = Column(String(64), nullable=False)
    classification = Column(String(64), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, default="new")
    model_name = Column(String(128), nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    transit_features = relationship(
        "TransitFeature", back_populates="candidate", uselist=False, cascade="all, delete-orphan"
    )
    radio_features = relationship(
        "RadioFeature", back_populates="candidate", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_candidates_confidence", "confidence"),
        Index("ix_candidates_classification", "classification"),
        Index("ix_candidates_observation", "observation_id"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "observation_id": self.observation_id,
            "candidate_type": self.candidate_type,
            "classification": self.classification,
            "confidence": self.confidence,
            "status": self.status,
            "model_name": self.model_name,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TransitFeature(Base):
    """Transit-specific features extracted during detection."""

    __tablename__ = "transit_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(
        Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    period = Column(Float, nullable=True)
    period_uncertainty = Column(Float, nullable=True)
    depth = Column(Float, nullable=True)
    duration = Column(Float, nullable=True)
    transit_time = Column(Float, nullable=True)
    detection_power = Column(Float, nullable=True)
    snr = Column(Float, nullable=True)
    n_transits = Column(Integer, nullable=True)
    odd_even_mismatch = Column(Float, nullable=True)

    candidate = relationship("Candidate", back_populates="transit_features")


class RadioFeature(Base):
    """Radio-specific features extracted during detection."""

    __tablename__ = "radio_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(
        Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    frequency_mhz = Column(Float, nullable=True)
    bandwidth_hz = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    signal_strength = Column(Float, nullable=True)
    integrated_power = Column(Float, nullable=True)
    drift_rate = Column(Float, nullable=True)

    candidate = relationship("Candidate", back_populates="radio_features")
