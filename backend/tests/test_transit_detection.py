"""
ANVESHAK — Tests for Transit Detection Module
"""

import numpy as np
import pytest

from app.processing.transit_detection import detect_transits


def simulate_transit_lightcurve(period: float, depth: float, t0: float, duration: float):
    """Helper to generate a synthetic light curve with a transit."""
    time = np.linspace(0, 20, 2000) # 20 days
    flux = np.ones_like(time)
    
    # Inject transit
    phase = (time - t0) % period
    in_transit = (phase < duration / 2) | (phase > period - duration / 2)
    flux[in_transit] -= depth
    
    # Add noise
    flux += np.random.normal(0, 0.0001, len(time))
    
    return time, flux


def test_detect_transits_positive():
    """Test that TLS can successfully detect a clear transit."""
    period_true = 3.5
    depth_true = 0.01
    t0_true = 1.2
    duration_true = 0.1
    
    time, flux = simulate_transit_lightcurve(period_true, depth_true, t0_true, duration_true)
    
    results = detect_transits(time, flux)
    
    assert len(results) > 0
    best_candidate = results[0]
    
    # Period should be recovered accurately
    assert np.isclose(best_candidate["period"], period_true, rtol=0.05)
    # High SDE
    assert best_candidate["detection_power"] > 10.0


def test_detect_transits_noise():
    """Test that pure noise does not result in false high-confidence transits."""
    time = np.linspace(0, 20, 2000)
    flux = np.ones(2000) + np.random.normal(0, 0.005, 2000)
    
    results = detect_transits(time, flux)
    
    # It might return a result, but SDE should be low
    if len(results) > 0:
        assert results[0]["detection_power"] < 8.0 
