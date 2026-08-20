"""
ANVESHAK — Candidate Ranking Service
Transparent Research Priority Score combining multiple signals.

This is a "Research Priority Score" — NOT a "planet confirmation score".
It indicates which candidates may be worth further investigation.
"""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.db_models import (
    Anomaly,
    AstronomicalObject,
    EngineeredFeature,
    MLPrediction,
)

logger = get_logger("service.ranking")

# Scoring weights (transparent and documented)
SCORING_WEIGHTS = {
    "classifier_confidence": 0.30,
    "anomaly_score": 0.20,
    "completeness": 0.20,
    "physical_consistency": 0.15,
    "multi_signal": 0.15,
}


class RankingService:
    """
    Computes Research Priority Scores for astronomical objects.

    The score combines:
    - Classifier confidence (30%)
    - Anomaly score (20%)
    - Data completeness (20%)
    - Physical consistency (15%)
    - Multi-signal bonus (15%)

    Score range: 0.0 to 1.0 (higher = higher research priority)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_priority_score(self, object_id: int) -> float:
        """Compute the Research Priority Score for a single object."""
        scores = {}

        # 1. Classifier confidence
        pred_result = await self.db.execute(
            select(MLPrediction)
            .where(MLPrediction.object_id == object_id)
            .order_by(MLPrediction.created_at.desc())
            .limit(1)
        )
        prediction = pred_result.scalar_one_or_none()
        if prediction:
            # Higher confidence in "CANDIDATE" or "CONFIRMED" is more interesting
            if prediction.predicted_class in ("CANDIDATE", "CONFIRMED"):
                scores["classifier_confidence"] = prediction.confidence
            else:
                scores["classifier_confidence"] = 1.0 - prediction.confidence
        else:
            scores["classifier_confidence"] = 0.5  # Neutral

        # 2. Anomaly score
        anom_result = await self.db.execute(
            select(Anomaly)
            .where(Anomaly.object_id == object_id)
            .order_by(Anomaly.created_at.desc())
            .limit(1)
        )
        anomaly = anom_result.scalar_one_or_none()
        if anomaly:
            # More anomalous = higher priority
            # anomaly_score from IsolationForest: more negative = more anomalous
            # We use normalized_score which is already 0-1
            scores["anomaly_score"] = max(0, min(1, -anomaly.anomaly_score + 0.5))
        else:
            scores["anomaly_score"] = 0.5

        # 3. Completeness score
        feat_result = await self.db.execute(
            select(EngineeredFeature)
            .where(
                EngineeredFeature.object_id == object_id,
                EngineeredFeature.feature_name == "completeness_score",
            )
        )
        completeness_feat = feat_result.scalar_one_or_none()
        scores["completeness"] = completeness_feat.feature_value if completeness_feat else 0.3

        # 4. Physical consistency (check if derived features are reasonable)
        feat_results = await self.db.execute(
            select(EngineeredFeature)
            .where(EngineeredFeature.object_id == object_id)
        )
        features = {f.feature_name: f.feature_value for f in feat_results.scalars().all()}

        consistency = 0.5
        checks = 0
        passes = 0

        if "density_estimate" in features:
            checks += 1
            if 0.1 < features["density_estimate"] < 30:
                passes += 1

        if "surface_gravity_planet" in features:
            checks += 1
            if 0.01 < features["surface_gravity_planet"] < 100:
                passes += 1

        if "stellar_planet_radius_ratio" in features:
            checks += 1
            if features["stellar_planet_radius_ratio"] > 1:
                passes += 1

        if checks > 0:
            consistency = passes / checks

        scores["physical_consistency"] = consistency

        # 5. Multi-signal bonus
        has_prediction = prediction is not None
        has_anomaly = anomaly is not None
        has_features = len(features) > 3
        multi_count = sum([has_prediction, has_anomaly, has_features])
        scores["multi_signal"] = multi_count / 3.0

        # Compute weighted score
        total = sum(
            scores.get(key, 0.5) * weight
            for key, weight in SCORING_WEIGHTS.items()
        )

        return round(min(1.0, max(0.0, total)), 4)

    async def rank_all_objects(self, dataset_id: Optional[int] = None) -> list[dict[str, Any]]:
        """Compute priority scores for all objects and return sorted ranking."""
        query = select(AstronomicalObject)
        if dataset_id:
            query = query.where(AstronomicalObject.dataset_id == dataset_id)

        result = await self.db.execute(query)
        objects = result.scalars().all()

        rankings = []
        for obj in objects:
            score = await self.compute_priority_score(obj.id)
            rankings.append({
                "object_id": obj.id,
                "name": obj.name,
                "external_id": obj.external_id,
                "object_type": obj.object_type,
                "priority_score": score,
            })

        rankings.sort(key=lambda x: x["priority_score"], reverse=True)

        # Assign ranks
        for i, r in enumerate(rankings):
            r["rank"] = i + 1

        return rankings

    @staticmethod
    def get_scoring_methodology() -> dict[str, Any]:
        """Return transparent scoring methodology for documentation."""
        return {
            "name": "Research Priority Score",
            "description": (
                "A composite score indicating which candidates may warrant "
                "further scientific investigation. This score does NOT confirm "
                "the existence of exoplanets."
            ),
            "range": "0.0 - 1.0 (higher = higher research priority)",
            "weights": SCORING_WEIGHTS,
            "components": {
                "classifier_confidence": "ML model confidence in candidate/confirmed classification",
                "anomaly_score": "How unusual the object is relative to the population",
                "completeness": "Fraction of key parameters with observed values",
                "physical_consistency": "Whether derived parameters fall in physically plausible ranges",
                "multi_signal": "Bonus for having multiple analysis results available",
            },
        }
