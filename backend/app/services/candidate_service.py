"""
ANVESHAK — Candidate Service
CRUD operations and aggregation for detected candidates.
"""

from typing import Any, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.candidate import Candidate, RadioFeature, TransitFeature
from app.models.observation import Observation
from app.schemas.candidate import CandidateCreate, CandidateDetail, CandidateResponse

logger = get_logger("service.candidate")


class CandidateService:
    """Service for managing astronomical candidates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_candidates(
        self, 
        skip: int = 0, 
        limit: int = 50,
        source_id: Optional[str] = None,
        signal_type: Optional[str] = None,
        classification: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> tuple[list[CandidateResponse], int]:
        """
        Get a paginated list of candidates with optional filtering.
        Includes joined observation data.
        """
        # Base query joined with Observation
        stmt = select(Candidate, Observation).join(
            Observation, Candidate.observation_id == Observation.id
        )
        
        # Apply filters
        if source_id:
            stmt = stmt.where(Observation.source_id == source_id)
        if signal_type:
            stmt = stmt.where(Observation.signal_type == signal_type)
        if classification:
            stmt = stmt.where(Candidate.classification == classification)
        if min_confidence is not None:
            stmt = stmt.where(Candidate.confidence >= min_confidence)
            
        # Count total matches
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Get paginated results
        stmt = stmt.order_by(desc(Candidate.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        
        candidates = []
        for candidate, observation in result.all():
            cand_dict = candidate.to_dict()
            cand_dict.update({
                "source_id": observation.source_id,
                "record_id": observation.record_id,
                "target_name": observation.target_name,
                "ra": observation.ra,
                "dec": observation.dec,
                "signal_type": observation.signal_type,
                "observed_at": observation.observed_at,
            })
            candidates.append(CandidateResponse(**cand_dict))
            
        return candidates, total

    async def get_candidate_detail(self, candidate_id: int) -> Optional[CandidateDetail]:
        """Get full details for a candidate including features and raw data."""
        stmt = select(Candidate, Observation).join(
            Observation, Candidate.observation_id == Observation.id
        ).where(Candidate.id == candidate_id).options(
            selectinload(Candidate.transit_features),
            selectinload(Candidate.radio_features)
        )
        
        result = await self.db.execute(stmt)
        row = result.first()
        
        if not row:
            return None
            
        candidate, observation = row
        
        # Build response dictionary
        cand_dict = candidate.to_dict()
        cand_dict.update({
            "source_id": observation.source_id,
            "record_id": observation.record_id,
            "target_name": observation.target_name,
            "ra": observation.ra,
            "dec": observation.dec,
            "signal_type": observation.signal_type,
            "observed_at": observation.observed_at,
        })
        
        # Add features if they exist
        if candidate.transit_features:
            cand_dict["transit_features"] = {
                k: v for k, v in candidate.transit_features.__dict__.items() 
                if not k.startswith("_") and k not in ["id", "candidate_id"]
            }
            
        if candidate.radio_features:
            cand_dict["radio_features"] = {
                k: v for k, v in candidate.radio_features.__dict__.items() 
                if not k.startswith("_") and k not in ["id", "candidate_id"]
            }
            
        # Add chart data based on signal type
        if observation.signal_type == "transit":
            # Extract light curve data
            if isinstance(observation.raw_payload, dict):
                cand_dict["light_curve_data"] = {
                    "time": observation.raw_payload.get("time", []),
                    "flux": observation.raw_payload.get("flux", []),
                }
            
            # Extract phase-folded data from metadata if available
            if isinstance(candidate.metadata_, dict) and "folded_phase" in candidate.metadata_:
                cand_dict["phase_folded_data"] = {
                    "phase": candidate.metadata_["folded_phase"],
                    "flux": candidate.metadata_.get("folded_flux", []),
                }
                
        elif observation.signal_type.startswith("radio"):
            # Extract spectrogram data
            if isinstance(observation.raw_payload, dict):
                cand_dict["spectrogram_data"] = {
                    "spectrogram": observation.raw_payload.get("spectrogram", []),
                    "frequencies": observation.raw_payload.get("frequencies_mhz", []),
                    "times": observation.raw_payload.get("times_seconds", []),
                }

        return CandidateDetail(**cand_dict)

    async def get_statistics(self) -> dict[str, Any]:
        """Aggregate statistics for the dashboard."""
        # Total counts
        total_obs = await self.db.scalar(select(func.count(Observation.id)))
        total_cand = await self.db.scalar(select(func.count(Candidate.id)))
        high_conf = await self.db.scalar(
            select(func.count(Candidate.id)).where(Candidate.confidence >= 0.8)
        )
        
        # Classification distribution
        class_dist_result = await self.db.execute(
            select(Candidate.classification, func.count(Candidate.id))
            .group_by(Candidate.classification)
        )
        class_dist = {row[0]: row[1] for row in class_dist_result.all()}
        
        # Signal type distribution
        signal_dist_result = await self.db.execute(
            select(Observation.signal_type, func.count(Observation.id))
            .group_by(Observation.signal_type)
        )
        signal_dist = {row[0]: row[1] for row in signal_dist_result.all()}
        
        # Source distribution
        source_dist_result = await self.db.execute(
            select(Observation.source_id, func.count(Observation.id))
            .group_by(Observation.source_id)
        )
        source_dist = {row[0]: row[1] for row in source_dist_result.all()}
        
        # Recent activity (latest 5 candidates)
        recent = await self.db.execute(
            select(Candidate, Observation)
            .join(Observation, Candidate.observation_id == Observation.id)
            .order_by(desc(Candidate.created_at))
            .limit(5)
        )
        
        recent_activity = [
            {
                "id": c.id,
                "classification": c.classification,
                "source": o.source_id,
                "target": o.target_name,
                "time": c.created_at.isoformat() if c.created_at else None,
                "confidence": c.confidence
            }
            for c, o in recent.all()
        ]
        
        return {
            "total_observations": total_obs or 0,
            "total_candidates": total_cand or 0,
            "high_confidence_candidates": high_conf or 0,
            "classification_distribution": class_dist,
            "signal_type_distribution": signal_dist,
            "source_distribution": source_dist,
            "recent_activity": recent_activity
        }
