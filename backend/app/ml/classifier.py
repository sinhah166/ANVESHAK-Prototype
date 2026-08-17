"""
ANVESHAK — ML Classifiers
Classifier interface with baseline (Random Forest) and optional CNN implementations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import numpy as np

from app.core.logging import get_logger

logger = get_logger("ml.classifier")


class ClassifierInterface(ABC):
    """Abstract classifier interface."""

    @abstractmethod
    def classify(self, features: np.ndarray) -> tuple[str, float, str]:
        """
        Classify a candidate based on extracted features.

        Args:
            features: Feature vector.

        Returns:
            Tuple of (classification_label, confidence, model_name).
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this classifier is ready to use."""
        ...


class BaselineClassifier(ClassifierInterface):
    """
    Baseline transit classifier using Random Forest (scikit-learn).

    Uses extracted transit features to classify candidates as:
    - planet_candidate
    - false_positive
    - stellar_variability
    - eclipsing_binary
    - noise
    """

    MODEL_FILENAME = "baseline_classifier.joblib"

    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.model = None
        self.model_name = "baseline_random_forest_v1"
        self._load_model()

    def _load_model(self):
        """Load trained model from disk if available."""
        model_path = self.model_dir / self.MODEL_FILENAME
        if model_path.exists():
            try:
                import joblib
                self.model = joblib.load(model_path)
                logger.info("baseline_model_loaded", path=str(model_path))
            except Exception as e:
                logger.warning("baseline_model_load_failed", error=str(e))
                self.model = None
        else:
            logger.info("no_trained_model_found_using_rules", path=str(model_path))

    def classify(self, features: np.ndarray) -> tuple[str, float, str]:
        """
        Classify transit candidate.

        If trained model exists, use it.
        Otherwise, fall back to rule-based classification.
        """
        if self.model is not None:
            return self._classify_ml(features)
        return self._classify_rules(features)

    def _classify_ml(self, features: np.ndarray) -> tuple[str, float, str]:
        """Classify using trained Random Forest model."""
        features_2d = features.reshape(1, -1)

        try:
            prediction = self.model.predict(features_2d)[0]
            probabilities = self.model.predict_proba(features_2d)[0]
            confidence = float(np.max(probabilities))
            return str(prediction), confidence, self.model_name
        except Exception as e:
            logger.warning("ml_classification_failed", error=str(e))
            return self._classify_rules(features)

    def _classify_rules(self, features: np.ndarray) -> tuple[str, float, str]:
        """
        Rule-based fallback classification for transit candidates.

        Features expected:
        [period, log_depth, duration, sde, snr, n_transits, depth_sig, odd_even]
        """
        model_name = "rule_based_transit_v1"

        if len(features) < 8:
            return "unclassified", 0.0, model_name

        period = features[0]
        log_depth = features[1]
        duration_hrs = features[2]
        sde = features[3]
        snr = features[4]
        n_transits = features[5]
        depth_sig = features[6]
        odd_even = features[7]

        depth = 10 ** log_depth

        # Strong detection with reasonable parameters
        if sde > 8.0 and depth_sig > 3.0 and 0.3 < period < 50:
            # Check for eclipsing binary indicators
            if depth > 0.05 or (odd_even > 0.5 and depth > 0.02):
                return "eclipsing_binary", min(0.7 + sde / 100, 0.95), model_name

            # Planet candidate criteria
            if 0.0001 < depth < 0.05 and 0.5 < duration_hrs < 15:
                confidence = min(0.5 + sde / 30 + depth_sig / 20, 0.98)
                return "planet_candidate", confidence, model_name

            # Stellar variability
            if duration_hrs > 10 or period < 0.5:
                return "stellar_variability", 0.6, model_name

        # Moderate detection
        if sde > 5.0 and depth_sig > 2.0:
            if 0.0001 < depth < 0.05:
                confidence = min(0.3 + sde / 40, 0.85)
                return "planet_candidate", confidence, model_name
            return "false_positive", 0.6, model_name

        # Weak detection
        if sde > 3.0:
            return "false_positive", 0.5, model_name

        return "noise", 0.7, model_name

    def is_available(self) -> bool:
        """Baseline classifier is always available (rule fallback)."""
        return True


class OptionalCNNClassifier(ClassifierInterface):
    """
    Optional CNN classifier using PyTorch.

    Falls back to BaselineClassifier if no trained model exists.
    This is a placeholder for future deep learning integration.
    """

    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.model = None
        self.model_name = "cnn_transit_v1"
        self.fallback = BaselineClassifier(model_dir)
        self._load_model()

    def _load_model(self):
        """Attempt to load a PyTorch CNN model."""
        model_path = self.model_dir / "cnn_classifier.pt"
        if model_path.exists():
            try:
                import torch
                self.model = torch.load(model_path, map_location="cpu")
                self.model.eval()
                logger.info("cnn_model_loaded", path=str(model_path))
            except Exception as e:
                logger.warning("cnn_model_load_failed", error=str(e))
                self.model = None
        else:
            logger.info("no_cnn_model_found_using_fallback")

    def classify(self, features: np.ndarray) -> tuple[str, float, str]:
        """Classify using CNN if available, else fallback."""
        if self.model is not None:
            return self._classify_cnn(features)
        return self.fallback.classify(features)

    def _classify_cnn(self, features: np.ndarray) -> tuple[str, float, str]:
        """CNN classification (placeholder for trained model)."""
        # In a real implementation, this would:
        # 1. Reshape features or raw light curve into CNN input format
        # 2. Run forward pass
        # 3. Map output to classification labels
        return self.fallback.classify(features)

    def is_available(self) -> bool:
        """Check if CNN model is loaded."""
        return self.model is not None


class RadioRuleClassifier(ClassifierInterface):
    """Rule-based classifier for radio signals."""

    def __init__(self):
        self.model_name = "rule_based_radio_v1"

    def classify(self, features: np.ndarray) -> tuple[str, float, str]:
        """
        Classify radio candidate from feature vector.

        Not typically used directly — radio classification happens
        in radio_processing.py. This provides the interface compliance.
        """
        return "unclassified", 0.0, self.model_name

    def is_available(self) -> bool:
        return True
