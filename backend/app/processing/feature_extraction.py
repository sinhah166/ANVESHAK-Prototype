"""
ANVESHAK — Feature Extraction
Unified feature extraction for transit and radio candidates.
"""

from typing import Any

import numpy as np

from app.schemas.candidate import RadioFeatures, TransitFeatures


def extract_transit_features(
    detection_result: dict[str, Any],
) -> TransitFeatures:
    """
    Extract structured transit features from a detection result.

    Args:
        detection_result: Raw output from transit detection module.

    Returns:
        TransitFeatures Pydantic model.
    """
    return TransitFeatures(
        period=detection_result.get("period"),
        period_uncertainty=detection_result.get("period_uncertainty"),
        depth=detection_result.get("depth"),
        duration=detection_result.get("duration_hours"),
        transit_time=detection_result.get("transit_time"),
        detection_power=detection_result.get("detection_power"),
        snr=detection_result.get("snr"),
        n_transits=detection_result.get("n_transits"),
        odd_even_mismatch=detection_result.get("odd_even_mismatch"),
    )


def extract_radio_features_schema(
    radio_result: dict[str, Any],
) -> RadioFeatures:
    """
    Extract structured radio features from a processing result.

    Args:
        radio_result: Raw output from radio processing module.

    Returns:
        RadioFeatures Pydantic model.
    """
    return RadioFeatures(
        frequency_mhz=radio_result.get("center_frequency_mhz"),
        bandwidth_hz=radio_result.get("bandwidth_hz"),
        duration_seconds=radio_result.get("duration_seconds"),
        signal_strength=radio_result.get("signal_strength"),
        integrated_power=radio_result.get("integrated_power"),
        drift_rate=radio_result.get("drift_rate_hz_per_s"),
    )


def compute_transit_ml_features(
    transit_features: TransitFeatures,
    flux_std: float = 0.001,
) -> np.ndarray:
    """
    Compute feature vector for ML classification of transit candidates.

    Returns a fixed-length feature array suitable for scikit-learn models.

    Features:
    0: period (days)
    1: log10(depth)
    2: duration (hours)
    3: detection_power (SDE)
    4: snr
    5: n_transits
    6: depth / flux_std (depth significance)
    7: odd_even_mismatch (0 if unavailable)
    """
    period = transit_features.period or 0.0
    depth = transit_features.depth or 0.0
    duration = transit_features.duration or 0.0
    sde = transit_features.detection_power or 0.0
    snr = transit_features.snr or 0.0
    n_transits = transit_features.n_transits or 0
    odd_even = transit_features.odd_even_mismatch or 0.0

    log_depth = np.log10(max(depth, 1e-10))
    depth_significance = depth / max(flux_std, 1e-10)

    return np.array([
        period,
        log_depth,
        duration,
        sde,
        snr,
        float(n_transits),
        depth_significance,
        odd_even,
    ], dtype=np.float64)
