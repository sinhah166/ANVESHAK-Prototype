"""
ANVESHAK — Observations API
Endpoints for querying raw normalized observations.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.observation import Observation
from app.schemas.observation import ObservationDetail, ObservationListResponse, ObservationResponse

router = APIRouter()


@router.get("", response_model=ObservationListResponse)
async def list_observations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    source_id: Optional[str] = None,
    signal_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of normalized observations."""
    stmt = select(Observation)
    
    if source_id:
        stmt = stmt.where(Observation.source_id == source_id)
    if signal_type:
        stmt = stmt.where(Observation.signal_type == signal_type)
        
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Get items
    stmt = stmt.order_by(desc(Observation.observed_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    observations = result.scalars().all()
    
    return {
        "items": [obs.to_dict() for obs in observations],
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit
    }


@router.get("/{observation_id}", response_model=ObservationDetail)
async def get_observation(
    observation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get full details for a raw observation including chart data arrays."""
    stmt = select(Observation).where(Observation.id == observation_id)
    result = await db.execute(stmt)
    observation = result.scalar_one_or_none()
    
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
        
    obs_dict = observation.to_dict()
    
    # Add chart data appropriately
    payload = observation.raw_payload or {}
    
    if observation.signal_type in ["transit", "stellar_variability", "noise"]:
        if "time" in payload and "flux" in payload:
            obs_dict["light_curve_data"] = {
                "time": payload["time"],
                "flux": payload["flux"]
            }
            
    elif observation.signal_type.startswith("radio"):
        if "spectrogram" in payload:
            obs_dict["spectrogram_data"] = {
                "spectrogram": payload["spectrogram"],
                "frequencies": payload.get("frequencies_mhz", []),
                "times": payload.get("times_seconds", [])
            }
            
    return obs_dict
