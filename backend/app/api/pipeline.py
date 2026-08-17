"""
ANVESHAK — Pipeline API
Endpoints for triggering pipeline runs and fetching stats.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.source import PipelineStatusResponse, StatsResponse
from app.services.candidate_service import CandidateService
from app.services.pipeline_service import PipelineService, get_logger

logger = get_logger("api.pipeline")
router = APIRouter()


@router.post("/run/{source_id}")
async def run_pipeline(
    source_id: str,
    background_tasks: BackgroundTasks,
    mode: str = "demo",
    db: AsyncSession = Depends(get_db)
):
    """Trigger a pipeline run for a specific source."""
    service = PipelineService(db)
    
    # Check if already running
    status = await service.get_pipeline_status()
    if status["is_running"]:
        raise HTTPException(status_code=409, detail="Pipeline is already running")
        
    # Start in background
    background_tasks.add_task(service.run_pipeline, source_id, mode)
    
    return {"status": "accepted", "message": f"Pipeline run started for {source_id}"}


@router.post("/demo")
async def run_demo_pipeline(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger the visual demo pipeline sequence.
    This generates simulated real-time data across multiple sources.
    """
    service = PipelineService(db)
    
    status = await service.get_pipeline_status()
    if status["is_running"]:
        raise HTTPException(status_code=409, detail="Pipeline is already running")
        
    # Start sequence in background
    background_tasks.add_task(service.run_demo_sequence)
    
    return {"status": "accepted", "message": "Demo sequence started"}


@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(db: AsyncSession = Depends(get_db)):
    """Get real-time status of all pipeline stages."""
    service = PipelineService(db)
    status_dict = await service.get_pipeline_status()
    
    # Format for response model
    stages = []
    for stage_name, stage_data in status_dict["stages"].items():
        stages.append({
            "stage": stage_name,
            "status": stage_data["status"],
            "last_run": stage_data["last_run"],
            "processed_count": stage_data["processed_count"],
            "error_count": stage_data["error_count"],
            "last_error": stage_data["last_error"],
        })
        
    return {
        "stages": stages,
        "is_running": status_dict["is_running"],
        "current_mode": status_dict["current_mode"]
    }


@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregated statistics for the dashboard overview."""
    service = CandidateService(db)
    stats = await service.get_statistics()
    return stats
