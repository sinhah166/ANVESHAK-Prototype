"""
ANVESHAK — Tests for Preprocessing Module
"""

import numpy as np

from app.processing.preprocessing import preprocess_lightcurve


def test_preprocess_lightcurve_basic():
    """Test basic detrending and normalization."""
    # Create simple synthetic time series
    time = np.linspace(0, 10, 1000)
    # Baseline flux around 1.0 with some noise and a trend
    trend = 1.0 + 0.1 * np.sin(time)
    noise = np.random.normal(0, 0.001, 1000)
    flux = trend + noise

    result = preprocess_lightcurve(time, flux)

    assert "processed_time" in result
    assert "processed_flux" in result
    assert "metadata" in result
    
    p_flux = result["processed_flux"]
    
    # Assert normalized around 1.0
    assert np.isclose(np.mean(p_flux), 1.0, atol=0.01)
    # Trend should be mostly removed, standard dev should match noise closely
    assert np.std(p_flux) < 0.005


def test_preprocess_lightcurve_outliers():
    """Test outlier rejection in preprocessing."""
    time = np.linspace(0, 10, 1000)
    flux = np.ones(1000)
    
    # Inject massive outliers
    flux[10] = 5.0
    flux[20] = -5.0
    
    result = preprocess_lightcurve(time, flux)
    p_flux = result["processed_flux"]
    
    # Outliers should be clipped (replaced by nan or median, our logic replaces with nan and drops)
    # The length should be less than 1000 since we dropped the NaNs
    assert len(p_flux) < 1000
    assert np.max(p_flux) < 2.0
    assert np.min(p_flux) > 0.5
