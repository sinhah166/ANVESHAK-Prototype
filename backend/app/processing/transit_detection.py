"""
ANVESHAK — Transit Detection
Implements transit search using Transit Least Squares (TLS) and BLS fallback.
"""

from typing import Any, Optional

import numpy as np

from app.core.logging import get_logger

logger = get_logger("processing.transit_detection")


def detect_transits(
    time: np.ndarray,
    flux: np.ndarray,
    method: str = "tls",
    min_period: float = 0.5,
    max_period: float = 20.0,
    **kwargs,
) -> list[dict[str, Any]]:
    """
    Search for periodic transit signals in a light curve.

    Primary method: Transit Least Squares (TLS)
    Fallback: Box Least Squares (BLS) via astropy

    Args:
        time: Time array (days).
        flux: Normalized flux array.
        method: Detection method ('tls' or 'bls').
        min_period: Minimum search period in days.
        max_period: Maximum search period in days.

    Returns:
        List of detected transit candidate dictionaries.
    """
    time = np.asarray(time, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)

    if len(time) < 50:
        logger.warning("too_few_points_for_transit_search", n_points=len(time))
        return []

    # Constrain max_period to half the time baseline
    time_baseline = time[-1] - time[0]
    max_period = min(max_period, time_baseline / 2.0)

    if max_period <= min_period:
        logger.warning("period_range_invalid", min_period=min_period, max_period=max_period)
        return []

    if method == "tls":
        try:
            return _detect_tls(time, flux, min_period, max_period, **kwargs)
        except Exception as e:
            logger.warning("tls_failed_falling_back_to_bls", error=str(e))
            return _detect_bls(time, flux, min_period, max_period, **kwargs)
    else:
        return _detect_bls(time, flux, min_period, max_period, **kwargs)


def _detect_tls(
    time: np.ndarray,
    flux: np.ndarray,
    min_period: float,
    max_period: float,
    **kwargs,
) -> list[dict[str, Any]]:
    """
    Transit detection using Transit Least Squares.

    Returns list of candidate dicts with scientific features.
    """
    from transitleastsquares import transitleastsquares

    model = transitleastsquares(time, flux)
    results = model.power(
        period_min=min_period,
        period_max=max_period,
        show_progress_bar=False,
        use_threads=1,
    )

    candidates = []

    # Check if a significant signal was found
    sde = float(results.SDE)
    if sde < 5.0:
        logger.info("no_significant_transit_tls", sde=sde)
        # Still return the best result with low confidence
        if hasattr(results, "period") and results.period is not None:
            candidates.append(_build_tls_candidate(results, significant=False))
        return candidates

    candidates.append(_build_tls_candidate(results, significant=True))

    logger.info(
        "transit_detected_tls",
        period=float(results.period),
        depth=float(results.depth) if hasattr(results, "depth") else None,
        sde=sde,
    )

    return candidates


def _build_tls_candidate(results, significant: bool) -> dict[str, Any]:
    """Build a candidate dict from TLS results."""
    period = float(results.period)
    t0 = float(results.T0)
    sde = float(results.SDE)

    # Safely extract depth
    depth = None
    if hasattr(results, "depth"):
        depth_val = results.depth
        if depth_val is not None:
            depth = float(1.0 - depth_val) if depth_val < 1 else float(depth_val)

    # Safely extract duration
    duration_hours = None
    if hasattr(results, "duration"):
        dur = results.duration
        if dur is not None:
            duration_hours = float(dur) * 24.0  # Convert days to hours

    # Number of transits
    n_transits = None
    if hasattr(results, "distinct_transit_count"):
        n_transits = int(results.distinct_transit_count)
    elif hasattr(results, "transit_count"):
        n_transits = int(results.transit_count)

    # SNR estimate
    snr = sde  # SDE is roughly analogous to SNR for TLS

    # Odd/even mismatch
    odd_even = None
    if hasattr(results, "odd_even_mismatch"):
        odd_even = float(results.odd_even_mismatch)

    return {
        "method": "tls",
        "period": period,
        "period_uncertainty": float(results.period_uncertainty) if hasattr(results, "period_uncertainty") and results.period_uncertainty else None,
        "transit_time": t0,
        "depth": depth,
        "duration_hours": duration_hours,
        "detection_power": sde,
        "snr": snr,
        "n_transits": n_transits,
        "odd_even_mismatch": odd_even,
        "significant": significant,
        "model_flux": results.model_lightcurve_model.tolist() if hasattr(results, "model_lightcurve_model") and results.model_lightcurve_model is not None else None,
        "in_transit_mask": results.in_transit_indices.tolist() if hasattr(results, "in_transit_indices") and results.in_transit_indices is not None else None,
        "folded_phase": results.folded_phase.tolist() if hasattr(results, "folded_phase") and results.folded_phase is not None else None,
        "folded_flux": results.folded_y.tolist() if hasattr(results, "folded_y") and results.folded_y is not None else None,
    }


def _detect_bls(
    time: np.ndarray,
    flux: np.ndarray,
    min_period: float,
    max_period: float,
    **kwargs,
) -> list[dict[str, Any]]:
    """
    Transit detection using Box Least Squares (astropy).

    Fallback method when TLS is unavailable.
    """
    from astropy.timeseries import BoxLeastSquares

    bls = BoxLeastSquares(time, flux)

    # Generate period grid
    n_periods = min(10000, int((max_period - min_period) / 0.001))
    n_periods = max(n_periods, 100)
    periods = np.linspace(min_period, max_period, n_periods)

    # Duration grid (fraction of period)
    durations = np.array([0.01, 0.02, 0.03, 0.05, 0.08]) * np.median(periods)
    durations = durations[durations > 0]

    try:
        results = bls.power(periods, durations)
    except Exception as e:
        logger.error("bls_power_failed", error=str(e))
        return []

    # Find best period
    best_idx = np.argmax(results.power)
    best_period = float(results.period[best_idx])
    best_power = float(results.power[best_idx])
    best_duration = float(results.duration[best_idx])

    # Estimate significance
    median_power = np.median(results.power)
    std_power = np.std(results.power)
    if std_power > 0:
        snr = (best_power - median_power) / std_power
    else:
        snr = 0.0

    significant = snr > 5.0

    # Get transit parameters
    try:
        stats = bls.compute_stats(best_period, best_duration, results.transit_time[best_idx])
        depth = float(stats.get("depth", [0])[0]) if "depth" in stats else None
    except Exception:
        depth = None
        stats = {}

    # Phase fold for output
    phase = ((time - float(results.transit_time[best_idx])) % best_period) / best_period
    phase = (phase + 0.5) % 1.0
    sort_idx = np.argsort(phase)

    candidate = {
        "method": "bls",
        "period": best_period,
        "period_uncertainty": None,
        "transit_time": float(results.transit_time[best_idx]),
        "depth": depth,
        "duration_hours": best_duration * 24.0,
        "detection_power": best_power,
        "snr": snr,
        "n_transits": int(np.round((time[-1] - time[0]) / best_period)) if best_period > 0 else None,
        "odd_even_mismatch": None,
        "significant": significant,
        "model_flux": None,
        "in_transit_mask": None,
        "folded_phase": phase[sort_idx].tolist(),
        "folded_flux": flux[sort_idx].tolist(),
    }

    if significant:
        logger.info(
            "transit_detected_bls",
            period=best_period,
            snr=snr,
            depth=depth,
        )
    else:
        logger.info("no_significant_transit_bls", snr=snr)

    return [candidate]
