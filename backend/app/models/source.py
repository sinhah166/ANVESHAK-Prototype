"""
ANVESHAK — Source Database Model
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    func,
)

from app.models.database import Base


class Source(Base):
    """Source table — registered data sources (telescopes, instruments)."""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    source_key = Column(String(64), nullable=False, unique=True)
    type = Column(String(32), nullable=False, index=True)
    adapter = Column(String(64), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    status = Column(String(32), default="unknown")
    last_seen = Column(DateTime(timezone=True), nullable=True)
    observation_count = Column(Integer, default=0)
    error_message = Column(String(512), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.source_key,
            "name": self.name,
            "type": self.type,
            "adapter": self.adapter,
            "enabled": self.enabled,
            "health": self.status or "unknown",
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "observation_count": self.observation_count or 0,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
