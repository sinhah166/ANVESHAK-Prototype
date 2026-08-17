"""
ANVESHAK — Observation Database Model
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)

from app.models.database import Base


class Observation(Base):
    """Observation table — stores all normalized observations from any source."""

    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(64), nullable=False, index=True)
    record_id = Column(String(256), nullable=False, unique=True)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    target_name = Column(String(256), nullable=False)
    ra = Column(Float, nullable=False)
    dec = Column(Float, nullable=False)
    signal_type = Column(String(64), nullable=False, index=True)
    raw_payload = Column(JSON, default=dict)
    confidence = Column(Float, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_observations_observed_at", "observed_at"),
        Index("ix_observations_confidence", "confidence"),
        Index("ix_observations_source_signal", "source_id", "signal_type"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "record_id": self.record_id,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "target": {
                "name": self.target_name,
                "ra": self.ra,
                "dec": self.dec,
            },
            "signal_type": self.signal_type,
            "raw_payload": self.raw_payload or {},
            "preliminary_confidence": self.confidence,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
