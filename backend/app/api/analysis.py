"""
ANVESHAK — Analysis API
Endpoints for scientific data analysis: scatter, histogram, correlation, PCA, anomalies, classification.
All data is returned machine-readable — no hardcoded chart values.
"""

from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.db_models import (
    Anomaly,
    AstronomicalObject,
    Cluster,
    MLPrediction,
    ModelVersion,
    PlanetParameter,
    StellarParameter,
)
from app.schemas.schemas import (
    AnomalyListResponse,
    ClassificationSummaryResponse,
    CorrelationResponse,
    HistogramResponse,
    PCAResponse,
    ScatterResponse,
)

router = APIRouter()

# Available columns for analysis
PLANET_COLS = {
    "orbital_period_days": PlanetParameter.orbital_period_days,
    "planet_radius_earth": PlanetParameter.planet_radius_earth,
    "planet_mass_earth": PlanetParameter.planet_mass_earth,
    "semi_major_axis_au": PlanetParameter.semi_major_axis_au,
    "eccentricity": PlanetParameter.eccentricity,
    "density_g_cm3": PlanetParameter.density_g_cm3,
    "equilibrium_temp_k": PlanetParameter.equilibrium_temp_k,
    "transit_depth": PlanetParameter.transit_depth,
    "transit_duration_hrs": PlanetParameter.transit_duration_hrs,
    "inclination_deg": PlanetParameter.inclination_deg,
}

STELLAR_COLS = {
    "effective_temp_k": StellarParameter.effective_temp_k,
    "stellar_radius_solar": StellarParameter.stellar_radius_solar,
    "stellar_mass_solar": StellarParameter.stellar_mass_solar,
    "metallicity_fe_h": StellarParameter.metallicity_fe_h,
    "surface_gravity_log_cgs": StellarParameter.surface_gravity_log_cgs,
    "luminosity_solar": StellarParameter.luminosity_solar,
}

ALL_NUMERIC_COLS = list(PLANET_COLS.keys()) + list(STELLAR_COLS.keys())

COLOR_BY_OPTIONS = {
    "discovery_method": PlanetParameter.discovery_method,
    "object_type": AstronomicalObject.object_type,
}


async def _build_analysis_dataframe(
    db: AsyncSession,
    columns: list[str],
    dataset_id: Optional[int] = None,
) -> pd.DataFrame:
    """Build a DataFrame from DB for analysis."""
    query = (
        select(
            AstronomicalObject.id,
            AstronomicalObject.name,
            AstronomicalObject.object_type,
            PlanetParameter.orbital_period_days,
            PlanetParameter.planet_radius_earth,
            PlanetParameter.planet_mass_earth,
            PlanetParameter.semi_major_axis_au,
            PlanetParameter.eccentricity,
            PlanetParameter.density_g_cm3,
            PlanetParameter.equilibrium_temp_k,
            PlanetParameter.transit_depth,
            PlanetParameter.transit_duration_hrs,
            PlanetParameter.inclination_deg,
            PlanetParameter.discovery_method,
            PlanetParameter.discovery_year,
            StellarParameter.effective_temp_k,
            StellarParameter.stellar_radius_solar,
            StellarParameter.stellar_mass_solar,
            StellarParameter.metallicity_fe_h,
            StellarParameter.surface_gravity_log_cgs,
            StellarParameter.luminosity_solar,
        )
        .join(PlanetParameter, PlanetParameter.object_id == AstronomicalObject.id, isouter=True)
        .join(StellarParameter, StellarParameter.object_id == AstronomicalObject.id, isouter=True)
    )

    if dataset_id:
        query = query.where(AstronomicalObject.dataset_id == dataset_id)

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=[
        "id", "name", "object_type",
        "orbital_period_days", "planet_radius_earth", "planet_mass_earth",
        "semi_major_axis_au", "eccentricity", "density_g_cm3",
        "equilibrium_temp_k", "transit_depth", "transit_duration_hrs",
        "inclination_deg", "discovery_method", "discovery_year",
        "effective_temp_k", "stellar_radius_solar", "stellar_mass_solar",
        "metallicity_fe_h", "surface_gravity_log_cgs", "luminosity_solar",
    ])

    return df


@router.get("/scatter", response_model=ScatterResponse)
async def scatter_analysis(
    x_column: str = "orbital_period_days",
    y_column: str = "planet_radius_earth",
    color_by: Optional[str] = None,
    log_x: bool = False,
    log_y: bool = False,
    dataset_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate scatter plot data."""
    if x_column not in ALL_NUMERIC_COLS or y_column not in ALL_NUMERIC_COLS:
        raise HTTPException(400, f"Invalid column. Available: {ALL_NUMERIC_COLS}")

    df = await _build_analysis_dataframe(db, [x_column, y_column], dataset_id)
    if df.empty:
        return ScatterResponse(x=[], y=[], names=[], ids=[], x_label=x_column, y_label=y_column, total=0)

    # Drop rows where both x and y are null
    mask = df[x_column].notna() & df[y_column].notna()
    df = df[mask]

    x_vals = df[x_column].tolist()
    y_vals = df[y_column].tolist()

    colors = None
    color_label = None
    if color_by and color_by in df.columns:
        colors = df[color_by].fillna("Unknown").astype(str).tolist()
        color_label = color_by

    return ScatterResponse(
        x=x_vals,
        y=y_vals,
        names=df["name"].tolist(),
        ids=df["id"].tolist(),
        colors=colors,
        x_label=x_column,
        y_label=y_column,
        color_label=color_label,
        total=len(df),
    )


@router.get("/histogram", response_model=HistogramResponse)
async def histogram_analysis(
    column: str = "planet_radius_earth",
    bins: int = Query(50, ge=5, le=200),
    dataset_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate histogram data."""
    if column not in ALL_NUMERIC_COLS:
        raise HTTPException(400, f"Invalid column. Available: {ALL_NUMERIC_COLS}")

    df = await _build_analysis_dataframe(db, [column], dataset_id)
    if df.empty:
        return HistogramResponse(values=[], label=column, bins=bins, total=0)

    values = df[column].dropna().tolist()
    return HistogramResponse(values=values, label=column, bins=bins, total=len(values))


@router.get("/correlation", response_model=CorrelationResponse)
async def correlation_analysis(
    dataset_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate correlation matrix for numeric features."""
    df = await _build_analysis_dataframe(db, ALL_NUMERIC_COLS, dataset_id)
    if df.empty:
        return CorrelationResponse(matrix=[], labels=[], total_objects=0)

    numeric_df = df[ALL_NUMERIC_COLS].apply(pd.to_numeric, errors="coerce")
    # Only keep columns with sufficient non-null data
    valid_cols = [c for c in numeric_df.columns if numeric_df[c].notna().sum() > 10]
    numeric_df = numeric_df[valid_cols]

    corr = numeric_df.corr()
    matrix = corr.values.tolist()
    # Replace NaN with None
    matrix = [
        [None if (isinstance(v, float) and np.isnan(v)) else round(v, 4) for v in row]
        for row in matrix
    ]

    return CorrelationResponse(
        matrix=matrix,
        labels=valid_cols,
        total_objects=len(df),
    )


@router.get("/pca", response_model=PCAResponse)
async def pca_analysis(
    n_components: int = Query(2, ge=2, le=5),
    color_by: Optional[str] = None,
    dataset_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate PCA visualization data."""
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer

    df = await _build_analysis_dataframe(db, ALL_NUMERIC_COLS, dataset_id)
    if df.empty:
        return PCAResponse(components=[], explained_variance=[], names=[], ids=[], features_used=[])

    numeric_df = df[ALL_NUMERIC_COLS].apply(pd.to_numeric, errors="coerce")
    valid_cols = [c for c in numeric_df.columns if numeric_df[c].notna().sum() > 10]
    if len(valid_cols) < 2:
        raise HTTPException(400, "Insufficient numeric data for PCA")

    X = numeric_df[valid_cols].values
    imputer = SimpleImputer(strategy="median")
    X_imputed = imputer.fit_transform(X)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    n_comp = min(n_components, X_scaled.shape[1], X_scaled.shape[0])
    pca = PCA(n_components=n_comp, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    colors = None
    color_label = None
    if color_by and color_by in df.columns:
        colors = df[color_by].fillna("Unknown").astype(str).tolist()
        color_label = color_by

    return PCAResponse(
        components=X_pca.tolist(),
        explained_variance=pca.explained_variance_ratio_.tolist(),
        names=df["name"].tolist(),
        ids=df["id"].tolist(),
        colors=colors,
        color_label=color_label,
        features_used=valid_cols,
    )


@router.get("/anomalies")
async def anomaly_analysis(
    limit: int = Query(50, ge=1, le=500),
    dataset_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List top anomalous objects."""
    query = (
        select(
            Anomaly.id,
            Anomaly.anomaly_score,
            Anomaly.rank,
            Anomaly.algorithm,
            Anomaly.feature_contributions,
            AstronomicalObject.name,
            AstronomicalObject.external_id,
            AstronomicalObject.object_type,
            AstronomicalObject.id.label("object_id"),
        )
        .join(AstronomicalObject, Anomaly.object_id == AstronomicalObject.id)
    )
    if dataset_id:
        query = query.where(AstronomicalObject.dataset_id == dataset_id)

    query = query.order_by(Anomaly.anomaly_score.asc()).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return {
        "anomalies": [
            {
                "id": r.id,
                "object_id": r.object_id,
                "name": r.name,
                "external_id": r.external_id,
                "object_type": r.object_type,
                "anomaly_score": r.anomaly_score,
                "rank": r.rank,
                "algorithm": r.algorithm,
                "feature_contributions": r.feature_contributions,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.get("/classification")
async def classification_analysis(
    dataset_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get classification summary and predictions."""
    query = (
        select(
            MLPrediction.predicted_class,
            func.count().label("count"),
        )
        .group_by(MLPrediction.predicted_class)
    )
    result = await db.execute(query)
    distribution = {row.predicted_class: row.count for row in result.all()}

    # Get recent predictions
    pred_query = (
        select(
            MLPrediction.id,
            MLPrediction.predicted_class,
            MLPrediction.confidence,
            MLPrediction.probabilities,
            AstronomicalObject.name,
            AstronomicalObject.external_id,
            AstronomicalObject.id.label("object_id"),
        )
        .join(AstronomicalObject, MLPrediction.object_id == AstronomicalObject.id)
        .order_by(MLPrediction.confidence.desc())
        .limit(100)
    )
    pred_result = await db.execute(pred_query)
    predictions = [
        {
            "id": r.id,
            "object_id": r.object_id,
            "name": r.name,
            "external_id": r.external_id,
            "predicted_class": r.predicted_class,
            "confidence": r.confidence,
            "probabilities": r.probabilities,
        }
        for r in pred_result.all()
    ]

    return {
        "class_distribution": distribution,
        "total_predictions": sum(distribution.values()),
        "predictions": predictions,
    }


@router.get("/columns")
async def get_available_columns():
    """Return available analysis columns."""
    return {
        "numeric_columns": ALL_NUMERIC_COLS,
        "color_by_options": ["discovery_method", "object_type", "cluster_id"],
        "plot_types": ["scatter", "histogram", "box", "correlation", "pca", "anomaly_ranking"],
    }
