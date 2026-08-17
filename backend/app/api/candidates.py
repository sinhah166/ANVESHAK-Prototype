"""
ANVESHAK — Candidates API
Endpoints for fetching and filtering detected candidates.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.candidate import CandidateDetail, CandidateListResponse
from app.services.candidate_service import CandidateService

router = APIRouter()


@router.get("", response_model=CandidateListResponse)
async def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    source_id: Optional[str] = None,
    signal_type: Optional[str] = None,
    classification: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of candidates with optional filtering."""
    service = CandidateService(db)
    
    candidates, total = await service.get_candidates(
        skip=skip,
        limit=limit,
        source_id=source_id,
        signal_type=signal_type,
        classification=classification,
        min_confidence=min_confidence
    )
    
    return {
        "items": candidates,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit
    }


@router.get("/{candidate_id}", response_model=CandidateDetail)
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get full details for a single candidate, including chart data."""
    service = CandidateService(db)
    candidate = await service.get_candidate_detail(candidate_id)
    
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        
    return candidate
