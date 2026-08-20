"""
ANVESHAK — Database Models
Complete PostgreSQL schema for the Exoplanet Data Analysis Platform.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.models.database import Base


# ═══════════════════════════════════════════════════════════════════════════════
# Sources — Registered data sources (NASA Exoplanet Archive, etc.)
# ═══════════════════════════════════════════════════════════════════════════════
class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, unique=True)
    type = Column(String(64), nullable=False)  # e.g. "tap", "csv", "api"
    description = Column(Text, nullable=True)
    base_url = Column(String(512), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    datasets = relationship("Dataset", back_populates="source", cascade="all, delete-orphan")


# ═══════════════════════════════════════════════════════════════════════════════
# Datasets — Individual ingested datasets from a source
# ═══════════════════════════════════════════════════════════════════════════════
class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(256), nullable=False)
    source_table = Column(String(128), nullable=True)  # e.g. "pscomppars", "koi"
    version = Column(String(64), nullable=True)
    record_count = Column(Integer, default=0)
    query_used = Column(Text, nullable=True)
    ingestion_status = Column(String(32), default="pending")  # pending/running/completed/failed
    ingestion_started_at = Column(DateTime(timezone=True), nullable=True)
    ingestion_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", back_populates="datasets")
    objects = relationship("AstronomicalObject", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_datasets_source_id", "source_id"),
        Index("ix_datasets_status", "ingestion_status"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Astronomical Objects — Core entity for planets, candidates, etc.
# ═══════════════════════════════════════════════════════════════════════════════
class AstronomicalObject(Base):
    __tablename__ = "astronomical_objects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(128), nullable=False)  # e.g. "nasa_exoplanet_archive"
    external_id = Column(String(256), nullable=False)  # e.g. "Kepler-22 b"
    object_type = Column(String(64), nullable=False)  # "confirmed", "candidate", "false_positive"
    name = Column(String(256), nullable=False)
    host_name = Column(String(256), nullable=True)
    ra = Column(Float, nullable=True)  # Right ascension (degrees)
    dec = Column(Float, nullable=True)  # Declination (degrees)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", back_populates="objects")
    planet_params = relationship("PlanetParameter", back_populates="object", uselist=False, cascade="all, delete-orphan")
    stellar_params = relationship("StellarParameter", back_populates="object", uselist=False, cascade="all, delete-orphan")
    engineered_features = relationship("EngineeredFeature", back_populates="object", cascade="all, delete-orphan")
    predictions = relationship("MLPrediction", back_populates="object", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="object", cascade="all, delete-orphan")
    clusters = relationship("Cluster", back_populates="object", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_objects_external_id", "external_id"),
        Index("ix_objects_name", "name"),
        Index("ix_objects_host_name", "host_name"),
        Index("ix_objects_type", "object_type"),
        Index("ix_objects_source", "source"),
        Index("ix_objects_dataset_id", "dataset_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Planet Parameters — Normalized planetary properties
# ═══════════════════════════════════════════════════════════════════════════════
class PlanetParameter(Base):
    __tablename__ = "planet_parameters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(Integer, ForeignKey("astronomical_objects.id", ondelete="CASCADE"), nullable=False, unique=True)

    planet_radius_earth = Column(Float, nullable=True)
    planet_mass_earth = Column(Float, nullable=True)
    orbital_period_days = Column(Float, nullable=True)
    semi_major_axis_au = Column(Float, nullable=True)
    eccentricity = Column(Float, nullable=True)
    density_g_cm3 = Column(Float, nullable=True)
    equilibrium_temp_k = Column(Float, nullable=True)
    transit_depth = Column(Float, nullable=True)
    transit_duration_hrs = Column(Float, nullable=True)
    inclination_deg = Column(Float, nullable=True)
    discovery_method = Column(String(128), nullable=True)
    discovery_facility = Column(String(256), nullable=True)
    discovery_year = Column(Integer, nullable=True)

    object = relationship("AstronomicalObject", back_populates="planet_params")

    __table_args__ = (
        Index("ix_planet_params_period", "orbital_period_days"),
        Index("ix_planet_params_radius", "planet_radius_earth"),
        Index("ix_planet_params_method", "discovery_method"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Stellar Parameters — Host star properties
# ═══════════════════════════════════════════════════════════════════════════════
class StellarParameter(Base):
    __tablename__ = "stellar_parameters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(Integer, ForeignKey("astronomical_objects.id", ondelete="CASCADE"), nullable=False, unique=True)

    effective_temp_k = Column(Float, nullable=True)
    stellar_radius_solar = Column(Float, nullable=True)
    stellar_mass_solar = Column(Float, nullable=True)
    metallicity_fe_h = Column(Float, nullable=True)
    surface_gravity_log_cgs = Column(Float, nullable=True)
    luminosity_solar = Column(Float, nullable=True)
    spectral_type = Column(String(32), nullable=True)

    object = relationship("AstronomicalObject", back_populates="stellar_params")

    __table_args__ = (
        Index("ix_stellar_params_temp", "effective_temp_k"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Engineered Features — Derived feature values from feature engineering
# ═══════════════════════════════════════════════════════════════════════════════
class EngineeredFeature(Base):
    __tablename__ = "engineered_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(Integer, ForeignKey("astronomical_objects.id", ondelete="CASCADE"), nullable=False)
    feature_name = Column(String(128), nullable=False)
    feature_value = Column(Float, nullable=True)
    feature_version = Column(String(32), default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    object = relationship("AstronomicalObject", back_populates="engineered_features")

    __table_args__ = (
        Index("ix_eng_features_object_name", "object_id", "feature_name"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ML Predictions — Classification results from ML models
# ═══════════════════════════════════════════════════════════════════════════════
class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(Integer, ForeignKey("astronomical_objects.id", ondelete="CASCADE"), nullable=False)
    model_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)
    predicted_class = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities = Column(JSON, nullable=True)  # {"CONFIRMED": 0.8, "CANDIDATE": 0.15, ...}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    object = relationship("AstronomicalObject", back_populates="predictions")
    model_version = relationship("ModelVersion")

    __table_args__ = (
        Index("ix_predictions_object_id", "object_id"),
        Index("ix_predictions_class", "predicted_class"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Anomalies — Anomaly detection results
# ═══════════════════════════════════════════════════════════════════════════════
class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(Integer, ForeignKey("astronomical_objects.id", ondelete="CASCADE"), nullable=False)
    algorithm = Column(String(64), nullable=False)  # e.g. "IsolationForest"
    anomaly_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=True)
    feature_contributions = Column(JSON, nullable=True)  # Top features contributing to score
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    object = relationship("AstronomicalObject", back_populates="anomalies")

    __table_args__ = (
        Index("ix_anomalies_object_id", "object_id"),
        Index("ix_anomalies_score", "anomaly_score"),
        Index("ix_anomalies_rank", "rank"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Clusters — Clustering assignments
# ═══════════════════════════════════════════════════════════════════════════════
class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(Integer, ForeignKey("astronomical_objects.id", ondelete="CASCADE"), nullable=False)
    algorithm = Column(String(64), nullable=False)  # e.g. "KMeans"
    cluster_id = Column(Integer, nullable=False)
    distance_to_centroid = Column(Float, nullable=True)
    pca_x = Column(Float, nullable=True)
    pca_y = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    object = relationship("AstronomicalObject", back_populates="clusters")

    __table_args__ = (
        Index("ix_clusters_object_id", "object_id"),
        Index("ix_clusters_cluster_id", "cluster_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Model Versions — ML model registry
# ═══════════════════════════════════════════════════════════════════════════════
class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)  # e.g. "exoplanet_classifier"
    algorithm = Column(String(64), nullable=False)  # e.g. "RandomForestClassifier"
    version = Column(String(32), nullable=False)
    training_dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    metrics = Column(JSON, nullable=True)  # {"accuracy": 0.92, "f1": 0.89, ...}
    artifact_path = Column(String(512), nullable=True)
    feature_list = Column(JSON, nullable=True)  # ["orbital_period_days", "planet_radius_earth", ...]
    confusion_matrix = Column(JSON, nullable=True)  # [[tp, fp], [fn, tn]]
    feature_importances = Column(JSON, nullable=True)  # {"feature": importance, ...}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    training_dataset = relationship("Dataset")


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Jobs — Background job tracking
# ═══════════════════════════════════════════════════════════════════════════════
class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_type = Column(String(64), nullable=False)  # "ingestion", "training", "prediction", "anomaly", "clustering"
    status = Column(String(32), default="queued")  # queued/running/completed/failed
    progress = Column(Float, default=0.0)  # 0.0 to 100.0
    parameters = Column(JSON, nullable=True)
    result_location = Column(String(512), nullable=True)
    result_summary = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_type", "job_type"),
    )
