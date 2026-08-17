"""
ANVESHAK — Redis Client
Async Redis connection management.
"""

from typing import Optional

from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("queue.redis")

_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """Get or create the async Redis client."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            health_check_interval=30,
        )
        logger.info("redis_client_initialized", url=settings.redis_url)
    return _redis_client


async def close_redis_client():
    """Close the Redis client connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def check_redis_health() -> bool:
    """Check if Redis is reachable."""
    try:
        client = await get_redis_client()
        return await client.ping()
    except Exception as e:
        logger.warning("redis_health_check_failed", error=str(e))
        return False
