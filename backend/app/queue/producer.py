"""
ANVESHAK — Event Producer
Publishes events to Redis Streams.
"""

import json
from typing import Any

from app.core.logging import get_logger
from app.queue.redis_client import get_redis_client

logger = get_logger("queue.producer")

# Stream names
STREAM_OBSERVATIONS = "anveshak:observations"
STREAM_CANDIDATES = "anveshak:candidates"
STREAM_ALERTS = "anveshak:alerts"


async def publish_event(stream_name: str, event_data: dict[str, Any]) -> Optional[str]:
    """
    Publish an event to a Redis Stream.
    
    Args:
        stream_name: Name of the Redis stream.
        event_data: Dictionary containing event data.
        
    Returns:
        Message ID if successful, None otherwise.
    """
    try:
        client = await get_redis_client()
        # Convert all values to strings for Redis Streams
        payload = {k: json.dumps(v) if isinstance(v, (dict, list, bool)) else str(v) 
                  for k, v in event_data.items()}
        
        msg_id = await client.xadd(stream_name, payload, maxlen=10000)
        return msg_id
    except Exception as e:
        logger.error("redis_publish_failed", stream=stream_name, error=str(e))
        return None


async def publish_observation(observation_id: int, source_id: str) -> None:
    """Publish a new observation event."""
    await publish_event(
        STREAM_OBSERVATIONS,
        {"event": "new_observation", "observation_id": observation_id, "source_id": source_id}
    )


async def publish_candidate(candidate_id: int, classification: str, confidence: float) -> None:
    """Publish a new candidate event."""
    await publish_event(
        STREAM_CANDIDATES,
        {
            "event": "new_candidate",
            "candidate_id": candidate_id,
            "classification": classification,
            "confidence": confidence
        }
    )
