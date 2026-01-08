"""
WebSocket handler for real-time frontend updates.

Forwards Redis events to connected WebSocket clients.
Handles Q&A query forwarding to VLM container.
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .event_bus import Event, EventBus

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level event bus reference (set by setup_event_handlers)
_event_bus: Optional[EventBus] = None


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        # Track pending queries: request_id -> websocket
        self.pending_queries: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        # Clean up any pending queries for this connection
        to_remove = [rid for rid, ws in self.pending_queries.items() if ws == websocket]
        for rid in to_remove:
            del self.pending_queries[rid]
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

    def register_query(self, request_id: str, websocket: WebSocket):
        """Register a pending query to route the response back."""
        self.pending_queries[request_id] = websocket

    async def send_query_response(self, request_id: str, response: Dict):
        """Send query response to the original requester."""
        websocket = self.pending_queries.pop(request_id, None)
        if websocket:
            await self.send_to(websocket, response)
        else:
            logger.warning(f"No pending query found for request_id: {request_id}")


manager = ConnectionManager()


def setup_event_handlers(event_bus: EventBus):
    """Set up event bus handlers to forward to WebSocket clients."""
    global _event_bus
    _event_bus = event_bus

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

    async def on_query_response(event: Event):
        """Forward Q&A responses to the requesting client."""
        request_id = event.data.get("request_id")
        if request_id:
            await manager.send_query_response(request_id, {
                "type": "query_response",
                "request_id": request_id,
                "stream_id": event.stream_id,
                "answer": event.data.get("answer", ""),
                "timestamp": event.timestamp.isoformat()
            })

    # Register handlers
    event_bus.on("summary.received", on_status_update)
    event_bus.on("alert.triggered", on_alert)
    event_bus.on("query.response", on_query_response)
    # event_bus.on("detection.received", on_detection)  # Uncomment if needed


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live updates.

    Server sends:
    - status_update: {type, stream_id, severity, icon, description}
    - alert_new: {type, alert}
    - query_received: {type, request_id, status}
    - query_response: {type, request_id, stream_id, answer}

    Client sends:
    - query: {type, stream_id, question, request_id}
    - ping: {type: "ping"}
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
                    # Handle Q&A query - forward to VLM via Redis
                    stream_id = message.get("stream_id")
                    question = message.get("question")
                    request_id = message.get("request_id") or str(uuid.uuid4())

                    # Register this query so we can route the response back
                    manager.register_query(request_id, websocket)

                    # Acknowledge receipt
                    await manager.send_to(websocket, {
                        "type": "query_received",
                        "request_id": request_id,
                        "status": "processing"
                    })

                    # Forward to VLM container via Redis "queries" channel
                    if _event_bus and _event_bus.is_connected:
                        query_event = Event(
                            type="query",
                            stream_id=stream_id,
                            data={
                                "question": question,
                                "request_id": request_id,
                                "stream_id": stream_id
                            }
                        )
                        await _event_bus.publish("queries", query_event)
                        logger.info(f"Forwarded query {request_id} to VLM: {question[:50]}...")
                    else:
                        # No Redis connection - send error response
                        await manager.send_to(websocket, {
                            "type": "query_response",
                            "request_id": request_id,
                            "stream_id": stream_id,
                            "answer": "Q&A service is not available. Please try again later.",
                            "error": True
                        })
                        manager.pending_queries.pop(request_id, None)

                elif msg_type == "ping":
                    await manager.send_to(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
