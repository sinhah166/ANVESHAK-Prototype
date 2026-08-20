"""
ANVESHAK — Pydantic Schemas
Request/Response models for all API endpoints.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Source Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class SourceResponse(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str] = None
    base_url: Optional[str] = None
    active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    dataset_count: int = 0


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Dataset Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class DatasetResponse(BaseModel):
    id: int
    source_id: int
    name: str
    source_table: Optional[str] = None
    version: Optional[str] = None
    record_count: int = 0
    query_used: Optional[str] = None
    ingestion_status: str
    ingestion_started_at: Optional[datetime] = None
    ingestion_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Planet Parameter Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class PlanetParameterResponse(BaseModel):
    planet_radius_earth: Optional[float] = None
    planet_mass_earth: Optional[float] = None
    orbital_period_days: Optional[float] = None
    semi_major_axis_au: Optional[float] = None
    eccentricity: Optional[float] = None
    density_g_cm3: Optional[float] = None
    equilibrium_temp_k: Optional[float] = None
    transit_depth: Optional[float] = None
    transit_duration_hrs: Optional[float] = None
    inclination_deg: Optional[float] = None
    discovery_method: Optional[str] = None
    discovery_facility: Optional[str] = None
    discovery_year: Optional[int] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Stellar Parameter Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class StellarParameterResponse(BaseModel):
    effective_temp_k: Optional[float] = None
    stellar_radius_solar: Optional[float] = None
    stellar_mass_solar: Optional[float] = None
    metallicity_fe_h: Optional[float] = None
    surface_gravity_log_cgs: Optional[float] = None
    luminosity_solar: Optional[float] = None
    spectral_type: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Astronomical Object Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class ObjectSummaryResponse(BaseModel):
    id: int
    external_id: str
    name: str
    host_name: Optional[str] = None
    object_type: str
    ra: Optional[float] = None
    dec: Optional[float] = None
    # Key planet params inlined for table display
    orbital_period_days: Optional[float] = None
    planet_radius_earth: Optional[float] = None
    planet_mass_earth: Optional[float] = None
    discovery_method: Optional[str] = None
    discovery_year: Optional[int] = None
    # ML results inlined
    predicted_class: Optional[str] = None
    confidence: Optional[float] = None
    anomaly_score: Optional[float] = None
    anomaly_rank: Optional[int] = None
    cluster_id: Optional[int] = None
    priority_score: Optional[float] = None


class ObjectListResponse(BaseModel):
    objects: list[ObjectSummaryResponse]
    total: int
    page: int
    page_size: int


class EngineeredFeatureResponse(BaseModel):
    feature_name: str
    feature_value: Optional[float] = None
    feature_version: str = "v1"


class PredictionResponse(BaseModel):
    id: int
    predicted_class: str
    confidence: float
    probabilities: Optional[dict[str, float]] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    created_at: Optional[datetime] = None


class AnomalyResponse(BaseModel):
    id: int
    algorithm: str
    anomaly_score: float
    rank: Optional[int] = None
    feature_contributions: Optional[dict[str, float]] = None
    created_at: Optional[datetime] = None


class ClusterResponse(BaseModel):
    id: int
    algorithm: str
    cluster_id: int
    distance_to_centroid: Optional[float] = None
    pca_x: Optional[float] = None
    pca_y: Optional[float] = None
    created_at: Optional[datetime] = None


class ObjectDetailResponse(BaseModel):
    id: int
    external_id: str
    name: str
    host_name: Optional[str] = None
    object_type: str
    source: str
    ra: Optional[float] = None
    dec: Optional[float] = None
    planet_parameters: Optional[PlanetParameterResponse] = None
    stellar_parameters: Optional[StellarParameterResponse] = None
    engineered_features: list[EngineeredFeatureResponse] = []
    predictions: list[PredictionResponse] = []
    anomalies: list[AnomalyResponse] = []
    clusters: list[ClusterResponse] = []
    priority_score: Optional[float] = None
    created_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Schemas — Request/Response for analysis endpoints
# ═══════════════════════════════════════════════════════════════════════════════
class ScatterRequest(BaseModel):
    x_column: str = "orbital_period_days"
    y_column: str = "planet_radius_earth"
    color_by: Optional[str] = None  # "discovery_method", "cluster_id", "object_type"
    filter_min_x: Optional[float] = None
    filter_max_x: Optional[float] = None
    filter_min_y: Optional[float] = None
    filter_max_y: Optional[float] = None
    log_x: bool = False
    log_y: bool = False
    dataset_id: Optional[int] = None


class ScatterResponse(BaseModel):
    x: list[Optional[float]]
    y: list[Optional[float]]
    names: list[str]
    ids: list[int]
    colors: Optional[list[Optional[str]]] = None
    x_label: str
    y_label: str
    color_label: Optional[str] = None
    total: int


class HistogramRequest(BaseModel):
    column: str = "planet_radius_earth"
    bins: int = 50
    log_scale: bool = False
    dataset_id: Optional[int] = None
    filter_object_type: Optional[str] = None


class HistogramResponse(BaseModel):
    values: list[Optional[float]]
    label: str
    bins: int
    total: int


class CorrelationRequest(BaseModel):
    columns: Optional[list[str]] = None
    dataset_id: Optional[int] = None


class CorrelationResponse(BaseModel):
    matrix: list[list[Optional[float]]]
    labels: list[str]
    total_objects: int


class PCARequest(BaseModel):
    n_components: int = 2
    color_by: Optional[str] = None
    dataset_id: Optional[int] = None


class PCAResponse(BaseModel):
    components: list[list[float]]  # [[x1,y1], [x2,y2], ...]
    explained_variance: list[float]
    names: list[str]
    ids: list[int]
    colors: Optional[list[Optional[str]]] = None
    color_label: Optional[str] = None
    features_used: list[str]


class AnomalyListResponse(BaseModel):
    anomalies: list[dict[str, Any]]
    total: int


class ClassificationSummaryResponse(BaseModel):
    class_distribution: dict[str, int]
    total_predictions: int
    model_info: Optional[dict[str, Any]] = None
    predictions: list[dict[str, Any]] = []


# ═══════════════════════════════════════════════════════════════════════════════
# ML Model Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class ModelVersionResponse(BaseModel):
    id: int
    name: str
    algorithm: str
    version: str
    training_dataset_id: Optional[int] = None
    metrics: Optional[dict[str, Any]] = None
    feature_list: Optional[list[str]] = None
    confusion_matrix: Optional[list[list[int]]] = None
    feature_importances: Optional[dict[str, float]] = None
    created_at: Optional[datetime] = None


class ModelListResponse(BaseModel):
    models: list[ModelVersionResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Job Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class IngestionRequest(BaseModel):
    source: str = "nasa_exoplanet_archive"
    dataset: str = "pscomppars"
    max_records: int = Field(default=2000, ge=10, le=50000)
    filters: Optional[dict[str, Any]] = None


class JobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    progress: float = 0.0
    parameters: Optional[dict[str, Any]] = None
    result_summary: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Candidate Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class CandidateResponse(BaseModel):
    id: int
    external_id: str
    name: str
    host_name: Optional[str] = None
    object_type: str
    predicted_class: Optional[str] = None
    confidence: Optional[float] = None
    probabilities: Optional[dict[str, float]] = None
    anomaly_score: Optional[float] = None
    anomaly_rank: Optional[int] = None
    priority_score: Optional[float] = None
    orbital_period_days: Optional[float] = None
    planet_radius_earth: Optional[float] = None
    planet_mass_earth: Optional[float] = None
    discovery_method: Optional[str] = None


class CandidateListResponse(BaseModel):
    candidates: list[CandidateResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class DashboardStatsResponse(BaseModel):
    total_datasets: int = 0
    total_objects: int = 0
    total_confirmed: int = 0
    total_candidates: int = 0
    total_false_positives: int = 0
    total_anomalies: int = 0
    high_priority_count: int = 0
    last_sync: Optional[datetime] = None
    latest_model_version: Optional[str] = None
    data_mode: str = "demo"
    discovery_method_distribution: dict[str, int] = {}
    object_type_distribution: dict[str, int] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# Workbench Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class WorkbenchRequest(BaseModel):
    plot_type: str = "scatter"  # scatter, histogram, box, correlation, pca, anomaly_ranking
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_by: Optional[str] = None
    dataset_id: Optional[int] = None
    filters: Optional[dict[str, Any]] = None
    bins: int = 50
    log_x: bool = False
    log_y: bool = False
