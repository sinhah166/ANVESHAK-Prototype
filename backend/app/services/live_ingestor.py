"""
ANVESHAK — Live Ingestor
Continuously pulls real data from the NASA MAST API (via Lightkurve) 
and streams it into the pipeline to simulate real-time live telescope operations.
"""

import asyncio
import random
from datetime import datetime, timezone

from app.adapters.tess import TessAdapter
from app.core.logging import get_logger
from app.services.pipeline_service import PipelineService
from app.models.database import get_session_factory

logger = get_logger("service.ingestor")

# Famous exoplanet host stars and eclipsing binaries to search in MAST
TARGET_STARS = [
    "Pi Mensae",      # Bright star with a known super-Earth
    "TRAPPIST-1",     # Famous 7-planet system
    "WASP-12",        # Hot Jupiter
    "Kepler-90",      # 8-planet system
    "LHS 1140",       # Rocky super-Earth in habitable zone
    "K2-18",          # Habitable zone planet with water vapor
    "HD 209458",      # First transiting exoplanet discovered
]


async def run_continuous_ingestor():
    """
    Background worker that continuously fetches data for random targets 
    and feeds it into the ANVESHAK pipeline.
    """
    logger.info("live_ingestor_started", targets=len(TARGET_STARS))
    adapter = TessAdapter(source_id="tess_live")
    
    SessionLocal = get_session_factory()
    
    while True:
        target = random.choice(TARGET_STARS)
        logger.info("ingestor_fetching_target", target=target)
        
        try:
            # Overwrite the adapter's target for this run
            adapter.target_name = target
            
            # Fetch from MAST API
            observations = await adapter.fetch_and_normalize(mode="archive")
            
            if observations:
                logger.info("ingestor_fetched_data", target=target, records=len(observations))
                
                # Push through pipeline
                async with SessionLocal() as db:
                    pipeline = PipelineService(db)
                    
                    # We stream them one by one to simulate live data
                    for obs in observations:
                        await pipeline.process_observation(obs)
                        # Sleep to simulate real-time telemetry downlink
                        await asyncio.sleep(3.0)
            else:
                logger.warning("ingestor_no_data", target=target)
                
        except Exception as e:
            logger.error("ingestor_error", target=target, error=str(e))
            
        # Wait before querying the next star to avoid rate limits
        await asyncio.sleep(10.0)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_continuous_ingestor())
