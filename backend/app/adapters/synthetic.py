"""
ANVESHAK — Synthetic Light Curve Adapter
Generates deterministic synthetic astronomical light curves for demo mode.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter, register_adapter
from app.schemas.observation import ObservationCreate, TargetInfo


@register_adapter("synthetic")
class SyntheticAdapter(BaseAdapter):
    """
    Generates synthetic stellar light curves with known properties.
    Used for demo mode and testing.

    Generates three types:
    1. Periodic transit signals (planet-like)
    2. Stellar variability (sinusoidal)
    3. Noise-only (no signal)
    """

    # Demo target catalog
    DEMO_TARGETS = [
        {"name": "TIC 307210830", "ra": 120.45, "dec": -22.31},
        {"name": "TIC 441462736", "ra": 85.12, "dec": 15.67},
        {"name": "TIC 150428135", "ra": 200.89, "dec": -45.22},
        {"name": "TIC 261136679", "ra": 310.33, "dec": 62.14},
        {"name": "TIC 92226327", "ra": 55.78, "dec": -8.90},
        {"name": "KIC 11904151", "ra": 291.05, "dec": 50.13},
        {"name": "KIC 10593626", "ra": 285.67, "dec": 47.82},
        {"name": "TIC 175532955", "ra": 142.30, "dec": -33.45},
    ]

    async def fetch_new(self, count: int = 5, seed: int = 42, **kwargs) -> list[dict[str, Any]]:
        """
        Generate synthetic light curve data.

        Args:
            count: Number of light curves to generate.
            seed: Random seed for determinism.

        Returns:
            List of raw synthetic light curve dictionaries.
        """
        rng = np.random.default_rng(seed)
        records = []

        for i in range(count):
            signal_idx = i % 3  # Cycle: transit, variability, noise

            if signal_idx == 0:
                record = self._generate_transit(rng, i)
            elif signal_idx == 1:
                record = self._generate_variability(rng, i)
            else:
                record = self._generate_noise(rng, i)

            records.append(record)

        self.logger.info("generated_synthetic", count=len(records))
        return records

    def _generate_transit(self, rng: np.random.Generator, idx: int) -> dict[str, Any]:
        """Generate a light curve with a periodic transit signal."""
        n_points = 2000
        duration_days = 27.0  # ~1 TESS sector

        time = np.linspace(0, duration_days, n_points)
        # Base stellar flux with slight trend
        flux = np.ones(n_points) + rng.normal(0, 0.001, n_points)

        # Inject transit
        period = 3.5 + rng.uniform(-0.5, 1.5)  # 3-5 day period
        depth = 0.005 + rng.uniform(0, 0.01)    # 0.5-1.5% depth
        transit_duration_frac = 0.02 + rng.uniform(0, 0.01)
        t0 = rng.uniform(0.5, period)            # First transit time

        # Create box-shaped transits
        phase = ((time - t0) % period) / period
        in_transit = (phase < transit_duration_frac) | (phase > (1.0 - transit_duration_frac))
        flux[in_transit] -= depth

        target = self.DEMO_TARGETS[idx % len(self.DEMO_TARGETS)]

        return {
            "type": "transit",
            "time": time.tolist(),
            "flux": flux.tolist(),
            "target": target,
            "injected_period": float(period),
            "injected_depth": float(depth),
            "injected_t0": float(t0),
            "idx": idx,
        }

    def _generate_variability(self, rng: np.random.Generator, idx: int) -> dict[str, Any]:
        """Generate a light curve with stellar variability (no transit)."""
        n_points = 2000
        duration_days = 27.0

        time = np.linspace(0, duration_days, n_points)

        # Sinusoidal variability + harmonics
        period = 2.0 + rng.uniform(0, 8.0)
        amplitude = 0.005 + rng.uniform(0, 0.015)
        phase_offset = rng.uniform(0, 2 * np.pi)

        flux = (
            1.0
            + amplitude * np.sin(2 * np.pi * time / period + phase_offset)
            + (amplitude / 3) * np.sin(4 * np.pi * time / period + phase_offset)
            + rng.normal(0, 0.001, n_points)
        )

        target = self.DEMO_TARGETS[(idx + 3) % len(self.DEMO_TARGETS)]

        return {
            "type": "stellar_variability",
            "time": time.tolist(),
            "flux": flux.tolist(),
            "target": target,
            "variability_period": float(period),
            "variability_amplitude": float(amplitude),
            "idx": idx,
        }

    def _generate_noise(self, rng: np.random.Generator, idx: int) -> dict[str, Any]:
        """Generate a noise-only light curve (no astrophysical signal)."""
        n_points = 2000
        duration_days = 27.0

        time = np.linspace(0, duration_days, n_points)
        # White noise with slight red noise component
        white_noise = rng.normal(0, 0.002, n_points)
        # Simple red noise via cumulative sum
        red_component = np.cumsum(rng.normal(0, 0.0001, n_points))
        red_component -= np.mean(red_component)
        flux = 1.0 + white_noise + red_component * 0.1

        target = self.DEMO_TARGETS[(idx + 5) % len(self.DEMO_TARGETS)]

        return {
            "type": "noise",
            "time": time.tolist(),
            "flux": flux.tolist(),
            "target": target,
            "idx": idx,
        }

    async def normalize(self, raw_data: dict[str, Any]) -> ObservationCreate:
        """Normalize synthetic data into the common observation schema."""
        target_info = raw_data["target"]
        signal_type = raw_data["type"]
        idx = raw_data.get("idx", 0)

        # Build metadata from injected signal parameters
        metadata = {}
        if signal_type == "transit":
            metadata = {
                "injected_period_days": raw_data.get("injected_period"),
                "injected_depth": raw_data.get("injected_depth"),
                "injected_t0": raw_data.get("injected_t0"),
                "n_points": len(raw_data["time"]),
                "duration_days": raw_data["time"][-1] - raw_data["time"][0],
            }
        elif signal_type == "stellar_variability":
            metadata = {
                "variability_period": raw_data.get("variability_period"),
                "variability_amplitude": raw_data.get("variability_amplitude"),
                "n_points": len(raw_data["time"]),
            }
        else:
            metadata = {"n_points": len(raw_data["time"])}

        return ObservationCreate(
            source_id=self.source_id,
            record_id=f"SYNTH-LC-{idx:04d}-{uuid.uuid4().hex[:8]}",
            observed_at=datetime.now(timezone.utc),
            target=TargetInfo(
                name=target_info["name"],
                ra=target_info["ra"],
                dec=target_info["dec"],
            ),
            signal_type=signal_type,
            raw_payload={
                "time": raw_data["time"],
                "flux": raw_data["flux"],
            },
            preliminary_confidence=None,  # No confidence before processing
            metadata=metadata,
        )

    async def health_check(self) -> dict[str, Any]:
        """Synthetic adapter is always healthy."""
        return {
            "healthy": True,
            "message": "Synthetic data generator is available",
            "source_id": self.source_id,
        }
