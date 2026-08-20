"""
ANVESHAK — NASA Exoplanet Archive TAP Client
Reusable client for querying the NASA TAP service with ADQL.
"""

import csv
import io
import time
from typing import Any, Optional

import httpx
import pandas as pd

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("service.nasa_tap")

# Column mapping from NASA TAP schema to ANVESHAK internal names
PSCOMPPARS_COLUMN_MAP = {
    # Identity
    "pl_name": "planet_name",
    "hostname": "host_name",
    "default_flag": "default_flag",
    "ra": "ra",
    "dec": "dec",
    "disc_method": "discovery_method",    # not disc_method
    "discoverymethod": "discovery_method",
    "disc_facility": "discovery_facility",
    "disc_year": "discovery_year",
    # Planet parameters
    "pl_rade": "planet_radius_earth",
    "pl_bmasse": "planet_mass_earth",
    "pl_orbper": "orbital_period_days",
    "pl_orbsmax": "semi_major_axis_au",
    "pl_orbeccen": "eccentricity",
    "pl_dens": "density_g_cm3",
    "pl_eqt": "equilibrium_temp_k",
    "pl_trandep": "transit_depth",
    "pl_trandur": "transit_duration_hrs",
    "pl_orbincl": "inclination_deg",
    # Stellar parameters
    "st_teff": "effective_temp_k",
    "st_rad": "stellar_radius_solar",
    "st_mass": "stellar_mass_solar",
    "st_met": "metallicity_fe_h",
    "st_logg": "surface_gravity_log_cgs",
    "st_lum": "luminosity_solar",
    "st_spectype": "spectral_type",
}

KOI_COLUMN_MAP = {
    "kepoi_name": "external_id",
    "kepler_name": "planet_name",
    "koi_disposition": "disposition",
    "koi_pdisposition": "pdisposition",
    "ra": "ra",
    "dec": "dec",
    "koi_period": "orbital_period_days",
    "koi_prad": "planet_radius_earth",
    "koi_depth": "transit_depth",
    "koi_duration": "transit_duration_hrs",
    "koi_teq": "equilibrium_temp_k",
    "koi_insol": "insolation_flux",
    "koi_steff": "effective_temp_k",
    "koi_srad": "stellar_radius_solar",
    "koi_smass": "stellar_mass_solar",
    "koi_slogg": "surface_gravity_log_cgs",
    "koi_impact": "impact_parameter",
    "koi_eccen": "eccentricity",
    "koi_model_snr": "model_snr",
    "koi_score": "koi_score",
}
# NOTE: The KOI data lives in the TAP table named "cumulative", not "koi"
KOI_TAP_TABLE = "cumulative"

# Default columns to fetch for each table
PSCOMPPARS_COLUMNS = [
    "pl_name", "hostname", "default_flag", "ra", "dec",
    "discoverymethod", "disc_facility", "disc_year",
    "pl_rade", "pl_bmasse", "pl_orbper", "pl_orbsmax",
    "pl_orbeccen", "pl_dens", "pl_eqt",
    "pl_trandep", "pl_trandur", "pl_orbincl",
    "st_teff", "st_rad", "st_mass", "st_met", "st_logg", "st_lum", "st_spectype",
]

KOI_COLUMNS = [
    "kepoi_name", "kepler_name", "koi_disposition", "koi_pdisposition",
    "ra", "dec",
    "koi_period", "koi_prad", "koi_depth", "koi_duration",
    "koi_teq", "koi_insol",
    "koi_steff", "koi_srad", "koi_smass", "koi_slogg",
    "koi_impact", "koi_eccen", "koi_model_snr", "koi_score",
]


class NASATAPClient:
    """
    Reusable client for the NASA Exoplanet Archive TAP service.

    Supports:
    - ADQL queries
    - Table/column selection
    - WHERE filters
    - Bounded retrieval (TOP N)
    - CSV response parsing
    - Retry logic with exponential backoff
    - Timeout handling
    - Schema inspection
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        settings = get_settings()
        self.base_url = base_url or settings.nasa_tap_url
        self.sync_url = f"{self.base_url}/sync"
        self.timeout = timeout
        self.max_retries = max_retries

    def _build_adql(
        self,
        table: str,
        columns: Optional[list[str]] = None,
        where: Optional[str] = None,
        top: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> str:
        """Build an ADQL query string."""
        col_str = ", ".join(columns) if columns else "*"
        top_str = f"TOP {top} " if top else ""
        query = f"SELECT {top_str}{col_str} FROM {table}"
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        return query

    async def execute_query(
        self,
        query: str,
        format: str = "csv",
    ) -> pd.DataFrame:
        """
        Execute an ADQL query against the TAP sync endpoint.

        Args:
            query: ADQL query string.
            format: Response format ('csv' or 'json').

        Returns:
            DataFrame with query results.
        """
        params = {
            "query": query,
            "format": format,
        }

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "tap_query_attempt",
                    attempt=attempt,
                    query=query[:200],
                )
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(self.sync_url, params=params)
                    response.raise_for_status()

                    if format == "csv":
                        df = pd.read_csv(io.StringIO(response.text))
                    else:
                        df = pd.DataFrame(response.json())

                    logger.info(
                        "tap_query_success",
                        rows=len(df),
                        columns=len(df.columns),
                    )
                    return df

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning("tap_timeout", attempt=attempt, error=str(e))
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code == 429:
                    # Rate limited — wait longer
                    wait = 2 ** attempt * 2
                    logger.warning("tap_rate_limited", wait=wait)
                    await self._async_sleep(wait)
                elif e.response.status_code >= 500:
                    logger.warning("tap_server_error", status=e.response.status_code)
                else:
                    raise  # Client errors should not retry
            except Exception as e:
                last_exception = e
                logger.warning("tap_request_failed", attempt=attempt, error=str(e))

            if attempt < self.max_retries:
                wait = 2 ** attempt
                logger.info("tap_retry_wait", seconds=wait)
                await self._async_sleep(wait)

        raise ConnectionError(
            f"Failed to query NASA TAP after {self.max_retries} attempts: {last_exception}"
        )

    async def _async_sleep(self, seconds: float):
        """Async sleep helper."""
        import asyncio
        await asyncio.sleep(seconds)

    async def fetch_table(
        self,
        table: str,
        columns: Optional[list[str]] = None,
        where: Optional[str] = None,
        max_records: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch data from a specific TAP table.

        Args:
            table: Table name (e.g., 'pscomppars', 'ps', 'koi').
            columns: List of columns to select. None for all.
            where: WHERE clause filter.
            max_records: Maximum number of records (uses TOP).
            order_by: ORDER BY clause.

        Returns:
            DataFrame with results.
        """
        query = self._build_adql(
            table=table,
            columns=columns,
            where=where,
            top=max_records,
            order_by=order_by,
        )
        return await self.execute_query(query)

    async def fetch_pscomppars(
        self,
        max_records: int = 2000,
        where: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch from the Planetary Systems Composite Parameters table."""
        return await self.fetch_table(
            table="pscomppars",
            columns=PSCOMPPARS_COLUMNS,
            where=where,
            max_records=max_records,
            order_by="pl_name",
        )

    async def fetch_koi(
        self,
        max_records: int = 2000,
        where: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch from the Kepler Objects of Interest (cumulative) table."""
        return await self.fetch_table(
            table=KOI_TAP_TABLE,
            columns=KOI_COLUMNS,
            where=where,
            max_records=max_records,
            order_by="kepoi_name",
        )

    async def inspect_schema(self, table: str) -> pd.DataFrame:
        """
        Inspect the schema of a TAP table.

        Returns DataFrame with column names, descriptions, data types.
        """
        query = f"""
        SELECT column_name, datatype, description, unit
        FROM TAP_SCHEMA.columns
        WHERE table_name = '{table}'
        ORDER BY column_name
        """
        return await self.execute_query(query)

    async def get_table_count(self, table: str, where: Optional[str] = None) -> int:
        """Get the total number of rows in a table."""
        query = f"SELECT COUNT(*) as cnt FROM {table}"
        if where:
            query += f" WHERE {where}"
        df = await self.execute_query(query)
        return int(df.iloc[0]["cnt"])

    def get_query_metadata(self, table: str, query: str) -> dict[str, Any]:
        """Build metadata dict for a query."""
        return {
            "source": "NASA Exoplanet Archive",
            "tap_url": self.base_url,
            "table": table,
            "query": query,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
