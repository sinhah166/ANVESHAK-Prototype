"""
ANVESHAK — Radio Signal Processing
Processing pipeline for radio spectrograms: normalization, RFI handling,
narrowband detection, and candidate extraction.
"""

from typing import Any

import numpy as np
from scipy import ndimage
from scipy.stats import median_abs_deviation

from app.core.logging import get_logger

logger = get_logger("processing.radio")


def process_spectrogram(
    data: np.ndarray,
    frequencies_mhz: np.ndarray,
    times_seconds: np.ndarray,
    detection_threshold: float = 5.0,
    rfi_threshold: float = 10.0,
    min_signal_bins: int = 3,
) -> list[dict[str, Any]]:
    """
    Full radio spectrogram processing pipeline.

    Steps:
    1. Normalization
    2. Noise estimation
    3. RFI flagging and removal
    4. Candidate extraction
    5. Feature extraction
    6. Rule-based classification

    Args:
        data: 2D spectrogram (time × frequency).
        frequencies_mhz: Frequency array in MHz.
        times_seconds: Time array in seconds.
        detection_threshold: S/N threshold for candidate detection.
        rfi_threshold: S/N threshold for RFI flagging.
        min_signal_bins: Minimum connected bins for a candidate.

    Returns:
        List of candidate dictionaries with features and classifications.
    """
    data = np.asarray(data, dtype=np.float64)
    frequencies_mhz = np.asarray(frequencies_mhz, dtype=np.float64)
    times_seconds = np.asarray(times_seconds, dtype=np.float64)

    # Step 1: Normalize
    normalized = normalize_spectrogram(data)

    # Step 2: Noise estimation
    noise_level, noise_map = estimate_noise(normalized)

    # Step 3: RFI flagging
    rfi_mask = flag_rfi(normalized, rfi_threshold)

    # Apply RFI mask — set flagged regions to noise level
    cleaned = normalized.copy()
    cleaned[rfi_mask] = 0.0

    # Step 4: Candidate extraction
    candidates = extract_candidates(
        cleaned, frequencies_mhz, times_seconds,
        noise_level=noise_level,
        threshold=detection_threshold,
        min_bins=min_signal_bins,
    )

    # Step 5 & 6: Feature extraction + classification
    classified_candidates = []
    for cand in candidates:
        features = extract_radio_features(cand, frequencies_mhz, times_seconds)
        classification = classify_radio_candidate(features, rfi_mask)
        features["classification"] = classification
        classified_candidates.append(features)

    logger.info(
        "radio_processing_complete",
        total_candidates=len(classified_candidates),
        rfi_fraction=float(np.mean(rfi_mask)),
    )

    return classified_candidates


def normalize_spectrogram(data: np.ndarray) -> np.ndarray:
    """
    Normalize spectrogram by subtracting median and dividing by MAD.

    This produces a "S/N-like" map where values represent significance.
    """
    median = np.median(data)
    mad = median_abs_deviation(data.flatten())

    if mad == 0 or np.isnan(mad):
        return data - median

    normalized = (data - median) / (mad * 1.4826)
    return normalized


def estimate_noise(data: np.ndarray) -> tuple[float, np.ndarray]:
    """
    Estimate noise level per frequency channel.

    Returns:
        Tuple of (global_noise_level, per_channel_noise_array).
    """
    # Per-channel MAD-based noise
    n_freq = data.shape[1]
    channel_noise = np.zeros(n_freq)

    for i in range(n_freq):
        channel_data = data[:, i]
        channel_noise[i] = median_abs_deviation(channel_data) * 1.4826

    global_noise = float(np.median(channel_noise))

    return global_noise, channel_noise


def flag_rfi(data: np.ndarray, threshold: float = 10.0) -> np.ndarray:
    """
    Flag Radio Frequency Interference (RFI).

    Identifies:
    1. Broadband bursts (entire time bins above threshold across many channels)
    2. Persistent narrowband RFI (single channels always above threshold)

    Returns:
        Boolean mask where True = RFI.
    """
    rfi_mask = np.zeros_like(data, dtype=bool)

    # Broadband: check if a time bin has high values across >50% of channels
    time_medians = np.median(np.abs(data), axis=1)
    broadband_rfi_times = time_medians > threshold
    rfi_mask[broadband_rfi_times, :] = True

    # Persistent narrowband: check if a channel has consistently high values
    freq_medians = np.median(np.abs(data), axis=0)
    persistent_rfi_freqs = freq_medians > threshold * 0.5
    rfi_mask[:, persistent_rfi_freqs] = True

    return rfi_mask


def extract_candidates(
    data: np.ndarray,
    frequencies_mhz: np.ndarray,
    times_seconds: np.ndarray,
    noise_level: float,
    threshold: float = 5.0,
    min_bins: int = 3,
) -> list[dict[str, Any]]:
    """
    Extract candidate signals from cleaned spectrogram.

    Uses thresholding + connected component labeling.
    """
    # Create detection map
    detection_map = data > threshold

    # Label connected components
    labeled_array, n_features = ndimage.label(detection_map)

    candidates = []
    for i in range(1, n_features + 1):
        component = labeled_array == i
        n_pixels = np.sum(component)

        if n_pixels < min_bins:
            continue

        # Get bounding box
        time_indices, freq_indices = np.where(component)

        candidates.append({
            "component_id": i,
            "time_indices": time_indices.tolist(),
            "freq_indices": freq_indices.tolist(),
            "n_pixels": int(n_pixels),
            "peak_value": float(np.max(data[component])),
            "integrated_value": float(np.sum(data[component])),
        })

    return candidates


def extract_radio_features(
    candidate: dict[str, Any],
    frequencies_mhz: np.ndarray,
    times_seconds: np.ndarray,
) -> dict[str, Any]:
    """
    Extract scientific features from a radio candidate.

    Returns dict with: center_frequency, bandwidth, duration,
    signal_strength, integrated_power, drift_rate.
    """
    time_idx = np.array(candidate["time_indices"])
    freq_idx = np.array(candidate["freq_indices"])

    freq_values = frequencies_mhz[freq_idx]
    time_values = times_seconds[time_idx]

    center_freq = float(np.mean(freq_values))
    bandwidth_mhz = float(np.max(freq_values) - np.min(freq_values))
    bandwidth_hz = bandwidth_mhz * 1e6

    duration = float(np.max(time_values) - np.min(time_values))

    # Drift rate: linear fit of frequency vs time
    drift_rate = 0.0
    if len(time_idx) > 3 and duration > 0:
        try:
            coeffs = np.polyfit(time_values, freq_values * 1e6, deg=1)  # Hz/s
            drift_rate = float(coeffs[0])
        except Exception:
            pass

    return {
        "center_frequency_mhz": center_freq,
        "bandwidth_hz": max(bandwidth_hz, float(np.mean(np.diff(frequencies_mhz)) * 1e6)),
        "duration_seconds": max(duration, float(np.mean(np.diff(times_seconds)))),
        "signal_strength": float(candidate["peak_value"]),
        "integrated_power": float(candidate["integrated_value"]),
        "drift_rate_hz_per_s": drift_rate,
        "n_pixels": candidate["n_pixels"],
    }


def classify_radio_candidate(
    features: dict[str, Any],
    rfi_mask: np.ndarray,
) -> str:
    """
    Rule-based classification of radio candidates.

    Classifications:
    - noise: weak, diffuse signals
    - rfi: broadband, very strong, or known interference patterns
    - narrowband_candidate: narrow bandwidth, moderate strength, drifting
    - anomaly: doesn't fit other categories
    """
    strength = features.get("signal_strength", 0)
    bandwidth = features.get("bandwidth_hz", 0)
    duration = features.get("duration_seconds", 0)
    drift = abs(features.get("drift_rate_hz_per_s", 0))
    n_pixels = features.get("n_pixels", 0)

    # Noise: weak signal
    if strength < 3.0:
        return "noise"

    # RFI: very strong broadband
    if bandwidth > 1e6 and strength > 8.0:
        return "rfi"

    # RFI: very strong, very short
    if strength > 15.0 and duration < 2.0:
        return "rfi"

    # Narrowband candidate: narrow bandwidth, reasonable strength
    if bandwidth < 5e5 and strength > 4.0:
        if drift > 0.001 or n_pixels > 5:
            return "narrowband_candidate"

    # Anomaly: doesn't fit standard patterns
    if strength > 5.0:
        return "anomaly"

    return "noise"
