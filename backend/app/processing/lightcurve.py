"""
ANVESHAK — Light Curve Processing
Detrending, gap handling, and advanced light curve operations.
"""

from typing import Any, Optional

import numpy as np
from scipy.signal import savgol_filter


def detrend_lightcurve(
    time: np.ndarray,
    flux: np.ndarray,
    method: str = "savgol",
    window_length: int = 301,
    polyorder: int = 2,
) -> dict[str, Any]:
    """
    Detrend a light curve to remove long-term stellar variability.

    Args:
        time: Time array.
        flux: Normalized flux array.
        method: Detrending method ('savgol', 'polynomial', 'median').
        window_length: Window for Savitzky-Golay filter (must be odd).
        polyorder: Polynomial order for filter.

    Returns:
        Dictionary with detrended_flux and trend.
    """
    time = np.asarray(time, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)

    if len(flux) < 20:
        return {
            "detrended_flux": flux.tolist(),
            "trend": np.ones_like(flux).tolist(),
            "method": "none (too few points)",
        }

    if method == "savgol":
        # Ensure window_length is odd and <= len(flux)
        wl = min(window_length, len(flux))
        if wl % 2 == 0:
            wl -= 1
        wl = max(wl, polyorder + 2)

        trend = savgol_filter(flux, window_length=wl, polyorder=polyorder)
        detrended = flux / trend

    elif method == "polynomial":
        coeffs = np.polyfit(time - time[0], flux, deg=polyorder)
        trend = np.polyval(coeffs, time - time[0])
        detrended = flux / trend

    elif method == "median":
        # Sliding median filter
        kernel_size = min(window_length, len(flux))
        if kernel_size % 2 == 0:
            kernel_size -= 1
        kernel_size = max(kernel_size, 3)
        from scipy.ndimage import median_filter
        trend = median_filter(flux, size=kernel_size)
        trend[trend == 0] = 1.0
        detrended = flux / trend

    else:
        raise ValueError(f"Unknown detrending method: {method}")

    return {
        "detrended_flux": detrended.tolist(),
        "trend": trend.tolist(),
        "method": method,
    }


def phase_fold(
    time: np.ndarray,
    flux: np.ndarray,
    period: float,
    t0: float = 0.0,
) -> dict[str, Any]:
    """
    Phase-fold a light curve at a given period.

    Args:
        time: Time array.
        flux: Flux array.
        period: Folding period in same units as time.
        t0: Reference epoch.

    Returns:
        Dictionary with phase and folded_flux arrays.
    """
    phase = ((time - t0) % period) / period
    # Center transit at phase 0.5
    phase = (phase + 0.5) % 1.0

    # Sort by phase
    sort_idx = np.argsort(phase)
    phase = phase[sort_idx]
    folded_flux = flux[sort_idx]

    return {
        "phase": phase.tolist(),
        "folded_flux": folded_flux.tolist(),
        "period": float(period),
        "t0": float(t0),
    }


def detect_gaps(
    time: np.ndarray, gap_threshold_factor: float = 5.0
) -> list[tuple[int, int]]:
    """
    Detect gaps in time series data.

    Args:
        time: Time array.
        gap_threshold_factor: Factor above median cadence to consider a gap.

    Returns:
        List of (start_idx, end_idx) tuples for each continuous segment.
    """
    if len(time) < 2:
        return [(0, len(time))]

    diffs = np.diff(time)
    median_cadence = np.median(diffs)
    gap_threshold = median_cadence * gap_threshold_factor

    gap_indices = np.where(diffs > gap_threshold)[0]

    segments = []
    start = 0
    for gap_idx in gap_indices:
        segments.append((start, gap_idx + 1))
        start = gap_idx + 1
    segments.append((start, len(time)))

    return segments


def bin_lightcurve(
    time: np.ndarray,
    flux: np.ndarray,
    bin_size: float = 0.01,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Bin a light curve in time.

    Args:
        time: Time array.
        flux: Flux array.
        bin_size: Bin width in same units as time.

    Returns:
        Tuple of (binned_time, binned_flux, binned_flux_err).
    """
    bins = np.arange(time[0], time[-1] + bin_size, bin_size)
    digitized = np.digitize(time, bins)

    binned_time = []
    binned_flux = []
    binned_err = []

    for i in range(1, len(bins)):
        mask = digitized == i
        if np.sum(mask) > 0:
            binned_time.append(np.mean(time[mask]))
            binned_flux.append(np.mean(flux[mask]))
            binned_err.append(np.std(flux[mask]) / np.sqrt(np.sum(mask)))

    return np.array(binned_time), np.array(binned_flux), np.array(binned_err)
