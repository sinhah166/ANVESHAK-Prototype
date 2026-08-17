"""
ANVESHAK — Pipeline Service
Orchestrates the entire data pipeline: ingestion -> preprocessing -> detection -> classification -> storage.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from app.adapters.base import get_adapter
from app.core.logging import get_logger
from app.ml.inference import classify_radio_candidate, classify_transit_candidate
from app.models.candidate import Candidate, RadioFeature, TransitFeature
from app.models.observation import Observation
from app.processing.feature_extraction import (
    extract_radio_features_schema,
    extract_transit_features,
)
from app.processing.preprocessing import preprocess_lightcurve
from app.processing.radio_processing import process_spectrogram
from app.processing.transit_detection import detect_transits
from app.queue.producer import publish_candidate, publish_observation
from app.schemas.observation import ObservationCreate
from app.services.source_service import SourceService

logger = get_logger("service.pipeline")

# Simple in-memory tracker for pipeline stages
_pipeline_status = {
    "is_running": False,
    "current_mode": "demo",
    "stages": {
        "ingestion": {"status": "idle", "processed_count": 0, "error_count": 0, "last_run": None, "last_error": None},
        "preprocessing": {"status": "idle", "processed_count": 0, "error_count": 0, "last_run": None, "last_error": None},
        "detection": {"status": "idle", "processed_count": 0, "error_count": 0, "last_run": None, "last_error": None},
        "classification": {"status": "idle", "processed_count": 0, "error_count": 0, "last_run": None, "last_error": None},
        "normalization": {"status": "idle", "processed_count": 0, "error_count": 0, "last_run": None, "last_error": None},
        "database": {"status": "idle", "processed_count": 0, "error_count": 0, "last_run": None, "last_error": None},
    }
}


def update_stage_status(stage: str, status: str = None, success: bool = None, error: str = None):
    """Update pipeline stage monitoring metrics."""
    if stage in _pipeline_status["stages"]:
        now = datetime.now(timezone.utc)
        if status:
            _pipeline_status["stages"][stage]["status"] = status
        if success is True:
            _pipeline_status["stages"][stage]["processed_count"] += 1
            _pipeline_status["stages"][stage]["last_run"] = now
        elif success is False:
            _pipeline_status["stages"][stage]["error_count"] += 1
            _pipeline_status["stages"][stage]["last_error"] = error
            _pipeline_status["stages"][stage]["last_run"] = now


class PipelineService:
    """Orchestrates the data processing pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.source_service = SourceService(db)

    async def get_pipeline_status(self) -> dict[str, Any]:
        """Get the current pipeline monitoring status."""
        return _pipeline_status

    async def run_pipeline(self, source_id: str, mode: str = "demo") -> dict[str, Any]:
        """
        Run the full pipeline for a specific source.
        
        Args:
            source_id: Source configuration ID.
            mode: 'demo' or 'archive'.
        """
        _pipeline_status["is_running"] = True
        _pipeline_status["current_mode"] = mode
        
        try:
            source = await self.source_service.get_source(source_id)
            if not source or not source.enabled:
                return {"status": "error", "message": f"Source {source_id} not found or disabled"}

            # INGESTION & NORMALIZATION
            update_stage_status("ingestion", status="running")
            adapter = get_adapter(source.adapter, source_id)
            
            # Fetch and normalize to ObservationCreate objects
            observations = await adapter.fetch_and_normalize(mode=mode)
            
            if not observations:
                update_stage_status("ingestion", status="completed")
                return {"status": "success", "message": "No new data", "processed": 0}
                
            update_stage_status("ingestion", status="completed", success=True)
            
            # Update source stats
            await self.source_service.update_observation_count(source_id, len(observations))
            
            processed_count = 0
            for obs in observations:
                await self.process_observation(obs)
                processed_count += 1
                
            return {"status": "success", "message": f"Processed {processed_count} observations", "processed": processed_count}
            
        except Exception as e:
            logger.error("pipeline_run_failed", source=source_id, error=str(e))
            return {"status": "error", "message": str(e)}
        finally:
            _pipeline_status["is_running"] = False
            for stage in _pipeline_status["stages"]:
                if _pipeline_status["stages"][stage]["status"] == "running":
                    _pipeline_status["stages"][stage]["status"] = "idle"

    async def run_demo_sequence(self) -> None:
        """
        Run a staggered demo sequence spanning both light curve and radio data.
        This provides a good real-time UI demonstration.
        """
        if _pipeline_status["is_running"]:
            logger.warning("pipeline_already_running")
            return
            
        _pipeline_status["is_running"] = True
        _pipeline_status["current_mode"] = "demo"
        
        try:
            # Get TESS and Radio Demo adapters
            tess_adapter = get_adapter("tess", "tess")
            radio_adapter = get_adapter("radio_demo", "radio_demo")
            
            # Fetch a few demo observations
            tess_obs = await tess_adapter.fetch_and_normalize()
            radio_obs = await radio_adapter.fetch_and_normalize()
            
            all_obs = tess_obs + radio_obs
            
            # Process them one by one with a delay to simulate real-time data streaming
            for i, obs in enumerate(all_obs):
                logger.info(f"Demo processing {i+1}/{len(all_obs)}: {obs.source_id}")
                await self.process_observation(obs)
                
                # Small delay to let UI show the update
                if i < len(all_obs) - 1:
                    await asyncio.sleep(2.0)
                    
        except Exception as e:
            logger.error("demo_sequence_failed", error=str(e))
        finally:
            _pipeline_status["is_running"] = False
            for stage in _pipeline_status["stages"]:
                _pipeline_status["stages"][stage]["status"] = "idle"

    async def process_observation(self, obs_data: ObservationCreate) -> None:
        """
        Process a single normalized observation through the scientific pipeline.
        Saves it to the DB and publishes events.
        """
        # Save observation to DB
        update_stage_status("database", status="running")
        try:
            db_obs = Observation(
                source_id=obs_data.source_id,
                record_id=obs_data.record_id,
                observed_at=obs_data.observed_at,
                target_name=obs_data.target.name,
                ra=obs_data.target.ra,
                dec=obs_data.target.dec,
                signal_type=obs_data.signal_type,
                raw_payload=obs_data.raw_payload,
                confidence=obs_data.preliminary_confidence,
                metadata_=obs_data.metadata
            )
            self.db.add(db_obs)
            await self.db.commit()
            await self.db.refresh(db_obs)
            
            # Publish event
            await publish_observation(db_obs.id, db_obs.source_id)
            update_stage_status("database", status="completed", success=True)
        except Exception as e:
            await self.db.rollback()
            logger.error("save_observation_failed", error=str(e))
            update_stage_status("database", status="error", success=False, error=str(e))
            return

        # Route to appropriate processing branch
        if obs_data.signal_type in ["transit", "stellar_variability", "noise", "lightcurve"]:
            await self._process_lightcurve_branch(db_obs, obs_data)
        elif obs_data.signal_type.startswith("radio"):
            await self._process_radio_branch(db_obs, obs_data)
        else:
            logger.warning("unknown_signal_type_skipped", type=obs_data.signal_type)

    async def _process_lightcurve_branch(self, db_obs: Observation, obs_data: ObservationCreate) -> None:
        """Process light curve data (preprocessing + transit detection + ML)."""
        payload = obs_data.raw_payload
        if "time" not in payload or "flux" not in payload:
            return

        time = np.array(payload["time"])
        flux = np.array(payload["flux"])
        
        # 1. PREPROCESSING
        update_stage_status("preprocessing", status="running")
        try:
            processed = preprocess_lightcurve(time, flux)
            p_time = np.array(processed["processed_time"])
            p_flux = np.array(processed["processed_flux"])
            flux_std = processed["metadata"].get("flux_std", 0.001)
            update_stage_status("preprocessing", status="completed", success=True)
        except Exception as e:
            logger.error("preprocessing_failed", error=str(e))
            update_stage_status("preprocessing", status="error", success=False, error=str(e))
            return

        # 2. DETECTION
        update_stage_status("detection", status="running")
        try:
            detections = detect_transits(p_time, p_flux)
            update_stage_status("detection", status="completed", success=True)
        except Exception as e:
            logger.error("transit_detection_failed", error=str(e))
            update_stage_status("detection", status="error", success=False, error=str(e))
            return

        # 3. CLASSIFICATION & DB SAVE
        update_stage_status("classification", status="running")
        
        for det in detections:
            try:
                # Build feature schema
                features = extract_transit_features(det)
                
                # Classify
                ml_result = classify_transit_candidate(features, flux_std)
                
                # Save candidate
                cand = Candidate(
                    observation_id=db_obs.id,
                    candidate_type="transit",
                    classification=ml_result["classification"],
                    confidence=ml_result["confidence"],
                    model_name=ml_result["model_name"],
                    metadata_={
                        "folded_phase": det.get("folded_phase"),
                        "folded_flux": det.get("folded_flux"),
                        "method": det.get("method")
                    }
                )
                self.db.add(cand)
                await self.db.commit()
                await self.db.refresh(cand)
                
                # Save features
                tf = TransitFeature(
                    candidate_id=cand.id,
                    **{k: v for k, v in features.model_dump().items() if v is not None}
                )
                self.db.add(tf)
                await self.db.commit()
                
                update_stage_status("classification", success=True)
                
                # Publish event
                await publish_candidate(cand.id, cand.classification, cand.confidence)
                
            except Exception as e:
                await self.db.rollback()
                logger.error("candidate_save_failed", error=str(e))
                update_stage_status("classification", success=False, error=str(e))
                
        update_stage_status("classification", status="idle")

    async def _process_radio_branch(self, db_obs: Observation, obs_data: ObservationCreate) -> None:
        """Process radio spectrogram data."""
        payload = obs_data.raw_payload
        if "spectrogram" not in payload:
            return

        spec = np.array(payload["spectrogram"])
        freqs = np.array(payload.get("frequencies_mhz", []))
        times = np.array(payload.get("times_seconds", []))
        
        # Combined Preprocessing/Detection
        update_stage_status("preprocessing", status="running")
        update_stage_status("detection", status="running")
        try:
            candidates = process_spectrogram(spec, freqs, times)
            update_stage_status("preprocessing", status="completed", success=True)
            update_stage_status("detection", status="completed", success=True)
        except Exception as e:
            logger.error("radio_processing_failed", error=str(e))
            update_stage_status("preprocessing", status="error", success=False, error=str(e))
            update_stage_status("detection", status="error", success=False, error=str(e))
            return

        # Classification & Save
        update_stage_status("classification", status="running")
        
        for cand in candidates:
            try:
                features = extract_radio_features_schema(cand)
                ml_result = classify_radio_candidate(cand)
                
                db_cand = Candidate(
                    observation_id=db_obs.id,
                    candidate_type="radio_signal",
                    classification=ml_result["classification"],
                    confidence=ml_result["confidence"],
                    model_name=ml_result["model_name"]
                )
                self.db.add(db_cand)
                await self.db.commit()
                await self.db.refresh(db_cand)
                
                rf = RadioFeature(
                    candidate_id=db_cand.id,
                    **{k: v for k, v in features.model_dump().items() if v is not None}
                )
                self.db.add(rf)
                await self.db.commit()
                
                update_stage_status("classification", success=True)
                
                # Publish event
                await publish_candidate(db_cand.id, db_cand.classification, db_cand.confidence)
                
            except Exception as e:
                await self.db.rollback()
                logger.error("radio_candidate_save_failed", error=str(e))
                update_stage_status("classification", success=False, error=str(e))
                
        update_stage_status("classification", status="idle")
