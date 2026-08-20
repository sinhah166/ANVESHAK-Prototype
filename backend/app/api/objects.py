"""
ANVESHAK — Objects API
Endpoints for listing, searching, and viewing astronomical objects.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_db
from app.models.db_models import (
    Anomaly,
    AstronomicalObject,
    Cluster,
    EngineeredFeature,
    MLPrediction,
    ModelVersion,
    PlanetParameter,
    StellarParameter,
)
from app.schemas.schemas import (
    AnomalyResponse,
    ClusterResponse,
    EngineeredFeatureResponse,
    ObjectDetailResponse,
    ObjectListResponse,
    ObjectSummaryResponse,
    PlanetParameterResponse,
    PredictionResponse,
    StellarParameterResponse,
)

router = APIRouter()


@router.get("/", response_model=ObjectListResponse)
async def list_objects(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    object_type: Optional[str] = None,
    discovery_method: Optional[str] = None,
    min_radius: Optional[float] = None,
    max_radius: Optional[float] = None,
    min_period: Optional[float] = None,
    max_period: Optional[float] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    dataset_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List astronomical objects with filtering, search, and pagination."""
    query = (
        select(AstronomicalObject)
        .outerjoin(PlanetParameter)
        .outerjoin(MLPrediction)
        .outerjoin(Anomaly)
    )

    # Filters
    if search:
        query = query.where(
            or_(
                AstronomicalObject.name.ilike(f"%{search}%"),
                AstronomicalObject.host_name.ilike(f"%{search}%"),
                AstronomicalObject.external_id.ilike(f"%{search}%"),
            )
        )
    if object_type:
        query = query.where(AstronomicalObject.object_type == object_type)
    if discovery_method:
        query = query.where(PlanetParameter.discovery_method == discovery_method)
    if min_radius is not None:
        query = query.where(PlanetParameter.planet_radius_earth >= min_radius)
    if max_radius is not None:
        query = query.where(PlanetParameter.planet_radius_earth <= max_radius)
    if min_period is not None:
        query = query.where(PlanetParameter.orbital_period_days >= min_period)
    if max_period is not None:
        query = query.where(PlanetParameter.orbital_period_days <= max_period)
    if dataset_id:
        query = query.where(AstronomicalObject.dataset_id == dataset_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    sort_col = getattr(AstronomicalObject, sort_by, AstronomicalObject.name)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.distinct()

    result = await db.execute(query)
    objects = result.scalars().unique().all()

    # Build summaries with joined data
    summaries = []
    for obj in objects:
        # Load relationships
        pp_r = await db.execute(select(PlanetParameter).where(PlanetParameter.object_id == obj.id))
        pp = pp_r.scalar_one_or_none()

        pred_r = await db.execute(
            select(MLPrediction).where(MLPrediction.object_id == obj.id)
            .order_by(MLPrediction.created_at.desc()).limit(1)
        )
        pred = pred_r.scalar_one_or_none()

        anom_r = await db.execute(
            select(Anomaly).where(Anomaly.object_id == obj.id)
            .order_by(Anomaly.created_at.desc()).limit(1)
        )
        anom = anom_r.scalar_one_or_none()

        clust_r = await db.execute(
            select(Cluster).where(Cluster.object_id == obj.id)
            .order_by(Cluster.created_at.desc()).limit(1)
        )
        clust = clust_r.scalar_one_or_none()

        summaries.append(ObjectSummaryResponse(
            id=obj.id,
            external_id=obj.external_id,
            name=obj.name,
            host_name=obj.host_name,
            object_type=obj.object_type,
            ra=obj.ra,
            dec=obj.dec,
            orbital_period_days=pp.orbital_period_days if pp else None,
            planet_radius_earth=pp.planet_radius_earth if pp else None,
            planet_mass_earth=pp.planet_mass_earth if pp else None,
            discovery_method=pp.discovery_method if pp else None,
            discovery_year=pp.discovery_year if pp else None,
            predicted_class=pred.predicted_class if pred else None,
            confidence=pred.confidence if pred else None,
            anomaly_score=anom.anomaly_score if anom else None,
            anomaly_rank=anom.rank if anom else None,
            cluster_id=clust.cluster_id if clust else None,
        ))

    return ObjectListResponse(
        objects=summaries,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{object_id}", response_model=ObjectDetailResponse)
async def get_object_detail(object_id: int, db: AsyncSession = Depends(get_db)):
    """Get full detail for a single astronomical object."""
    result = await db.execute(
        select(AstronomicalObject).where(AstronomicalObject.id == object_id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    # Planet parameters
    pp_r = await db.execute(select(PlanetParameter).where(PlanetParameter.object_id == object_id))
    pp = pp_r.scalar_one_or_none()

    # Stellar parameters
    sp_r = await db.execute(select(StellarParameter).where(StellarParameter.object_id == object_id))
    sp = sp_r.scalar_one_or_none()

    # Engineered features
    ef_r = await db.execute(select(EngineeredFeature).where(EngineeredFeature.object_id == object_id))
    features = ef_r.scalars().all()

    # Predictions
    pred_r = await db.execute(
        select(MLPrediction).where(MLPrediction.object_id == object_id)
        .order_by(MLPrediction.created_at.desc())
    )
    predictions = pred_r.scalars().all()

    # Anomalies
    anom_r = await db.execute(
        select(Anomaly).where(Anomaly.object_id == object_id)
        .order_by(Anomaly.created_at.desc())
    )
    anomalies = anom_r.scalars().all()

    # Clusters
    clust_r = await db.execute(
        select(Cluster).where(Cluster.object_id == object_id)
        .order_by(Cluster.created_at.desc())
    )
    clusters = clust_r.scalars().all()

    # Build response
    pred_responses = []
    for p in predictions:
        model_name = None
        model_version = None
        if p.model_version_id:
            mv_r = await db.execute(select(ModelVersion).where(ModelVersion.id == p.model_version_id))
            mv = mv_r.scalar_one_or_none()
            if mv:
                model_name = mv.name
                model_version = mv.version
        pred_responses.append(PredictionResponse(
            id=p.id,
            predicted_class=p.predicted_class,
            confidence=p.confidence,
            probabilities=p.probabilities,
            model_name=model_name,
            model_version=model_version,
            created_at=p.created_at,
        ))

    return ObjectDetailResponse(
        id=obj.id,
        external_id=obj.external_id,
        name=obj.name,
        host_name=obj.host_name,
        object_type=obj.object_type,
        source=obj.source,
        ra=obj.ra,
        dec=obj.dec,
        planet_parameters=PlanetParameterResponse(
            planet_radius_earth=pp.planet_radius_earth,
            planet_mass_earth=pp.planet_mass_earth,
            orbital_period_days=pp.orbital_period_days,
            semi_major_axis_au=pp.semi_major_axis_au,
            eccentricity=pp.eccentricity,
            density_g_cm3=pp.density_g_cm3,
            equilibrium_temp_k=pp.equilibrium_temp_k,
            transit_depth=pp.transit_depth,
            transit_duration_hrs=pp.transit_duration_hrs,
            inclination_deg=pp.inclination_deg,
            discovery_method=pp.discovery_method,
            discovery_facility=pp.discovery_facility,
            discovery_year=pp.discovery_year,
        ) if pp else None,
        stellar_parameters=StellarParameterResponse(
            effective_temp_k=sp.effective_temp_k,
            stellar_radius_solar=sp.stellar_radius_solar,
            stellar_mass_solar=sp.stellar_mass_solar,
            metallicity_fe_h=sp.metallicity_fe_h,
            surface_gravity_log_cgs=sp.surface_gravity_log_cgs,
            luminosity_solar=sp.luminosity_solar,
            spectral_type=sp.spectral_type,
        ) if sp else None,
        engineered_features=[
            EngineeredFeatureResponse(
                feature_name=f.feature_name,
                feature_value=f.feature_value,
                feature_version=f.feature_version,
            ) for f in features
        ],
        predictions=pred_responses,
        anomalies=[
            AnomalyResponse(
                id=a.id,
                algorithm=a.algorithm,
                anomaly_score=a.anomaly_score,
                rank=a.rank,
                feature_contributions=a.feature_contributions,
                created_at=a.created_at,
            ) for a in anomalies
        ],
        clusters=[
            ClusterResponse(
                id=c.id,
                algorithm=c.algorithm,
                cluster_id=c.cluster_id,
                distance_to_centroid=c.distance_to_centroid,
                pca_x=c.pca_x,
                pca_y=c.pca_y,
                created_at=c.created_at,
            ) for c in clusters
        ],
        created_at=obj.created_at,
    )
