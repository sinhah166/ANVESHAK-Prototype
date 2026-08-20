"""
ANVESHAK — Demo Data Generator
Fetches sample data from NASA Exoplanet Archive and saves as CSV for demo mode.

Usage:
    python scripts/generate_demo_data.py

This creates:
    data/samples/pscomppars_sample.csv  (~1500 rows)
    data/samples/koi_sample.csv         (~500 rows)
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.nasa_tap import NASATAPClient, PSCOMPPARS_COLUMNS, KOI_COLUMNS


async def generate():
    client = NASATAPClient(timeout=120.0)
    samples_dir = Path(__file__).parent.parent / "data" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch PSCompPars — confirmed exoplanets with default parameters
    print("Fetching PSCompPars data from NASA TAP...")
    try:
        df_ps = await client.fetch_pscomppars(max_records=1500)
        out_ps = samples_dir / "pscomppars_sample.csv"
        df_ps.to_csv(out_ps, index=False)
        print(f"  Saved {len(df_ps)} rows to {out_ps}")
    except Exception as e:
        print(f"  ERROR fetching PSCompPars: {e}")

    # 2. Fetch KOI — Kepler Objects of Interest with dispositions
    print("Fetching KOI data from NASA TAP...")
    try:
        df_koi = await client.fetch_koi(max_records=1500)
        out_koi = samples_dir / "koi_sample.csv"
        df_koi.to_csv(out_koi, index=False)
        print(f"  Saved {len(df_koi)} rows to {out_koi}")
    except Exception as e:
        print(f"  ERROR fetching KOI: {e}")

    print("Done! Sample data is ready for demo mode.")


if __name__ == "__main__":
    asyncio.run(generate())
