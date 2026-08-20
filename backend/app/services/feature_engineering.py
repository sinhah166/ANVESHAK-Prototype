"""
ANVESHAK — Feature Engineering Service
Generates scientifically useful derived features from astronomical data.

All derived features are documented with their formulas and physical meaning.
No physically invalid formulas are used.
"""

import math
from typing import Any, Optional

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.db_models import (
    AstronomicalObject,
    EngineeredFeature,
    PlanetParameter,
    StellarParameter,
)

logger = get_logger("service.feature_engineering")

# Feature definitions: name → (description, formula_description)
FEATURE_DEFINITIONS = {
    "log_orbital_period": (
        "Log10 of orbital period in days",
        "log10(orbital_period_days)",
    ),
    "log_planet_radius": (
        "Log10 of planet radius in Earth radii",
        "log10(planet_radius_earth)",
    ),
    "log_planet_mass": (
        "Log10 of planet mass in Earth masses",
        "log10(planet_mass_earth)",
    ),
    "density_estimate": (
        "Estimated bulk density in g/cm³ from mass and radius",
        "mass_earth * 5.51 / radius_earth³ (scaled from Earth's density)",
    ),
    "radius_to_mass_ratio": (
        "Planet radius divided by planet mass (Earth units)",
        "planet_radius_earth / planet_mass_earth",
    ),
    "surface_gravity_planet": (
        "Estimated surface gravity relative to Earth",
        "planet_mass_earth / planet_radius_earth²",
    ),
    "stellar_planet_radius_ratio": (
        "Ratio of stellar radius to planet radius",
        "stellar_radius_solar * 109.076 / planet_radius_earth",
    ),
    "stellar_planet_temp_ratio": (
        "Ratio of stellar temperature to planet equilibrium temperature",
        "effective_temp_k / equilibrium_temp_k",
    ),
    "insolation_proxy": (
        "Approximate insolation flux relative to Earth",
        "(stellar_radius_solar / semi_major_axis_au)² * (effective_temp_k / 5778)⁴",
    ),
    "completeness_score": (
        "Fraction of key parameters that are non-null (0-1)",
        "count(non_null_params) / count(total_key_params)",
    ),
    "transit_signal_strength": (
        "Transit depth normalized by estimated noise (proxy)",
        "transit_depth / (1 / sqrt(orbital_period_days)) where available",
    ),
    "habitable_zone_metric": (
        "Distance metric from conservative habitable zone",
        "Based on equilibrium temperature distance from 200-320K range",
    ),
}

# Key parameters for completeness scoring
COMPLETENESS_PARAMS = [
    "planet_radius_earth",
    "planet_mass_earth",
    "orbital_period_days",
    "semi_major_axis_au",
    "eccentricity",
    "equilibrium_temp_k",
    "effective_temp_k",
    "stellar_radius_solar",
    "stellar_mass_solar",
    "discovery_method",
]


class FeatureEngineeringService:
    """Generates derived scientific features for astronomical objects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_features_for_dataset(self, dataset_id: int) -> dict[str, Any]:
        """Generate engineered features for all objects in a dataset."""
        result = await self.db.execute(
            select(AstronomicalObject)
            .where(AstronomicalObject.dataset_id == dataset_id)
        )
        objects = result.scalars().all()
        logger.info("generating_features", dataset_id=dataset_id, objects=len(objects))

        generated = 0
        for obj in objects:
            count = await self.generate_features_for_object(obj.id)
            generated += count

        await self.db.commit()
        logger.info("feature_generation_complete", total_features=generated)
        return {"objects_processed": len(objects), "features_generated": generated}

    async def generate_features_for_object(self, object_id: int) -> int:
        """Generate all engineered features for a single object."""
        # Load object with relationships
        result = await self.db.execute(
            select(AstronomicalObject)
            .where(AstronomicalObject.id == object_id)
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return 0

        # Load parameters
        pp_result = await self.db.execute(
            select(PlanetParameter).where(PlanetParameter.object_id == object_id)
        )
        pp = pp_result.scalar_one_or_none()

        sp_result = await self.db.execute(
            select(StellarParameter).where(StellarParameter.object_id == object_id)
        )
        sp = sp_result.scalar_one_or_none()

        if not pp:
            return 0

        features = {}

        # Log transforms
        if pp.orbital_period_days and pp.orbital_period_days > 0:
            features["log_orbital_period"] = math.log10(pp.orbital_period_days)

        if pp.planet_radius_earth and pp.planet_radius_earth > 0:
            features["log_planet_radius"] = math.log10(pp.planet_radius_earth)

        if pp.planet_mass_earth and pp.planet_mass_earth > 0:
            features["log_planet_mass"] = math.log10(pp.planet_mass_earth)

        # Density estimate
        if pp.planet_mass_earth and pp.planet_radius_earth and pp.planet_radius_earth > 0:
            # Density = M / (4/3 π R³), scaled from Earth (5.51 g/cm³)
            features["density_estimate"] = (
                pp.planet_mass_earth * 5.51 / (pp.planet_radius_earth ** 3)
            )

        # Radius to mass ratio
        if pp.planet_radius_earth and pp.planet_mass_earth and pp.planet_mass_earth > 0:
            features["radius_to_mass_ratio"] = pp.planet_radius_earth / pp.planet_mass_earth

        # Surface gravity estimate
        if pp.planet_mass_earth and pp.planet_radius_earth and pp.planet_radius_earth > 0:
            features["surface_gravity_planet"] = (
                pp.planet_mass_earth / (pp.planet_radius_earth ** 2)
            )

        # Stellar-planet radius ratio
        if sp and sp.stellar_radius_solar and pp.planet_radius_earth and pp.planet_radius_earth > 0:
            # 1 solar radius ≈ 109.076 earth radii
            features["stellar_planet_radius_ratio"] = (
                sp.stellar_radius_solar * 109.076 / pp.planet_radius_earth
            )

        # Temperature ratio
        if sp and sp.effective_temp_k and pp.equilibrium_temp_k and pp.equilibrium_temp_k > 0:
            features["stellar_planet_temp_ratio"] = (
                sp.effective_temp_k / pp.equilibrium_temp_k
            )

        # Insolation proxy
        if (sp and sp.stellar_radius_solar and sp.effective_temp_k
                and pp.semi_major_axis_au and pp.semi_major_axis_au > 0):
            features["insolation_proxy"] = (
                (sp.stellar_radius_solar / pp.semi_major_axis_au) ** 2
                * (sp.effective_temp_k / 5778.0) ** 4
            )

        # Completeness score
        completeness_count = 0
        total_params = len(COMPLETENESS_PARAMS)
        for param in COMPLETENESS_PARAMS:
            if param == "discovery_method":
                if pp.discovery_method:
                    completeness_count += 1
            else:
                val = getattr(pp, param, None) or (getattr(sp, param, None) if sp else None)
                if val is not None:
                    completeness_count += 1
        features["completeness_score"] = completeness_count / total_params

        # Transit signal strength
        if pp.transit_depth and pp.orbital_period_days and pp.orbital_period_days > 0:
            features["transit_signal_strength"] = (
                pp.transit_depth * math.sqrt(pp.orbital_period_days)
            )

        # Habitable zone metric (distance from 200-320K range)
        if pp.equilibrium_temp_k:
            if 200 <= pp.equilibrium_temp_k <= 320:
                features["habitable_zone_metric"] = 1.0
            elif pp.equilibrium_temp_k < 200:
                features["habitable_zone_metric"] = max(0, 1.0 - (200 - pp.equilibrium_temp_k) / 200)
            else:
                features["habitable_zone_metric"] = max(0, 1.0 - (pp.equilibrium_temp_k - 320) / 1000)

        # Delete existing features for this object
        from sqlalchemy import delete
        await self.db.execute(
            delete(EngineeredFeature).where(EngineeredFeature.object_id == object_id)
        )

        # Save features
        for name, value in features.items():
            if value is not None and not (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
                feat = EngineeredFeature(
                    object_id=object_id,
                    feature_name=name,
                    feature_value=float(value),
                    feature_version="v1",
                )
                self.db.add(feat)

        return len(features)

    def build_feature_matrix(
        self,
        objects_data: list[dict],
        feature_names: Optional[list[str]] = None,
    ) -> tuple[np.ndarray, list[str], list[int]]:
        """
        Build a feature matrix from object data for ML models.

        Args:
            objects_data: List of dicts with object parameters.
            feature_names: Specific features to include. None for defaults.

        Returns:
            (feature_matrix, feature_names, object_ids) tuple.
        """
        if feature_names is None:
            feature_names = [
                "orbital_period_days", "planet_radius_earth", "planet_mass_earth",
                "semi_major_axis_au", "eccentricity", "equilibrium_temp_k",
                "effective_temp_k", "stellar_radius_solar", "stellar_mass_solar",
            ]

        matrix = []
        ids = []
        for obj in objects_data:
            row = []
            for feat in feature_names:
                val = obj.get(feat)
                row.append(float(val) if val is not None else np.nan)
            matrix.append(row)
            ids.append(obj.get("id", 0))

        return np.array(matrix), feature_names, ids

    @staticmethod
    def get_feature_definitions() -> dict[str, tuple[str, str]]:
        """Return feature definitions for documentation/UI."""
        return FEATURE_DEFINITIONS
