"""
ANVESHAK — WebSocket API
Real-time streaming of events to connected clients.
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.queue.consumer import consume_stream
from app.queue.producer import STREAM_CANDIDATES

logger = get_logger("api.websocket")
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections for the dashboard."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._consumer_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_client_connected", total_clients=len(self.active_connections))
        
        # Start background Redis consumer if not already running
        if self._consumer_task is None or self._consumer_task.done():
            self._consumer_task = asyncio.create_task(self._start_redis_consumer())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("websocket_client_disconnected", total_clients=len(self.active_connections))
            
            # Stop consumer if no clients left
            if not self.active_connections and self._consumer_task:
                self._consumer_task.cancel()
                self._consumer_task = None

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        text_data = json.dumps(message)
        
        # Create list of tasks for parallel broadcasting
        tasks = []
        for connection in self.active_connections:
            tasks.append(connection.send_text(text_data))
            
        if tasks:
            # Run concurrently and ignore errors (disconnected clients)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Clean up failed connections
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    try:
                        self.active_connections[i].close()
                    except Exception:
                        pass
                    if self.active_connections[i] in self.active_connections:
                        self.active_connections.remove(self.active_connections[i])

    async def _start_redis_consumer(self):
        """Background task that reads from Redis and broadcasts to WebSockets."""
        logger.info("starting_websocket_redis_consumer")
        try:
            await consume_stream(
                stream_name=STREAM_CANDIDATES,
                group_name="dashboard_group",
                consumer_name="ws_broadcaster",
                callback=self._handle_redis_message
            )
        except asyncio.CancelledError:
            logger.info("websocket_redis_consumer_stopped")
        except Exception as e:
            logger.error("websocket_redis_consumer_failed", error=str(e))
            self._consumer_task = None

    async def _handle_redis_message(self, msg_id: str, payload: dict):
        """Process a message from Redis and broadcast it."""
        try:
            # Decode payload
            event_data = {k: json.loads(v) if v.startswith(('{', '[')) else v for k, v in payload.items()}
            
            # Reconstruct numeric types if needed
            if "candidate_id" in event_data and isinstance(event_data["candidate_id"], str):
                event_data["candidate_id"] = int(event_data["candidate_id"])
            if "confidence" in event_data and isinstance(event_data["confidence"], str):
                event_data["confidence"] = float(event_data["confidence"])
                
            await self.broadcast(event_data)
        except Exception as e:
            logger.error("failed_to_broadcast_message", error=str(e))


manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard events."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open, wait for client messages (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning("websocket_error", error=str(e))
        manager.disconnect(websocket)
