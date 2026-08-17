"""
ANVESHAK — Radio Demo Adapter
Generates synthetic radio spectrograms for demo mode.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter, register_adapter
from app.schemas.observation import ObservationCreate, TargetInfo


@register_adapter("radio_demo")
class RadioDemoAdapter(BaseAdapter):
    """
    Generates synthetic radio spectrograms for demo/testing.

    Generates three types:
    1. Narrowband signal (potential interesting signal)
    2. RFI (radio frequency interference)
    3. Noise-only
    """

    DEMO_TARGETS = [
        {"name": "Proxima Centauri", "ra": 217.39, "dec": -62.68},
        {"name": "Barnard's Star", "ra": 269.45, "dec": 4.69},
        {"name": "Tau Ceti", "ra": 26.02, "dec": -15.94},
        {"name": "Ross 128", "ra": 176.94, "dec": 0.80},
        {"name": "GJ 273", "ra": 109.87, "dec": 5.23},
    ]

    async def fetch_new(self, count: int = 3, seed: int = 42, **kwargs) -> list[dict[str, Any]]:
        """Generate synthetic radio spectrogram data."""
        rng = np.random.default_rng(seed + 1000)  # Different seed from LC
        records = []

        for i in range(count):
            signal_idx = i % 3

            if signal_idx == 0:
                record = self._generate_narrowband(rng, i)
            elif signal_idx == 1:
                record = self._generate_rfi(rng, i)
            else:
                record = self._generate_noise(rng, i)

            records.append(record)

        self.logger.info("generated_radio_synthetic", count=len(records))
        return records

    def _generate_narrowband(self, rng: np.random.Generator, idx: int) -> dict[str, Any]:
        """Generate a spectrogram with a narrowband signal."""
        n_times = 256
        n_freqs = 128

        freq_min, freq_max = 1400.0, 1440.0  # MHz (near hydrogen line)
        freqs = np.linspace(freq_min, freq_max, n_freqs)
        times = np.linspace(0, 300, n_times)  # 300 seconds

        # Background noise
        data = rng.normal(0, 1, (n_times, n_freqs))

        # Inject narrowband signal
        signal_freq = 1420.0 + rng.uniform(-5, 5)
        signal_bw = 0.05 + rng.uniform(0, 0.1)  # Very narrow
        drift_rate = rng.uniform(-0.01, 0.01)  # Hz/s drift
        signal_strength = 5.0 + rng.uniform(0, 10)

        # Signal start/end in time
        t_start = int(n_times * 0.2)
        t_end = int(n_times * 0.8)

        for t_idx in range(t_start, t_end):
            current_freq = signal_freq + drift_rate * times[t_idx]
            freq_idx = np.argmin(np.abs(freqs - current_freq))
            bw_bins = max(1, int(signal_bw / (freqs[1] - freqs[0])))
            low = max(0, freq_idx - bw_bins)
            high = min(n_freqs, freq_idx + bw_bins + 1)
            data[t_idx, low:high] += signal_strength

        target = self.DEMO_TARGETS[idx % len(self.DEMO_TARGETS)]

        return {
            "type": "radio_narrowband",
            "spectrogram": data.tolist(),
            "frequencies_mhz": freqs.tolist(),
            "times_seconds": times.tolist(),
            "target": target,
            "injected_frequency_mhz": float(signal_freq),
            "injected_bandwidth_mhz": float(signal_bw),
            "injected_strength": float(signal_strength),
            "injected_drift_rate": float(drift_rate),
            "idx": idx,
        }

    def _generate_rfi(self, rng: np.random.Generator, idx: int) -> dict[str, Any]:
        """Generate a spectrogram with RFI (broadband interference)."""
        n_times = 256
        n_freqs = 128

        freq_min, freq_max = 1400.0, 1440.0
        freqs = np.linspace(freq_min, freq_max, n_freqs)
        times = np.linspace(0, 300, n_times)

        data = rng.normal(0, 1, (n_times, n_freqs))

        # RFI: broadband burst across many frequencies
        rfi_start = int(n_times * 0.3)
        rfi_end = int(n_times * 0.35)
        rfi_strength = 15.0 + rng.uniform(0, 10)
        data[rfi_start:rfi_end, :] += rfi_strength

        # Additional narrowband RFI at a fixed frequency
        rfi_freq_idx = rng.integers(20, n_freqs - 20)
        data[:, rfi_freq_idx - 2:rfi_freq_idx + 3] += 3.0

        target = self.DEMO_TARGETS[(idx + 2) % len(self.DEMO_TARGETS)]

        return {
            "type": "rfi",
            "spectrogram": data.tolist(),
            "frequencies_mhz": freqs.tolist(),
            "times_seconds": times.tolist(),
            "target": target,
            "idx": idx,
        }

    def _generate_noise(self, rng: np.random.Generator, idx: int) -> dict[str, Any]:
        """Generate a noise-only spectrogram."""
        n_times = 256
        n_freqs = 128

        freq_min, freq_max = 1400.0, 1440.0
        freqs = np.linspace(freq_min, freq_max, n_freqs)
        times = np.linspace(0, 300, n_times)

        data = rng.normal(0, 1, (n_times, n_freqs))

        target = self.DEMO_TARGETS[(idx + 4) % len(self.DEMO_TARGETS)]

        return {
            "type": "noise",
            "spectrogram": data.tolist(),
            "frequencies_mhz": freqs.tolist(),
            "times_seconds": times.tolist(),
            "target": target,
            "idx": idx,
        }

    async def normalize(self, raw_data: dict[str, Any]) -> ObservationCreate:
        """Normalize radio data into the common observation schema."""
        target_info = raw_data["target"]
        signal_type = raw_data["type"]
        idx = raw_data.get("idx", 0)

        metadata = {
            "n_time_bins": len(raw_data["times_seconds"]),
            "n_freq_bins": len(raw_data["frequencies_mhz"]),
            "freq_range_mhz": [
                raw_data["frequencies_mhz"][0],
                raw_data["frequencies_mhz"][-1],
            ],
            "duration_seconds": raw_data["times_seconds"][-1],
        }

        if signal_type == "radio_narrowband":
            metadata.update({
                "injected_frequency_mhz": raw_data.get("injected_frequency_mhz"),
                "injected_bandwidth_mhz": raw_data.get("injected_bandwidth_mhz"),
                "injected_strength": raw_data.get("injected_strength"),
                "injected_drift_rate": raw_data.get("injected_drift_rate"),
            })

        return ObservationCreate(
            source_id=self.source_id,
            record_id=f"RADIO-{signal_type.upper()}-{idx:04d}-{uuid.uuid4().hex[:8]}",
            observed_at=datetime.now(timezone.utc),
            target=TargetInfo(
                name=target_info["name"],
                ra=target_info["ra"],
                dec=target_info["dec"],
            ),
            signal_type=signal_type if signal_type != "noise" else "noise",
            raw_payload={
                "spectrogram": raw_data["spectrogram"],
                "frequencies_mhz": raw_data["frequencies_mhz"],
                "times_seconds": raw_data["times_seconds"],
            },
            preliminary_confidence=None,
            metadata=metadata,
        )

    async def health_check(self) -> dict[str, Any]:
        """Radio demo adapter is always healthy."""
        return {
            "healthy": True,
            "message": "Radio demo data generator is available",
            "source_id": self.source_id,
        }
