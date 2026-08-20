"""
ANVESHAK — NASA Exoplanet Archive Adapter
Implements data ingestion from the NASA Exoplanet Archive TAP service.

Supports:
- PSCompPars (Planetary Systems Composite Parameters)
- KOI (Kepler Objects of Interest)
- Demo mode using local sample CSV files
"""

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from app.adapters.base import BaseDataAdapter, register_adapter
from app.core.config import SAMPLES_DIR, get_settings
from app.core.logging import get_logger
from app.services.nasa_tap import (
    KOI_COLUMN_MAP,
    KOI_COLUMNS,
    PSCOMPPARS_COLUMN_MAP,
    PSCOMPPARS_COLUMNS,
    NASATAPClient,
)

logger = get_logger("adapter.nasa_exoplanet")


@register_adapter("nasa_exoplanet_archive")
class NASAExoplanetArchiveAdapter(BaseDataAdapter):
    """
    Adapter for the NASA Exoplanet Archive.

    In LIVE mode: queries the TAP service directly.
    In DEMO mode: loads from pre-generated CSV files in data/samples/.
    """

    def __init__(self, source_id: str = "nasa_exoplanet_archive", config: dict | None = None):
        super().__init__(source_id, config)
        self.tap_client = NASATAPClient()
        self.settings = get_settings()

    async def fetch_schema(self, table: str) -> pd.DataFrame:
        """Inspect the schema of a NASA TAP table."""
        if self.settings.data_mode == "demo":
            # Return schema from sample file columns
            sample_path = self._get_sample_path(table)
            if sample_path.exists():
                df = pd.read_csv(sample_path, nrows=0)
                return pd.DataFrame({
                    "column_name": df.columns.tolist(),
                    "datatype": ["VARCHAR"] * len(df.columns),
                    "description": [""] * len(df.columns),
                })
            return pd.DataFrame(columns=["column_name", "datatype", "description"])

        return await self.tap_client.inspect_schema(table)

    async def fetch_data(
        self,
        table: str,
        max_records: int = 2000,
        where: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch data from NASA TAP or local sample files.

        Args:
            table: Table name ('pscomppars', 'koi', 'ps').
            max_records: Maximum records to retrieve.
            where: Additional WHERE clause filter.

        Returns:
            Raw DataFrame from the source.
        """
        if self.settings.data_mode == "demo":
            return self._load_sample_data(table, max_records)

        # LIVE mode — query NASA TAP
        if table == "pscomppars":
            df = await self.tap_client.fetch_pscomppars(
                max_records=max_records,
                where=where,
            )
        elif table == "koi":
            df = await self.tap_client.fetch_koi(
                max_records=max_records,
                where=where,
            )
        else:
            df = await self.tap_client.fetch_table(
                table=table,
                max_records=max_records,
                where=where,
            )

        self.logger.info("fetched_data", table=table, rows=len(df))
        return df

    def validate(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Validate a DataFrame for data quality issues.

        Returns validation report including:
        - Expected columns present
        - Null ratios per column
        - Data type issues
        - Duplicate check
        - Value range issues
        """
        report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "issues": [],
            "warnings": [],
            "null_ratios": {},
            "duplicates": 0,
            "is_valid": True,
        }

        if len(df) == 0:
            report["issues"].append("DataFrame is empty")
            report["is_valid"] = False
            return report

        # Null ratio analysis
        for col in df.columns:
            null_ratio = df[col].isna().sum() / len(df)
            report["null_ratios"][col] = round(float(null_ratio), 4)
            if null_ratio > 0.95:
                report["warnings"].append(f"Column '{col}' is >95% null ({null_ratio:.1%})")

        # Duplicate check on planet name or external ID
        id_col = None
        for candidate in ["pl_name", "kepoi_name", "external_id", "planet_name"]:
            if candidate in df.columns:
                id_col = candidate
                break

        if id_col:
            dupes = df[id_col].duplicated().sum()
            report["duplicates"] = int(dupes)
            if dupes > 0:
                report["warnings"].append(f"{dupes} duplicate entries in '{id_col}'")

        # Check for obviously invalid values
        numeric_checks = {
            "pl_rade": (0, 100, "Planet radius"),
            "planet_radius_earth": (0, 100, "Planet radius"),
            "pl_orbper": (0, 1e8, "Orbital period"),
            "orbital_period_days": (0, 1e8, "Orbital period"),
            "pl_bmasse": (0, 1e6, "Planet mass"),
            "planet_mass_earth": (0, 1e6, "Planet mass"),
            "st_teff": (100, 100000, "Stellar temperature"),
            "effective_temp_k": (100, 100000, "Stellar temperature"),
        }

        for col, (vmin, vmax, label) in numeric_checks.items():
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")
                invalid = ((series < vmin) | (series > vmax)).sum()
                if invalid > 0:
                    report["warnings"].append(
                        f"{invalid} values in '{col}' outside expected range [{vmin}, {vmax}] for {label}"
                    )

        return report

    def normalize(self, df: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
        """
        Normalize column names from NASA TAP schema to ANVESHAK internal names.

        Args:
            df: Raw DataFrame.
            column_map: Mapping from source columns to internal names.

        Returns:
            DataFrame with renamed columns.
        """
        # Only rename columns that exist
        rename_map = {k: v for k, v in column_map.items() if k in df.columns}
        normalized = df.rename(columns=rename_map)

        # Drop columns not in the map (keep unmapped ones for now)
        self.logger.info(
            "normalized_columns",
            mapped=len(rename_map),
            total=len(df.columns),
        )
        return normalized

    def get_metadata(self) -> dict[str, Any]:
        """Return NASA Exoplanet Archive source metadata."""
        return {
            "name": "NASA Exoplanet Archive",
            "type": "tap",
            "base_url": self.tap_client.base_url,
            "description": (
                "The NASA Exoplanet Archive is an online astronomical exoplanet "
                "and stellar catalog and data service that collects and cross-correlates "
                "astronomical data and information on exoplanets."
            ),
            "tables": ["pscomppars", "ps", "koi"],
        }

    async def health_check(self) -> dict[str, Any]:
        """Check if NASA TAP endpoint is reachable."""
        if self.settings.data_mode == "demo":
            sample_exists = self._get_sample_path("pscomppars").exists()
            return {
                "healthy": sample_exists,
                "source_id": self.source_id,
                "mode": "demo",
                "message": "Demo sample data available" if sample_exists else "Demo sample data missing",
            }

        try:
            count = await self.tap_client.get_table_count("pscomppars", "default_flag = 1")
            return {
                "healthy": True,
                "source_id": self.source_id,
                "mode": "live",
                "total_records": count,
            }
        except Exception as e:
            return {
                "healthy": False,
                "source_id": self.source_id,
                "mode": "live",
                "error": str(e),
            }

    def _get_sample_path(self, table: str) -> Path:
        """Get the path to a sample CSV file."""
        return SAMPLES_DIR / f"{table}_sample.csv"

    def _load_sample_data(self, table: str, max_records: int) -> pd.DataFrame:
        """Load sample data from local CSV files for demo mode."""
        sample_path = self._get_sample_path(table)
        if not sample_path.exists():
            self.logger.warning("sample_data_not_found", path=str(sample_path))
            return pd.DataFrame()

        df = pd.read_csv(sample_path)
        if max_records and len(df) > max_records:
            df = df.head(max_records)

        self.logger.info(
            "loaded_sample_data",
            table=table,
            rows=len(df),
            path=str(sample_path),
        )
        return df

    def get_column_map(self, table: str) -> dict[str, str]:
        """Get the column mapping for a specific table."""
        if table == "pscomppars" or table == "ps":
            return PSCOMPPARS_COLUMN_MAP
        elif table == "koi":
            return KOI_COLUMN_MAP
        else:
            return {}
