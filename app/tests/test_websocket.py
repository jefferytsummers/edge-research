"""
Tests for WebSocket functionality.

Tests ConnectionManager, WebSocket endpoint, and event forwarding.
"""
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import WebSocket
from fastapi.testclient import TestClient

# Import from src package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.websocket import ConnectionManager, manager, setup_event_handlers
from src.event_bus import Event, EventBus


class TestConnectionManager:
    """Tests for the ConnectionManager class."""

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connecting a WebSocket client."""
        cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)

        await cm.connect(mock_ws)

        assert mock_ws in cm.active_connections
        mock_ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_multiple(self):
        """Test connecting multiple WebSocket clients."""
        cm = ConnectionManager()
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        await cm.connect(mock_ws1)
        await cm.connect(mock_ws2)

        assert len(cm.active_connections) == 2
        assert mock_ws1 in cm.active_connections
        assert mock_ws2 in cm.active_connections

    def test_disconnect(self):
        """Test disconnecting a WebSocket client."""
        cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        cm.active_connections.add(mock_ws)

        cm.disconnect(mock_ws)

        assert mock_ws not in cm.active_connections

    def test_disconnect_nonexistent(self):
        """Test disconnecting a client that's not connected."""
        cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)

        # Should not raise an error
        cm.disconnect(mock_ws)
        assert len(cm.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_no_connections(self):
        """Test broadcasting when no clients are connected."""
        cm = ConnectionManager()

        # Should not raise an error
        await cm.broadcast({"type": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self):
        """Test broadcasting message to all connected clients."""
        cm = ConnectionManager()
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        cm.active_connections.add(mock_ws1)
        cm.active_connections.add(mock_ws2)

        message = {"type": "test", "data": "hello"}
        await cm.broadcast(message)

        expected_data = json.dumps(message)
        mock_ws1.send_text.assert_called_once_with(expected_data)
        mock_ws2.send_text.assert_called_once_with(expected_data)

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected(self):
        """Test that broadcast removes clients that fail to receive."""
        cm = ConnectionManager()
        good_ws = AsyncMock(spec=WebSocket)
        bad_ws = AsyncMock(spec=WebSocket)
        bad_ws.send_text.side_effect = Exception("Connection closed")

        cm.active_connections.add(good_ws)
        cm.active_connections.add(bad_ws)

        await cm.broadcast({"type": "test"})

        # Good client should still be connected
        assert good_ws in cm.active_connections
        # Bad client should be removed
        assert bad_ws not in cm.active_connections

    @pytest.mark.asyncio
    async def test_send_to_specific_client(self):
        """Test sending message to a specific client."""
        cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)

        message = {"type": "response", "data": "specific"}
        await cm.send_to(mock_ws, message)

        mock_ws.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_to_handles_error(self):
        """Test that send_to handles send errors gracefully."""
        cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.send_text.side_effect = Exception("Send failed")

        # Should not raise
        await cm.send_to(mock_ws, {"type": "test"})


class TestSetupEventHandlers:
    """Tests for event handler setup."""

    @pytest.mark.asyncio
    async def test_setup_registers_handlers(self):
        """Test that setup_event_handlers registers expected handlers."""
        mock_bus = MagicMock(spec=EventBus)

        setup_event_handlers(mock_bus)

        # Should register handlers for summary and alert events
        assert mock_bus.on.call_count >= 2

        # Check that expected event types are registered
        registered_types = [call[0][0] for call in mock_bus.on.call_args_list]
        assert "summary.received" in registered_types
        assert "alert.triggered" in registered_types

    @pytest.mark.asyncio
    async def test_status_update_handler(self):
        """Test that status updates are broadcast to clients."""
        cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        cm.active_connections.add(mock_ws)

        # Create event
        event = Event(
            type="summary.received",
            data={
                "severity": "green",
                "icon": "reading",
                "description": "Reading quietly"
            },
            stream_id="stream_1",
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )

        # Get the handler by setting up with a real EventBus
        bus = EventBus()
        setup_event_handlers(bus)

        # Find the status update handler
        status_handler = None
        for handler in bus._handlers.get("summary.received", []):
            status_handler = handler
            break

        assert status_handler is not None

        # Replace the global manager temporarily
        original_manager = manager
        with patch("src.websocket.manager", cm):
            await status_handler(event)

        # Verify broadcast was called with correct structure
        assert mock_ws.send_text.called
        sent_data = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_data["type"] == "status_update"
        assert sent_data["stream_id"] == "stream_1"
        assert sent_data["severity"] == "green"

    @pytest.mark.asyncio
    async def test_alert_handler(self):
        """Test that alerts are broadcast to clients."""
        cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        cm.active_connections.add(mock_ws)

        event = Event(
            type="alert.triggered",
            data={
                "id": "alert_1",
                "title": "Attention needed",
                "message": "Movement detected",
                "level": "warning"
            }
        )

        bus = EventBus()
        setup_event_handlers(bus)

        alert_handler = None
        for handler in bus._handlers.get("alert.triggered", []):
            alert_handler = handler
            break

        assert alert_handler is not None

        with patch("src.websocket.manager", cm):
            await alert_handler(event)

        assert mock_ws.send_text.called
        sent_data = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_data["type"] == "alert_new"
        assert "alert" in sent_data


class TestWebSocketEndpoint:
    """Tests for the WebSocket endpoint."""

    def test_websocket_ping_pong(self, test_client):
        """Test WebSocket ping/pong message."""
        with test_client.websocket_connect("/ws/live") as websocket:
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"

    def test_websocket_query_received(self, test_client):
        """Test WebSocket query handling."""
        with test_client.websocket_connect("/ws/live") as websocket:
            websocket.send_json({
                "type": "query",
                "stream_id": "stream_1",
                "question": "What is happening?",
                "request_id": "req_123"
            })
            response = websocket.receive_json()
            assert response["type"] == "query_received"
            assert response["request_id"] == "req_123"
            assert response["status"] == "processing"

    def test_websocket_invalid_json(self, test_client):
        """Test WebSocket handling of invalid JSON."""
        with test_client.websocket_connect("/ws/live") as websocket:
            websocket.send_text("not valid json")
            # Connection should still be alive
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"

    def test_websocket_unknown_message_type(self, test_client):
        """Test WebSocket handling of unknown message types."""
        with test_client.websocket_connect("/ws/live") as websocket:
            websocket.send_json({"type": "unknown_type", "data": "test"})
            # Connection should still be alive
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"


class TestConnectionTracking:
    """Tests for connection tracking across multiple clients."""

    @pytest.mark.asyncio
    async def test_connection_count(self):
        """Test that connection count is accurate."""
        cm = ConnectionManager()

        assert len(cm.active_connections) == 0

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        await cm.connect(mock_ws1)
        assert len(cm.active_connections) == 1

        await cm.connect(mock_ws2)
        assert len(cm.active_connections) == 2

        cm.disconnect(mock_ws1)
        assert len(cm.active_connections) == 1

        cm.disconnect(mock_ws2)
        assert len(cm.active_connections) == 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test handling concurrent connections and messages."""
        cm = ConnectionManager()

        # Create multiple mock websockets
        mock_websockets = [AsyncMock(spec=WebSocket) for _ in range(5)]

        # Connect all concurrently
        await asyncio.gather(*[cm.connect(ws) for ws in mock_websockets])

        assert len(cm.active_connections) == 5

        # Broadcast message
        await cm.broadcast({"type": "test_broadcast"})

        # All should receive the message
        for ws in mock_websockets:
            ws.send_text.assert_called_once()


class TestGlobalManager:
    """Tests for the global ConnectionManager instance."""

    def test_global_manager_exists(self):
        """Test that global manager is initialized."""
        assert manager is not None
        assert isinstance(manager, ConnectionManager)

    @pytest.mark.asyncio
    async def test_global_manager_independence(self):
        """Test that creating new managers doesn't affect global."""
        original_count = len(manager.active_connections)

        # Create a new manager
        new_cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        await new_cm.connect(mock_ws)

        # Global manager should be unaffected
        assert len(manager.active_connections) == original_count
        assert len(new_cm.active_connections) == 1
