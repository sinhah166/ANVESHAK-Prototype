"""
ANVESHAK — Anomaly Detection Module
IsolationForest-based anomaly detection for identifying unusual exoplanet candidates.

Results indicate "unusual relative to the training population" — 
NOT "new planet confirmed" or "scientifically validated discovery".
"""

import json
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from app.core.config import ML_ARTIFACTS_DIR
from app.core.logging import get_logger

logger = get_logger("ml.anomaly")

# Default features for anomaly detection
ANOMALY_FEATURES = [
    "orbital_period_days",
    "planet_radius_earth",
    "planet_mass_earth",
    "semi_major_axis_au",
    "eccentricity",
    "equilibrium_temp_k",
    "effective_temp_k",
    "stellar_radius_solar",
    "stellar_mass_solar",
]


class AnomalyDetector:
    """
    IsolationForest-based anomaly detection for exoplanet data.

    Identifies objects with unusual combinations of physical parameters
    relative to the overall population.
    """

    def __init__(self, contamination: float = 0.1, n_estimators: int = 200):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.model = None
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy="median")
        self.feature_names = ANOMALY_FEATURES
        self.is_fitted = False

    def fit(
        self,
        df: pd.DataFrame,
        feature_names: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Fit the anomaly detection model.

        Args:
            df: DataFrame with feature columns.
            feature_names: Feature columns to use.

        Returns:
            Fit summary with statistics.
        """
        if feature_names:
            self.feature_names = feature_names

        available = [f for f in self.feature_names if f in df.columns]
        if len(available) < 2:
            raise ValueError(f"Need at least 2 features. Available: {available}")

        self.feature_names = available
        X = df[available].values

        # Impute and scale
        X_imputed = self.imputer.fit_transform(X)
        X_scaled = self.scaler.fit_transform(X_imputed)

        # Fit IsolationForest
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)
        self.is_fitted = True

        logger.info("anomaly_model_fitted", features=len(available), samples=len(X))
        return {
            "features_used": available,
            "n_samples": len(X),
            "contamination": self.contamination,
        }

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Score objects for anomalousness.

        Returns DataFrame with:
        - anomaly_score: Raw score (more negative = more anomalous)
        - anomaly_label: -1 for anomaly, 1 for normal
        - anomaly_rank: Rank by anomaly score (1 = most anomalous)
        - normalized_score: Score normalized to 0-1 range (1 = most anomalous)
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        available = [f for f in self.feature_names if f in df.columns]
        X = df[available].values

        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)

        scores = self.model.decision_function(X_scaled)
        labels = self.model.predict(X_scaled)

        # Normalize scores to 0-1 (1 = most anomalous)
        score_min, score_max = scores.min(), scores.max()
        if score_max > score_min:
            normalized = 1.0 - (scores - score_min) / (score_max - score_min)
        else:
            normalized = np.full_like(scores, 0.5)

        # Rank (1 = most anomalous)
        ranks = np.argsort(np.argsort(scores)) + 1  # Higher score = less anomalous

        result = pd.DataFrame({
            "anomaly_score": scores,
            "anomaly_label": labels,
            "anomaly_rank": ranks,
            "normalized_score": normalized,
        })

        n_anomalies = (labels == -1).sum()
        logger.info("anomaly_detection_complete", total=len(df), anomalies=int(n_anomalies))

        return result

    def get_feature_contributions(
        self,
        df: pd.DataFrame,
        object_idx: int,
    ) -> dict[str, float]:
        """
        Estimate feature contributions to anomaly score for a specific object.
        Uses a simple perturbation-based approach.
        """
        if not self.is_fitted:
            return {}

        available = [f for f in self.feature_names if f in df.columns]
        X = df[available].values
        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)

        if object_idx >= len(X_scaled):
            return {}

        base_score = self.model.decision_function(X_scaled[object_idx:object_idx + 1])[0]
        contributions = {}

        for i, feat_name in enumerate(available):
            # Replace feature with median (neutral)
            X_modified = X_scaled[object_idx:object_idx + 1].copy()
            X_modified[0, i] = 0.0  # Scaled median is 0
            modified_score = self.model.decision_function(X_modified)[0]
            contributions[feat_name] = float(base_score - modified_score)

        return contributions

    def save(self, path: Optional[str] = None, version: str = "v1") -> str:
        """Save the fitted model."""
        save_dir = Path(path) if path else ML_ARTIFACTS_DIR
        save_dir.mkdir(parents=True, exist_ok=True)
        model_path = save_dir / f"anomaly_{version}.joblib"

        joblib.dump({
            "model": self.model,
            "scaler": self.scaler,
            "imputer": self.imputer,
            "feature_names": self.feature_names,
            "contamination": self.contamination,
        }, model_path)

        logger.info("anomaly_model_saved", path=str(model_path))
        return str(model_path)

    def load(self, path: Optional[str] = None, version: str = "v1") -> bool:
        """Load a fitted model."""
        load_dir = Path(path) if path else ML_ARTIFACTS_DIR
        model_path = load_dir / f"anomaly_{version}.joblib"

        if not model_path.exists():
            return False

        data = joblib.load(model_path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.imputer = data["imputer"]
        self.feature_names = data["feature_names"]
        self.contamination = data.get("contamination", 0.1)
        self.is_fitted = True

        logger.info("anomaly_model_loaded", path=str(model_path))
        return True
