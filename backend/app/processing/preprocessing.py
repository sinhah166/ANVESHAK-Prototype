"""
ANVESHAK — Light Curve Preprocessing
Reusable preprocessing functions for stellar light curve data.
"""

from typing import Any, Optional

import numpy as np
from scipy import signal as scipy_signal
from scipy.stats import median_abs_deviation


def preprocess_lightcurve(
    time: np.ndarray,
    flux: np.ndarray,
    quality: Optional[np.ndarray] = None,
    sigma_clip: float = 5.0,
    normalize: bool = True,
) -> dict[str, Any]:
    """
    Full preprocessing pipeline for a stellar light curve.

    Steps:
    1. Quality filtering (if quality flags provided)
    2. NaN/Inf removal
    3. Normalization (to relative flux)
    4. Outlier removal (sigma clipping)
    5. Metadata generation

    Args:
        time: Time array (e.g., BJD days).
        flux: Flux array.
        quality: Optional quality flag array (0 = good).
        sigma_clip: Number of sigma for outlier clipping.
        normalize: Whether to normalize flux to median.

    Returns:
        Dictionary with processed_time, processed_flux, and metadata.
    """
    time = np.asarray(time, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)

    original_length = len(time)

    # Step 1: Quality filtering
    if quality is not None:
        quality = np.asarray(quality)
        good_mask = quality == 0
        time = time[good_mask]
        flux = flux[good_mask]

    # Step 2: Remove NaN and Inf
    valid_mask = np.isfinite(time) & np.isfinite(flux)
    time = time[valid_mask]
    flux = flux[valid_mask]

    if len(time) < 10:
        return {
            "processed_time": time.tolist(),
            "processed_flux": flux.tolist(),
            "metadata": {
                "original_points": original_length,
                "processed_points": len(time),
                "removed_points": original_length - len(time),
                "error": "Too few valid points after cleaning",
            },
        }

    # Step 3: Normalization
    if normalize:
        median_flux = np.nanmedian(flux)
        if median_flux > 0:
            flux = flux / median_flux
        else:
            flux = flux - np.nanmedian(flux) + 1.0

    # Step 4: Sigma clipping
    flux, clip_mask = sigma_clip_flux(flux, sigma=sigma_clip)
    time = time[clip_mask]

    metadata = {
        "original_points": original_length,
        "processed_points": len(time),
        "removed_points": original_length - len(time),
        "median_flux": float(np.nanmedian(flux)),
        "flux_std": float(np.nanstd(flux)),
        "time_span_days": float(time[-1] - time[0]) if len(time) > 1 else 0,
        "cadence_days": float(np.nanmedian(np.diff(time))) if len(time) > 1 else 0,
    }

    return {
        "processed_time": time.tolist(),
        "processed_flux": flux.tolist(),
        "metadata": metadata,
    }


def sigma_clip_flux(
    flux: np.ndarray, sigma: float = 5.0, max_iter: int = 3
) -> tuple[np.ndarray, np.ndarray]:
    """
    Iterative sigma clipping of flux values.

    Args:
        flux: Flux array.
        sigma: Number of sigma for clipping threshold.
        max_iter: Maximum number of clipping iterations.

    Returns:
        Tuple of (clipped_flux, mask_of_kept_indices).
    """
    mask = np.ones(len(flux), dtype=bool)

    for _ in range(max_iter):
        median = np.nanmedian(flux[mask])
        mad = median_abs_deviation(flux[mask], nan_policy="omit")
        if mad == 0:
            break
        # MAD to sigma conversion
        std_est = mad * 1.4826
        new_mask = np.abs(flux - median) < sigma * std_est
        combined = mask & new_mask
        if np.sum(combined) == np.sum(mask):
            break
        mask = combined

    return flux[mask], mask


def remove_nans(time: np.ndarray, flux: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Remove NaN and Inf values from time/flux arrays."""
    valid = np.isfinite(time) & np.isfinite(flux)
    return time[valid], flux[valid]


def normalize_flux(flux: np.ndarray) -> np.ndarray:
    """Normalize flux to median = 1."""
    median = np.nanmedian(flux)
    if median > 0:
        return flux / median
    return flux
