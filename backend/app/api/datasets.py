"""
ANVESHAK — Datasets API
Endpoints for listing and inspecting ingested datasets.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.db_models import Dataset, Source
from app.schemas.schemas import DatasetListResponse, DatasetResponse

router = APIRouter()


@router.get("/", response_model=DatasetListResponse)
async def list_datasets(db: AsyncSession = Depends(get_db)):
    """List all ingested datasets."""
    result = await db.execute(
        select(Dataset).order_by(Dataset.created_at.desc())
    )
    datasets = result.scalars().all()
    return DatasetListResponse(
        datasets=[
            DatasetResponse(
                id=d.id,
                source_id=d.source_id,
                name=d.name,
                source_table=d.source_table,
                version=d.version,
                record_count=d.record_count or 0,
                query_used=d.query_used,
                ingestion_status=d.ingestion_status,
                ingestion_started_at=d.ingestion_started_at,
                ingestion_completed_at=d.ingestion_completed_at,
                error_message=d.error_message,
                created_at=d.created_at,
            )
            for d in datasets
        ],
        total=len(datasets),
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """Get dataset details by ID."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse(
        id=d.id,
        source_id=d.source_id,
        name=d.name,
        source_table=d.source_table,
        version=d.version,
        record_count=d.record_count or 0,
        query_used=d.query_used,
        ingestion_status=d.ingestion_status,
        ingestion_started_at=d.ingestion_started_at,
        ingestion_completed_at=d.ingestion_completed_at,
        error_message=d.error_message,
        created_at=d.created_at,
    )
