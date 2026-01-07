"""
WebSocket handler for real-time frontend updates.

Forwards Redis events to connected WebSocket clients.
"""
import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .event_bus import Event

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        data = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        self.active_connections -= disconnected

    async def send_to(self, websocket: WebSocket, message: Dict):
        """Send message to specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send to client: {e}")


manager = ConnectionManager()


def setup_event_handlers(event_bus):
    """Set up event bus handlers to forward to WebSocket clients."""

    async def on_status_update(event: Event):
        """Forward status updates to clients."""
        await manager.broadcast({
            "type": "status_update",
            "stream_id": event.stream_id,
            "severity": event.data.get("severity"),
            "icon": event.data.get("icon"),
            "description": event.data.get("description"),
            "timestamp": event.timestamp.isoformat()
        })

    async def on_alert(event: Event):
        """Forward alerts to clients."""
        await manager.broadcast({
            "type": "alert_new",
            "alert": event.data
        })

    async def on_detection(event: Event):
        """Forward detection events (optional, high frequency)."""
        # Only forward if clients have opted in
        await manager.broadcast({
            "type": "detection",
            "stream_id": event.stream_id,
            "detections": event.data.get("detections", []),
            "timestamp": event.timestamp.isoformat()
        })

    # Register handlers
    event_bus.on("summary.received", on_status_update)
    event_bus.on("alert.triggered", on_alert)
    # event_bus.on("detection.received", on_detection)  # Uncomment if needed


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live updates.

    Server sends:
    - status_update: {type, stream_id, severity, icon, description}
    - alert_new: {type, alert}
    - frame: {type, stream_id, data} (base64 JPEG)

    Client sends:
    - query: {type, stream_id, question}
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive client messages
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "query":
                    # Handle Q&A query
                    # TODO: Forward to Agent for processing
                    await manager.send_to(websocket, {
                        "type": "query_received",
                        "request_id": message.get("request_id"),
                        "status": "processing"
                    })

                elif msg_type == "ping":
                    await manager.send_to(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
