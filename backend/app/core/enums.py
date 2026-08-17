"""
ANVESHAK — Core Enumerations
Defines all enum types used across the pipeline.
"""

from enum import Enum


class SignalType(str, Enum):
    """Types of astronomical signals detected by the pipeline."""
    TRANSIT = "transit"
    RADIAL_VELOCITY = "radial_velocity"
    MICROLENSING = "microlensing"
    RADIO_NARROWBAND = "radio_narrowband"
    RADIO_BROADBAND = "radio_broadband"
    STELLAR_VARIABILITY = "stellar_variability"
    NOISE = "noise"
    RFI = "rfi"
    ANOMALY = "anomaly"
    UNKNOWN = "unknown"


class CandidateClassification(str, Enum):
    """Classification labels for detected candidates."""
    PLANET_CANDIDATE = "planet_candidate"
    FALSE_POSITIVE = "false_positive"
    STELLAR_VARIABILITY = "stellar_variability"
    ECLIPSING_BINARY = "eclipsing_binary"
    NOISE = "noise"
    RFI = "rfi"
    NARROWBAND_CANDIDATE = "narrowband_candidate"
    ANOMALY = "anomaly"
    UNCLASSIFIED = "unclassified"


class CandidateStatus(str, Enum):
    """Status of a candidate through the review process."""
    NEW = "new"
    CONFIRMED_CANDIDATE = "confirmed_candidate"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class SourceType(str, Enum):
    """Types of observational data sources."""
    LIGHTCURVE = "lightcurve"
    RADIO = "radio"


class DataMode(str, Enum):
    """Data ingestion modes."""
    DEMO = "demo"
    ARCHIVE = "archive"


class PipelineStage(str, Enum):
    """Stages of the processing pipeline."""
    INGESTION = "ingestion"
    PREPROCESSING = "preprocessing"
    DETECTION = "detection"
    CLASSIFICATION = "classification"
    NORMALIZATION = "normalization"
    QUEUE = "queue"
    DATABASE = "database"
    WEBSOCKET = "websocket"


class PipelineStatus(str, Enum):
    """Status of a pipeline stage."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class SourceHealth(str, Enum):
    """Health status of a data source."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
