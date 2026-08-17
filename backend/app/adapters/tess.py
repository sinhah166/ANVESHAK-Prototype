"""
ANVESHAK — TESS Archive Adapter
Fetches light curves from MAST archive via lightkurve.
Falls back to demo data if archive is unavailable.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter, register_adapter
from app.schemas.observation import ObservationCreate, TargetInfo


@register_adapter("tess")
class TessAdapter(BaseAdapter):
    """
    TESS (Transiting Exoplanet Survey Satellite) data adapter.

    In archive mode: fetches from MAST via lightkurve.
    Falls back to synthetic demo data if external access fails.
    """

    # Well-known TESS targets for archive mode
    KNOWN_TARGETS = [
        {"name": "TIC 307210830", "ra": 120.45, "dec": -22.31, "tic_id": 307210830},
        {"name": "TIC 441462736", "ra": 85.12, "dec": 15.67, "tic_id": 441462736},
    ]

    async def fetch_new(self, mode: str = "demo", **kwargs) -> list[dict[str, Any]]:
        """
        Fetch TESS light curve data.

        In demo mode, generates synthetic TESS-like data.
        In archive mode, attempts to query MAST.
        """
        if mode == "archive":
            return await self._fetch_archive(**kwargs)
        return await self._fetch_demo(**kwargs)

    async def _fetch_archive(self, target_name: str = None, **kwargs) -> list[dict[str, Any]]:
        """Attempt to fetch from MAST archive."""
        try:
            import lightkurve as lk

            target = target_name or "TIC 307210830"
            self.logger.info("fetching_tess_archive", target=target)

            search_result = lk.search_lightcurve(target, mission="TESS", author="SPOC")

            if len(search_result) == 0:
                self.logger.warning("no_tess_data_found", target=target)
                return await self._fetch_demo()

            # Download first result
            lc = search_result[0].download()
            lc = lc.remove_nans().normalize()

            return [{
                "type": "transit",
                "time": lc.time.value.tolist(),
                "flux": lc.flux.value.tolist(),
                "target": {"name": target, "ra": 120.45, "dec": -22.31},
                "source": "MAST",
                "idx": 0,
            }]

        except Exception as e:
            self.logger.error("tess_archive_failed", error=str(e))
            self.logger.info("falling_back_to_demo")
            return await self._fetch_demo()

    async def _fetch_demo(self, **kwargs) -> list[dict[str, Any]]:
        """Generate TESS-like synthetic demo data."""
        rng = np.random.default_rng(100)
        records = []

        # Generate a transit light curve
        n_points = 2000
        time = np.linspace(0, 27.0, n_points)
        flux = np.ones(n_points) + rng.normal(0, 0.0008, n_points)

        period = 4.72
        depth = 0.008
        t0 = 1.5
        dur_frac = 0.015

        phase = ((time - t0) % period) / period
        in_transit = (phase < dur_frac) | (phase > (1.0 - dur_frac))
        flux[in_transit] -= depth

        records.append({
            "type": "transit",
            "time": time.tolist(),
            "flux": flux.tolist(),
            "target": self.KNOWN_TARGETS[0],
            "injected_period": period,
            "injected_depth": depth,
            "injected_t0": t0,
            "idx": 0,
        })

        return records

    async def normalize(self, raw_data: dict[str, Any]) -> ObservationCreate:
        """Normalize TESS data into common schema."""
        target_info = raw_data["target"]
        idx = raw_data.get("idx", 0)

        metadata = {
            "n_points": len(raw_data["time"]),
            "duration_days": raw_data["time"][-1] - raw_data["time"][0],
            "mission": "TESS",
        }

        if "injected_period" in raw_data:
            metadata["injected_period_days"] = raw_data["injected_period"]
            metadata["injected_depth"] = raw_data["injected_depth"]

        return ObservationCreate(
            source_id="tess",
            record_id=f"TESS-{idx:06d}-{uuid.uuid4().hex[:8]}",
            observed_at=datetime.now(timezone.utc),
            target=TargetInfo(
                name=target_info["name"],
                ra=target_info["ra"],
                dec=target_info["dec"],
            ),
            signal_type="transit",
            raw_payload={
                "time": raw_data["time"],
                "flux": raw_data["flux"],
            },
            preliminary_confidence=None,
            metadata=metadata,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check if MAST archive is reachable."""
        try:
            import lightkurve as lk
            # Quick search to test connectivity
            result = lk.search_lightcurve("TIC 307210830", mission="TESS")
            return {
                "healthy": True,
                "message": f"MAST reachable, {len(result)} results available",
                "source_id": self.source_id,
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"MAST unreachable: {str(e)[:100]}. Demo mode available.",
                "source_id": self.source_id,
            }
