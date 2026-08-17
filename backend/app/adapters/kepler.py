"""
ANVESHAK — Kepler Archive Adapter
Fetches light curves from Kepler archive via lightkurve.
Falls back to demo data if archive is unavailable.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter, register_adapter
from app.schemas.observation import ObservationCreate, TargetInfo


@register_adapter("kepler")
class KeplerAdapter(BaseAdapter):
    """
    Kepler Space Telescope data adapter.

    In archive mode: fetches from MAST via lightkurve.
    Falls back to synthetic demo data if external access fails.
    """

    async def fetch_new(self, mode: str = "demo", **kwargs) -> list[dict[str, Any]]:
        """Fetch Kepler light curve data."""
        if mode == "archive":
            return await self._fetch_archive(**kwargs)
        return await self._fetch_demo(**kwargs)

    async def _fetch_archive(self, target_name: str = None, **kwargs) -> list[dict[str, Any]]:
        """Attempt to fetch from Kepler archive."""
        try:
            import lightkurve as lk

            target = target_name or "KIC 11904151"
            self.logger.info("fetching_kepler_archive", target=target)

            search_result = lk.search_lightcurve(target, mission="Kepler")

            if len(search_result) == 0:
                self.logger.warning("no_kepler_data_found", target=target)
                return await self._fetch_demo()

            lc = search_result[0].download()
            lc = lc.remove_nans().normalize()

            return [{
                "type": "transit",
                "time": lc.time.value.tolist(),
                "flux": lc.flux.value.tolist(),
                "target": {"name": target, "ra": 291.05, "dec": 50.13},
                "source": "Kepler/MAST",
                "idx": 0,
            }]

        except Exception as e:
            self.logger.error("kepler_archive_failed", error=str(e))
            return await self._fetch_demo()

    async def _fetch_demo(self, **kwargs) -> list[dict[str, Any]]:
        """Generate Kepler-like synthetic demo data."""
        rng = np.random.default_rng(200)

        n_points = 3000
        time = np.linspace(0, 90.0, n_points)  # ~1 Kepler quarter
        flux = np.ones(n_points) + rng.normal(0, 0.0005, n_points)

        period = 6.84
        depth = 0.012
        t0 = 2.0
        dur_frac = 0.012

        phase = ((time - t0) % period) / period
        in_transit = (phase < dur_frac) | (phase > (1.0 - dur_frac))
        flux[in_transit] -= depth

        return [{
            "type": "transit",
            "time": time.tolist(),
            "flux": flux.tolist(),
            "target": {"name": "KIC 11904151", "ra": 291.05, "dec": 50.13},
            "injected_period": period,
            "injected_depth": depth,
            "injected_t0": t0,
            "idx": 0,
        }]

    async def normalize(self, raw_data: dict[str, Any]) -> ObservationCreate:
        """Normalize Kepler data into common schema."""
        target_info = raw_data["target"]
        idx = raw_data.get("idx", 0)

        metadata = {
            "n_points": len(raw_data["time"]),
            "duration_days": raw_data["time"][-1] - raw_data["time"][0],
            "mission": "Kepler",
        }

        if "injected_period" in raw_data:
            metadata["injected_period_days"] = raw_data["injected_period"]
            metadata["injected_depth"] = raw_data["injected_depth"]

        return ObservationCreate(
            source_id="kepler",
            record_id=f"KEPLER-{idx:06d}-{uuid.uuid4().hex[:8]}",
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
        """Check Kepler archive availability."""
        try:
            import lightkurve as lk
            result = lk.search_lightcurve("KIC 11904151", mission="Kepler")
            return {
                "healthy": True,
                "message": f"Kepler archive reachable, {len(result)} results",
                "source_id": self.source_id,
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Kepler archive unreachable: {str(e)[:100]}",
                "source_id": self.source_id,
            }
