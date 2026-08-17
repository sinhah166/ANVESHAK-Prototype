"""
ANVESHAK — Anomaly Detector
Isolation Forest-based anomaly detection for unusual candidates.
"""

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

from app.core.logging import get_logger

logger = get_logger("ml.anomaly")


class AnomalyDetector:
    """
    Isolation Forest anomaly detector for flagging unusual signals.

    This is an optional secondary filter that can flag candidates
    that don't fit normal patterns.
    """

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
        )
        self.is_fitted = False

    def fit(self, features: np.ndarray) -> None:
        """
        Fit the anomaly detector on a set of features.

        Args:
            features: 2D feature array (n_samples, n_features).
        """
        if len(features) < 10:
            logger.warning("too_few_samples_for_anomaly_detection", n=len(features))
            return

        self.model.fit(features)
        self.is_fitted = True
        logger.info("anomaly_detector_fitted", n_samples=len(features))

    def predict(self, features: np.ndarray) -> list[dict[str, Any]]:
        """
        Predict anomaly scores for candidates.

        Args:
            features: 2D feature array.

        Returns:
            List of dicts with 'is_anomaly' and 'anomaly_score'.
        """
        if not self.is_fitted:
            return [{"is_anomaly": False, "anomaly_score": 0.0} for _ in range(len(features))]

        predictions = self.model.predict(features)
        scores = self.model.decision_function(features)

        results = []
        for pred, score in zip(predictions, scores):
            results.append({
                "is_anomaly": bool(pred == -1),
                "anomaly_score": float(-score),  # Higher = more anomalous
            })

        return results
