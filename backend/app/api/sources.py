"""
ANVESHAK — Sources API
Endpoints for managing and monitoring astronomical data sources.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.source import SourceListResponse, SourceStatus
from app.services.source_service import SourceService

router = APIRouter()


@router.get("", response_model=SourceListResponse)
async def list_sources(db: AsyncSession = Depends(get_db)):
    """Get all configured data sources and their status."""
    service = SourceService(db)
    sources = await service.get_all_sources()
    return {"sources": sources}


@router.get("/{source_id}", response_model=SourceStatus)
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific data source."""
    service = SourceService(db)
    source = await service.get_source(source_id)
    
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
    return source


@router.post("/{source_id}/health")
async def check_source_health(source_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger a health check for a specific source adapter."""
    service = SourceService(db)
    result = await service.check_source_health(source_id)
    
    if not result.get("healthy"):
        raise HTTPException(status_code=503, detail=result.get("message"))
        
    return result
