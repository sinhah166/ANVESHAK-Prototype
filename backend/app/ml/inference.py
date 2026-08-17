"""
ANVESHAK — ML Inference
Routes classification requests to the appropriate classifier.
"""

from typing import Any

import numpy as np

from app.core.logging import get_logger
from app.ml.classifier import BaselineClassifier, RadioRuleClassifier
from app.processing.feature_extraction import compute_transit_ml_features
from app.schemas.candidate import TransitFeatures

logger = get_logger("ml.inference")

# Singleton classifiers
_transit_classifier = None
_radio_classifier = None


def get_transit_classifier() -> BaselineClassifier:
    """Get or create the transit classifier."""
    global _transit_classifier
    if _transit_classifier is None:
        _transit_classifier = BaselineClassifier()
    return _transit_classifier


def get_radio_classifier() -> RadioRuleClassifier:
    """Get or create the radio classifier."""
    global _radio_classifier
    if _radio_classifier is None:
        _radio_classifier = RadioRuleClassifier()
    return _radio_classifier


def classify_transit_candidate(
    transit_features: TransitFeatures,
    flux_std: float = 0.001,
) -> dict[str, Any]:
    """
    Classify a transit candidate using extracted features.

    Args:
        transit_features: Extracted transit features.
        flux_std: Standard deviation of the light curve flux.

    Returns:
        Dict with classification, confidence, and model_name.
    """
    feature_vector = compute_transit_ml_features(transit_features, flux_std)
    classifier = get_transit_classifier()
    classification, confidence, model_name = classifier.classify(feature_vector)

    logger.info(
        "transit_classified",
        classification=classification,
        confidence=confidence,
        model=model_name,
        period=transit_features.period,
    )

    return {
        "classification": classification,
        "confidence": confidence,
        "model_name": model_name,
    }


def classify_radio_candidate(
    radio_features: dict[str, Any],
) -> dict[str, Any]:
    """
    Classify a radio candidate.

    Radio classification is primarily rule-based and happens during
    radio processing. This function wraps the result for consistency.

    Args:
        radio_features: Dict with radio features including 'classification'.

    Returns:
        Dict with classification, confidence, and model_name.
    """
    # Radio classification is done in radio_processing.py
    classification = radio_features.get("classification", "unclassified")

    # Assign confidence based on signal properties
    strength = radio_features.get("signal_strength", 0)
    if classification == "narrowband_candidate":
        confidence = min(0.5 + strength / 30, 0.95)
    elif classification == "rfi":
        confidence = min(0.7 + strength / 50, 0.99)
    elif classification == "anomaly":
        confidence = min(0.4 + strength / 40, 0.85)
    else:
        confidence = 0.3

    return {
        "classification": classification,
        "confidence": confidence,
        "model_name": "rule_based_radio_v1",
    }
