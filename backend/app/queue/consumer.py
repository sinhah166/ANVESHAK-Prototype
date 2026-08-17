"""
ANVESHAK — Event Consumer
Reads events from Redis Streams.
"""

import asyncio
from typing import Any, Callable

from app.core.logging import get_logger
from app.queue.redis_client import get_redis_client

logger = get_logger("queue.consumer")


async def consume_stream(
    stream_name: str,
    group_name: str,
    consumer_name: str,
    callback: Callable[[str, dict[str, Any]], Any],
) -> None:
    """
    Consume events from a Redis Stream using a consumer group.
    
    Args:
        stream_name: Name of the stream to read from.
        group_name: Consumer group name.
        consumer_name: Unique name for this consumer.
        callback: Async function to process each message.
    """
    client = await get_redis_client()
    from app.queue.producer import _memory_streams
    
    try:
        # Ensure stream and group exist in Redis
        await client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        logger.info("created_consumer_group", stream=stream_name, group=group_name)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            logger.warning("redis_not_available_using_memory_fallback", error=str(e))
            # Memory fallback loop
            if stream_name not in _memory_streams:
                _memory_streams[stream_name] = asyncio.Queue()
            
            logger.info("starting_memory_consumer", stream=stream_name)
            while True:
                try:
                    msg_id, payload = await _memory_streams[stream_name].get()
                    await callback(msg_id, payload)
                except asyncio.CancelledError:
                    break
                except Exception as mem_err:
                    logger.error("memory_consumer_error", error=str(mem_err))
            return
            
    logger.info("starting_redis_consumer", stream=stream_name, consumer=consumer_name)
    
    while True:
        try:
            # Read new messages
            messages = await client.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: ">"},
                count=10,
                block=2000
            )
            
            for stream, msgs in messages:
                for msg_id, payload in msgs:
                    try:
                        # Process message
                        await callback(msg_id, payload)
                        # Acknowledge message
                        await client.xack(stream_name, group_name, msg_id)
                    except Exception as e:
                        logger.error(
                            "message_processing_failed",
                            msg_id=msg_id,
                            error=str(e)
                        )
                        
        except asyncio.CancelledError:
            logger.info("consumer_cancelled", stream=stream_name)
            break
        except Exception as e:
            logger.error("consumer_error", stream=stream_name, error=str(e))
            await asyncio.sleep(5)  # Backoff on error
