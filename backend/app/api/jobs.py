"""
ANVESHAK — Jobs & Ingestion API
Endpoints for triggering data ingestion and monitoring background jobs.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, get_session_factory
from app.models.db_models import AnalysisJob, Dataset, Source
from app.schemas.schemas import IngestionRequest, JobListResponse, JobResponse
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("api.jobs")
router = APIRouter()


async def _run_ingestion_job(job_id: int, table: str, max_records: int, filters: Optional[dict]):
    """Background task to run an ingestion job."""
    from app.services.ingestion import IngestionService

    factory = get_session_factory()
    async with factory() as db:
        try:
            # Update job status
            result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.status = "running"
                job.progress = 5.0
                await db.commit()

            service = IngestionService(db)
            where = None
            if filters:
                conditions = []
                for k, v in filters.items():
                    conditions.append(f"{k} = '{v}'")
                where = " AND ".join(conditions) if conditions else None

            result = await service.ingest_dataset(
                table=table,
                max_records=max_records,
                where=where,
                job_id=job_id,
            )

            # Update job with results
            job_result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
            job = job_result.scalar_one_or_none()
            if job:
                job.status = "completed"
                job.progress = 100.0
                job.completed_at = datetime.now(timezone.utc)
                job.result_summary = result
                await db.commit()

            logger.info("ingestion_job_completed", job_id=job_id, result=result)

        except Exception as e:
            logger.error("ingestion_job_failed", job_id=job_id, error=str(e))
            try:
                err_result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
                job = err_result.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)[:500]
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
            except Exception:
                pass


async def _run_ml_pipeline_job(job_id: int, dataset_id: int):
    """Background task to run ML pipeline (feature engineering + classifier + anomaly + clustering)."""
    from app.services.feature_engineering import FeatureEngineeringService
    from app.services.ingestion import IngestionService
    from app.ml.classifier import ExoplanetClassifier
    from app.ml.anomaly import AnomalyDetector
    from app.ml.clustering import ClusteringEngine
    from app.ml.registry import ModelRegistry

    factory = get_session_factory()
    async with factory() as db:
        try:
            # Update status
            job_r = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
            job = job_r.scalar_one_or_none()
            if job:
                job.status = "running"
                job.progress = 5.0
                await db.commit()

            # 1. Feature Engineering
            fe_service = FeatureEngineeringService(db)
            fe_result = await fe_service.generate_features_for_dataset(dataset_id)

            if job:
                job.progress = 30.0
                await db.commit()

            # 2. Build feature DataFrame
            from app.models.db_models import AstronomicalObject, PlanetParameter, StellarParameter
            obj_query = (
                select(
                    AstronomicalObject.id,
                    AstronomicalObject.name,
                    AstronomicalObject.object_type,
                    PlanetParameter.orbital_period_days,
                    PlanetParameter.planet_radius_earth,
                    PlanetParameter.planet_mass_earth,
                    PlanetParameter.semi_major_axis_au,
                    PlanetParameter.eccentricity,
                    PlanetParameter.equilibrium_temp_k,
                    StellarParameter.effective_temp_k,
                    StellarParameter.stellar_radius_solar,
                    StellarParameter.stellar_mass_solar,
                )
                .join(PlanetParameter, PlanetParameter.object_id == AstronomicalObject.id, isouter=True)
                .join(StellarParameter, StellarParameter.object_id == AstronomicalObject.id, isouter=True)
                .where(AstronomicalObject.dataset_id == dataset_id)
            )
            result = await db.execute(obj_query)
            rows = result.all()

            import pandas as pd
            df = pd.DataFrame(rows, columns=[
                "id", "name", "object_type",
                "orbital_period_days", "planet_radius_earth", "planet_mass_earth",
                "semi_major_axis_au", "eccentricity", "equilibrium_temp_k",
                "effective_temp_k", "stellar_radius_solar", "stellar_mass_solar",
            ])

            if len(df) < 10:
                raise ValueError("Insufficient data for ML analysis")

            # 3. Anomaly Detection
            detector = AnomalyDetector()
            anomaly_features = [c for c in [
                "orbital_period_days", "planet_radius_earth", "planet_mass_earth",
                "equilibrium_temp_k", "effective_temp_k", "stellar_radius_solar",
            ] if c in df.columns and df[c].notna().sum() > 10]

            if len(anomaly_features) >= 2:
                detector.fit(df, feature_names=anomaly_features)
                anomaly_results = detector.predict(df)
                detector.save(version="v1")

                # Save anomaly results to DB
                from app.models.db_models import Anomaly
                for idx, row in anomaly_results.iterrows():
                    anom = Anomaly(
                        object_id=int(df.iloc[idx]["id"]),
                        algorithm="IsolationForest",
                        anomaly_score=float(row["anomaly_score"]),
                        rank=int(row["anomaly_rank"]),
                    )
                    db.add(anom)

                await db.commit()

            if job:
                job.progress = 60.0
                await db.commit()

            # 4. Clustering
            clustering = ClusteringEngine()
            cluster_features = [c for c in [
                "orbital_period_days", "planet_radius_earth",
                "equilibrium_temp_k", "effective_temp_k",
                "stellar_radius_solar", "stellar_mass_solar",
            ] if c in df.columns and df[c].notna().sum() > 10]

            if len(cluster_features) >= 2:
                cluster_results = clustering.fit_predict(df, feature_names=cluster_features)
                clustering.save(version="v1")

                # Save cluster results to DB
                from app.models.db_models import Cluster
                for idx, row in cluster_results.iterrows():
                    cl = Cluster(
                        object_id=int(df.iloc[idx]["id"]),
                        algorithm="KMeans",
                        cluster_id=int(row["cluster_id"]),
                        distance_to_centroid=float(row["distance_to_centroid"]),
                        pca_x=float(row["pca_x"]),
                        pca_y=float(row["pca_y"]),
                    )
                    db.add(cl)

                await db.commit()

            if job:
                job.progress = 80.0
                await db.commit()

            # 5. Update job
            job_r2 = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
            job = job_r2.scalar_one_or_none()
            if job:
                job.status = "completed"
                job.progress = 100.0
                job.completed_at = datetime.now(timezone.utc)
                job.result_summary = {
                    "features_generated": fe_result,
                    "anomalies_detected": len(df) if anomaly_features else 0,
                    "clusters_created": clustering.n_clusters if cluster_features else 0,
                }
                await db.commit()

        except Exception as e:
            logger.error("ml_pipeline_failed", job_id=job_id, error=str(e))
            try:
                err_r = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
                job = err_r.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)[:500]
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
            except Exception:
                pass


@router.post("/ingestion/sync")
async def start_ingestion(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a data ingestion job."""
    job = AnalysisJob(
        job_type="ingestion",
        status="queued",
        progress=0.0,
        parameters={
            "source": request.source,
            "dataset": request.dataset,
            "max_records": request.max_records,
            "filters": request.filters,
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(
        _run_ingestion_job,
        job.id,
        request.dataset,
        request.max_records,
        request.filters,
    )

    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status="queued",
        progress=0.0,
        parameters=job.parameters,
        created_at=job.created_at,
    )


@router.post("/ml/run")
async def start_ml_pipeline(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start the ML analysis pipeline (features + anomaly + clustering)."""
    # Verify dataset exists
    ds_result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    if not ds_result.scalar_one_or_none():
        raise HTTPException(404, "Dataset not found")

    job = AnalysisJob(
        job_type="ml_pipeline",
        status="queued",
        progress=0.0,
        parameters={"dataset_id": dataset_id},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(_run_ml_pipeline_job, job.id, dataset_id)

    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status="queued",
        progress=0.0,
        parameters=job.parameters,
        created_at=job.created_at,
    )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List background jobs."""
    query = select(AnalysisJob).order_by(desc(AnalysisJob.created_at))
    if status:
        query = query.where(AnalysisJob.status == status)
    query = query.limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[
            JobResponse(
                id=j.id,
                job_type=j.job_type,
                status=j.status,
                progress=j.progress or 0.0,
                parameters=j.parameters,
                result_summary=j.result_summary,
                error_message=j.error_message,
                created_at=j.created_at,
                completed_at=j.completed_at,
            )
            for j in jobs
        ],
        total=len(jobs),
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get job status."""
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    j = result.scalar_one_or_none()
    if not j:
        raise HTTPException(404, "Job not found")

    return JobResponse(
        id=j.id,
        job_type=j.job_type,
        status=j.status,
        progress=j.progress or 0.0,
        parameters=j.parameters,
        result_summary=j.result_summary,
        error_message=j.error_message,
        created_at=j.created_at,
        completed_at=j.completed_at,
    )


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db)):
    """List registered data sources with dataset counts."""
    result = await db.execute(select(Source).order_by(Source.created_at))
    sources = result.scalars().all()

    source_list = []
    for s in sources:
        ds_result = await db.execute(select(Dataset).where(Dataset.source_id == s.id))
        datasets = ds_result.scalars().all()
        source_list.append({
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "description": s.description,
            "base_url": s.base_url,
            "active": s.active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "dataset_count": len(datasets),
            "total_records": sum(d.record_count or 0 for d in datasets),
            "datasets": [
                {
                    "id": d.id,
                    "name": d.name,
                    "source_table": d.source_table,
                    "record_count": d.record_count or 0,
                    "ingestion_status": d.ingestion_status,
                    "ingestion_completed_at": d.ingestion_completed_at.isoformat() if d.ingestion_completed_at else None,
                }
                for d in datasets
            ],
        })

    return {"sources": source_list, "total": len(source_list)}


@router.get("/dashboard/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    from sqlalchemy import func as sqlfunc

    settings = get_settings()

    # Count objects by type
    type_counts = await db.execute(
        select(AstronomicalObject.object_type, sqlfunc.count())
        .group_by(AstronomicalObject.object_type)
    )
    type_dist = {row[0]: row[1] for row in type_counts.all()}

    # Discovery method distribution
    method_counts = await db.execute(
        select(PlanetParameter.discovery_method, sqlfunc.count())
        .where(PlanetParameter.discovery_method.isnot(None))
        .group_by(PlanetParameter.discovery_method)
    )
    method_dist = {row[0]: row[1] for row in method_counts.all()}

    # Total counts
    total_objects = sum(type_dist.values())
    total_datasets = (await db.execute(select(sqlfunc.count()).select_from(Dataset))).scalar() or 0
    total_anomalies = (await db.execute(
        select(sqlfunc.count()).select_from(Anomaly)
    )).scalar() or 0

    # Last sync
    last_ds = await db.execute(
        select(Dataset.ingestion_completed_at)
        .where(Dataset.ingestion_status == "completed")
        .order_by(desc(Dataset.ingestion_completed_at))
        .limit(1)
    )
    last_sync_row = last_ds.scalar_one_or_none()

    # Latest model
    latest_model = await db.execute(
        select(ModelVersion.version)
        .order_by(desc(ModelVersion.created_at))
        .limit(1)
    )
    latest_model_version = latest_model.scalar_one_or_none()

    return {
        "total_datasets": total_datasets,
        "total_objects": total_objects,
        "total_confirmed": type_dist.get("confirmed", 0),
        "total_candidates": type_dist.get("candidate", 0),
        "total_false_positives": type_dist.get("false_positive", 0),
        "total_anomalies": total_anomalies,
        "high_priority_count": 0,
        "last_sync": last_sync_row.isoformat() if last_sync_row else None,
        "latest_model_version": latest_model_version,
        "data_mode": settings.data_mode,
        "discovery_method_distribution": method_dist,
        "object_type_distribution": type_dist,
    }
