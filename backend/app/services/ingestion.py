"""
ANVESHAK — Ingestion Service
Orchestrates data ingestion from NASA TAP to PostgreSQL.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.nasa_exoplanet import NASAExoplanetArchiveAdapter
from app.core.config import RAW_DATA_DIR, get_settings
from app.core.logging import get_logger
from app.models.db_models import (
    AnalysisJob,
    AstronomicalObject,
    Dataset,
    PlanetParameter,
    Source,
    StellarParameter,
)
from app.services.nasa_tap import PSCOMPPARS_COLUMN_MAP, KOI_COLUMN_MAP

logger = get_logger("service.ingestion")


class IngestionService:
    """Orchestrates the full data ingestion pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.adapter = NASAExoplanetArchiveAdapter()
        self.settings = get_settings()

    async def ensure_source_exists(self) -> Source:
        """Ensure the NASA Exoplanet Archive source exists in DB."""
        result = await self.db.execute(
            select(Source).where(Source.name == "NASA Exoplanet Archive")
        )
        source = result.scalar_one_or_none()
        if not source:
            source = Source(
                name="NASA Exoplanet Archive",
                type="tap",
                description="NASA Exoplanet Archive TAP service providing confirmed exoplanets and candidates.",
                base_url=self.settings.nasa_tap_url,
                active=True,
            )
            self.db.add(source)
            await self.db.commit()
            await self.db.refresh(source)
        return source

    async def ingest_dataset(
        self,
        table: str = "pscomppars",
        max_records: int = 2000,
        where: Optional[str] = None,
        job_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Full ingestion pipeline for a NASA TAP table.

        Steps:
        1. Ensure source exists
        2. Create dataset record
        3. Fetch data (live or demo)
        4. Save raw CSV
        5. Validate
        6. Normalize columns
        7. Clean data
        8. Persist to DB (objects + planet params + stellar params)
        9. Update dataset status

        Returns summary dict.
        """
        source = await self.ensure_source_exists()

        # Create dataset record
        query_str = f"SELECT TOP {max_records} ... FROM {table}"
        if where:
            query_str += f" WHERE {where}"

        dataset = Dataset(
            source_id=source.id,
            name=f"{table}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            source_table=table,
            version="v1",
            query_used=query_str,
            ingestion_status="running",
            ingestion_started_at=datetime.now(timezone.utc),
        )
        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)

        await self._update_job_progress(job_id, 10.0, "Fetching data...")

        try:
            # Fetch data
            df = await self.adapter.fetch_data(
                table=table,
                max_records=max_records,
                where=where,
            )

            if df.empty:
                dataset.ingestion_status = "completed"
                dataset.record_count = 0
                dataset.ingestion_completed_at = datetime.now(timezone.utc)
                await self.db.commit()
                return {"status": "completed", "records": 0, "message": "No data returned"}

            await self._update_job_progress(job_id, 20.0, f"Fetched {len(df)} rows")

            # Save raw data
            raw_path = RAW_DATA_DIR / f"{table}_{dataset.id}.csv"
            df.to_csv(raw_path, index=False)
            logger.info("saved_raw_data", path=str(raw_path), rows=len(df))

            await self._update_job_progress(job_id, 30.0, "Validating data...")

            # Validate
            validation = self.adapter.validate(df)
            logger.info("validation_report", **{k: v for k, v in validation.items() if k != "null_ratios"})

            await self._update_job_progress(job_id, 40.0, "Normalizing columns...")

            # Normalize columns
            column_map = self.adapter.get_column_map(table)
            df_norm = self.adapter.normalize(df, column_map)

            await self._update_job_progress(job_id, 50.0, "Cleaning data...")

            # Clean data
            df_clean = self._clean_data(df_norm, table)

            await self._update_job_progress(job_id, 60.0, "Persisting to database...")

            # Persist to DB
            count = await self._persist_objects(df_clean, dataset, table)

            await self._update_job_progress(job_id, 95.0, "Finalizing...")

            # Update dataset status
            dataset.ingestion_status = "completed"
            dataset.record_count = count
            dataset.ingestion_completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            await self._update_job_progress(job_id, 100.0, "Completed")

            return {
                "status": "completed",
                "dataset_id": dataset.id,
                "records": count,
                "table": table,
                "validation": validation,
            }

        except Exception as e:
            logger.error("ingestion_failed", error=str(e))
            dataset.ingestion_status = "failed"
            dataset.error_message = str(e)[:500]
            dataset.ingestion_completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            raise

    def _clean_data(self, df: pd.DataFrame, table: str) -> pd.DataFrame:
        """
        Clean and preprocess the normalized DataFrame.

        - Remove rows without a name identifier
        - Handle missing values (keep nulls for scientific accuracy)
        - Remove physically impossible values
        - Deduplicate by name
        """
        df = df.copy()

        # Determine name column
        if "planet_name" in df.columns:
            name_col = "planet_name"
        elif "external_id" in df.columns:
            name_col = "external_id"
        else:
            return df

        # Remove rows with no identifier
        df = df.dropna(subset=[name_col])

        # Deduplicate — keep first occurrence
        before = len(df)
        df = df.drop_duplicates(subset=[name_col], keep="first")
        dupes = before - len(df)
        if dupes > 0:
            logger.info("removed_duplicates", count=dupes)

        # Remove physically impossible values (but NOT astronomical outliers)
        # Negative radius/mass/period are measurement errors, not real
        for col in ["planet_radius_earth", "planet_mass_earth", "orbital_period_days",
                     "stellar_radius_solar", "stellar_mass_solar"]:
            if col in df.columns:
                df.loc[df[col] < 0, col] = None

        # Negative temperature is impossible
        for col in ["effective_temp_k", "equilibrium_temp_k"]:
            if col in df.columns:
                df.loc[df[col] < 0, col] = None

        logger.info("cleaned_data", rows=len(df))
        return df

    async def _persist_objects(
        self,
        df: pd.DataFrame,
        dataset: Dataset,
        table: str,
    ) -> int:
        """Persist cleaned DataFrame rows as AstronomicalObjects with parameters."""
        count = 0

        for _, row in df.iterrows():
            try:
                # Determine object properties based on table
                if table in ("pscomppars", "ps"):
                    name = str(row.get("planet_name", ""))
                    host = str(row.get("host_name", "")) if pd.notna(row.get("host_name")) else None
                    ext_id = name
                    obj_type = "confirmed"  # pscomppars contains confirmed planets
                elif table in ("cumulative", "koi"):
                    name = str(row.get("external_id", row.get("kepoi_name", "")))
                    host = str(row.get("planet_name", "")) if pd.notna(row.get("planet_name")) else None
                    ext_id = name
                    disposition = str(row.get("disposition", "")).upper()
                    if "CONFIRMED" in disposition:
                        obj_type = "confirmed"
                    elif "CANDIDATE" in disposition:
                        obj_type = "candidate"
                    elif "FALSE" in disposition:
                        obj_type = "false_positive"
                    else:
                        obj_type = "candidate"
                else:
                    name = str(row.iloc[0])
                    ext_id = name
                    host = None
                    obj_type = "unknown"

                if not name or name == "nan":
                    continue

                # Check for existing object
                existing = await self.db.execute(
                    select(AstronomicalObject).where(
                        AstronomicalObject.external_id == ext_id,
                        AstronomicalObject.dataset_id == dataset.id,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                obj = AstronomicalObject(
                    dataset_id=dataset.id,
                    source="nasa_exoplanet_archive",
                    external_id=ext_id,
                    object_type=obj_type,
                    name=name,
                    host_name=host,
                    ra=self._safe_float(row.get("ra")),
                    dec=self._safe_float(row.get("dec")),
                )
                self.db.add(obj)
                await self.db.flush()

                # Planet parameters
                pp = PlanetParameter(
                    object_id=obj.id,
                    planet_radius_earth=self._safe_float(row.get("planet_radius_earth")),
                    planet_mass_earth=self._safe_float(row.get("planet_mass_earth")),
                    orbital_period_days=self._safe_float(row.get("orbital_period_days")),
                    semi_major_axis_au=self._safe_float(row.get("semi_major_axis_au")),
                    eccentricity=self._safe_float(row.get("eccentricity")),
                    density_g_cm3=self._safe_float(row.get("density_g_cm3")),
                    equilibrium_temp_k=self._safe_float(row.get("equilibrium_temp_k")),
                    transit_depth=self._safe_float(row.get("transit_depth")),
                    transit_duration_hrs=self._safe_float(row.get("transit_duration_hrs")),
                    inclination_deg=self._safe_float(row.get("inclination_deg")),
                    discovery_method=self._safe_str(row.get("discovery_method")),
                    discovery_facility=self._safe_str(row.get("discovery_facility")),
                    discovery_year=self._safe_int(row.get("discovery_year")),
                )
                self.db.add(pp)

                # Stellar parameters
                sp = StellarParameter(
                    object_id=obj.id,
                    effective_temp_k=self._safe_float(row.get("effective_temp_k")),
                    stellar_radius_solar=self._safe_float(row.get("stellar_radius_solar")),
                    stellar_mass_solar=self._safe_float(row.get("stellar_mass_solar")),
                    metallicity_fe_h=self._safe_float(row.get("metallicity_fe_h")),
                    surface_gravity_log_cgs=self._safe_float(row.get("surface_gravity_log_cgs")),
                    luminosity_solar=self._safe_float(row.get("luminosity_solar")),
                    spectral_type=self._safe_str(row.get("spectral_type")),
                )
                self.db.add(sp)

                count += 1

                # Batch commit every 100 records
                if count % 100 == 0:
                    await self.db.commit()
                    logger.info("persisted_batch", count=count)

            except Exception as e:
                logger.warning("persist_row_failed", error=str(e))
                continue

        await self.db.commit()
        logger.info("persist_complete", total=count)
        return count

    async def _update_job_progress(
        self,
        job_id: Optional[int],
        progress: float,
        message: str,
    ):
        """Update job progress if a job_id is provided."""
        if job_id is None:
            return
        try:
            result = await self.db.execute(
                select(AnalysisJob).where(AnalysisJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            if job:
                job.progress = progress
                if progress >= 100.0:
                    job.status = "completed"
                    job.completed_at = datetime.now(timezone.utc)
                    job.result_summary = {"message": message}
                await self.db.commit()
        except Exception as e:
            logger.warning("job_progress_update_failed", error=str(e))

    @staticmethod
    def _safe_float(val) -> Optional[float]:
        """Safely convert to float, returning None for invalid values."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        try:
            v = float(val)
            if pd.isna(v):
                return None
            return v
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(val) -> Optional[int]:
        """Safely convert to int."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_str(val) -> Optional[str]:
        """Safely convert to string."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        s = str(val).strip()
        return s if s and s.lower() != "nan" else None
