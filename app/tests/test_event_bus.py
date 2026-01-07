"""
Tests for EventBus functionality.

Tests local event handling, Redis pub/sub integration, and thread-safe operations.
"""
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Import from src package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.event_bus import Event, EventBus


class TestEvent:
    """Tests for the Event dataclass."""

    def test_event_creation(self):
        """Test creating an Event with required fields."""
        event = Event(
            type="test.event",
            data={"key": "value"}
        )

        assert event.type == "test.event"
        assert event.data == {"key": "value"}
        assert event.stream_id is None
        assert isinstance(event.timestamp, datetime)

    def test_event_with_stream_id(self):
        """Test creating an Event with stream_id."""
        event = Event(
            type="detection.received",
            data={"detections": []},
            stream_id="stream_1"
        )

        assert event.stream_id == "stream_1"

    def test_event_to_dict(self):
        """Test converting Event to dictionary."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        event = Event(
            type="test.event",
            data={"key": "value"},
            timestamp=timestamp,
            stream_id="stream_1"
        )

        result = event.to_dict()

        assert result["type"] == "test.event"
        assert result["data"] == {"key": "value"}
        assert result["timestamp"] == "2024-01-01T12:00:00"
        assert result["stream_id"] == "stream_1"

    def test_event_from_dict(self):
        """Test creating Event from dictionary."""
        data = {
            "type": "test.event",
            "data": {"key": "value"},
            "timestamp": "2024-01-01T12:00:00",
            "stream_id": "stream_1"
        }

        event = Event.from_dict(data)

        assert event.type == "test.event"
        assert event.data == {"key": "value"}
        assert event.timestamp == datetime(2024, 1, 1, 12, 0, 0)
        assert event.stream_id == "stream_1"

    def test_event_from_dict_without_stream_id(self):
        """Test creating Event from dictionary without stream_id."""
        data = {
            "type": "test.event",
            "data": {},
            "timestamp": "2024-01-01T12:00:00"
        }

        event = Event.from_dict(data)

        assert event.stream_id is None


class TestEventBusLocal:
    """Tests for local (non-Redis) EventBus functionality."""

    def test_event_bus_initialization(self):
        """Test EventBus initialization."""
        bus = EventBus("redis://localhost:6379")

        assert bus.redis_url == "redis://localhost:6379"
        assert bus.is_connected is False
        assert len(bus._handlers) == 0

    def test_register_handler(self):
        """Test registering an event handler."""
        bus = EventBus()

        def handler(event):
            pass

        bus.on("test.event", handler)

        assert handler in bus._handlers["test.event"]

    def test_unregister_handler(self):
        """Test unregistering an event handler."""
        bus = EventBus()

        def handler(event):
            pass

        bus.on("test.event", handler)
        bus.off("test.event", handler)

        assert handler not in bus._handlers["test.event"]

    def test_unregister_nonexistent_handler(self):
        """Test unregistering a handler that was never registered."""
        bus = EventBus()

        def handler(event):
            pass

        # Should not raise an error
        bus.off("test.event", handler)

    @pytest.mark.asyncio
    async def test_emit_calls_handler(self):
        """Test that emit calls registered handlers."""
        bus = EventBus()
        received_events = []

        async def handler(event):
            received_events.append(event)

        bus.on("test.event", handler)

        event = Event(type="test.event", data={"key": "value"})
        await bus.emit(event)

        assert len(received_events) == 1
        assert received_events[0].type == "test.event"

    @pytest.mark.asyncio
    async def test_emit_calls_sync_handler(self):
        """Test that emit works with synchronous handlers."""
        bus = EventBus()
        received_events = []

        def handler(event):
            received_events.append(event)

        bus.on("test.event", handler)

        event = Event(type="test.event", data={"key": "value"})
        await bus.emit(event)

        assert len(received_events) == 1

    @pytest.mark.asyncio
    async def test_emit_wildcard_handler(self):
        """Test that wildcard handlers receive all events."""
        bus = EventBus()
        received_events = []

        async def handler(event):
            received_events.append(event)

        bus.on("*", handler)

        await bus.emit(Event(type="event.one", data={}))
        await bus.emit(Event(type="event.two", data={}))

        assert len(received_events) == 2

    @pytest.mark.asyncio
    async def test_emit_no_handlers(self):
        """Test that emit works when no handlers are registered."""
        bus = EventBus()
        event = Event(type="test.event", data={})

        # Should not raise an error
        await bus.emit(event)

    @pytest.mark.asyncio
    async def test_emit_handler_exception(self):
        """Test that emit continues after handler exception."""
        bus = EventBus()
        handler_calls = []

        async def bad_handler(event):
            raise ValueError("Handler error")

        async def good_handler(event):
            handler_calls.append(event)

        bus.on("test.event", bad_handler)
        bus.on("test.event", good_handler)

        event = Event(type="test.event", data={})
        await bus.emit(event)

        # Good handler should still be called
        assert len(handler_calls) == 1


class TestEventBusRedis:
    """Tests for Redis-integrated EventBus functionality."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_redis, mock_redis_url):
        """Test successful Redis connection."""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            bus = EventBus(mock_redis_url)
            await bus.connect()

            assert bus.is_connected is True
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_redis_url):
        """Test Redis connection failure."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            bus = EventBus(mock_redis_url)
            await bus.connect()

            assert bus.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_redis, mock_redis_url):
        """Test Redis disconnection."""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            bus = EventBus(mock_redis_url)
            await bus.connect()
            await bus.disconnect()

            assert bus.is_connected is False
            mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish(self, mock_redis, mock_redis_url):
        """Test publishing event to Redis."""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            bus = EventBus(mock_redis_url)
            await bus.connect()

            event = Event(type="test.event", data={"key": "value"})
            await bus.publish("test_channel", event)

            mock_redis.publish.assert_called_once()
            call_args = mock_redis.publish.call_args
            assert call_args[0][0] == "test_channel"
            assert "test.event" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_publish_not_connected(self, mock_redis_url):
        """Test publishing when not connected to Redis."""
        bus = EventBus(mock_redis_url)
        event = Event(type="test.event", data={})

        # Should not raise, just log warning
        await bus.publish("test_channel", event)

    @pytest.mark.asyncio
    async def test_subscribe_redis(self, mock_redis, mock_redis_url):
        """Test subscribing to Redis channels."""
        mock_pubsub = mock_redis.pubsub()

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            bus = EventBus(mock_redis_url)
            await bus.connect()

            # Start subscription task
            task = asyncio.create_task(
                bus.subscribe_redis(["channel1", "channel2"])
            )

            # Let it run briefly
            await asyncio.sleep(0.05)

            # Cancel task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            mock_pubsub.subscribe.assert_called_once_with("channel1", "channel2")

    @pytest.mark.asyncio
    async def test_subscribe_emits_events(self, mock_redis_url):
        """Test that Redis messages are emitted as local events."""
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Create mock with message generator
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.close = AsyncMock()

        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        test_event = {
            "type": "test.event",
            "data": {"key": "value"},
            "timestamp": "2024-01-01T12:00:00"
        }

        async def listen_generator():
            yield {"type": "subscribe", "channel": "test", "data": 1}
            yield {"type": "message", "channel": "test", "data": json.dumps(test_event)}
            await asyncio.sleep(10)  # Prevent immediate exit

        mock_pubsub.listen = MagicMock(return_value=listen_generator())
        mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            bus = EventBus(mock_redis_url)
            bus.on("test.event", handler)
            await bus.connect()

            task = asyncio.create_task(bus.subscribe_redis(["test"]))
            await asyncio.sleep(0.1)  # Let it process messages

            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            assert len(received_events) == 1
            assert received_events[0].type == "test.event"


class TestEventBusEmitSync:
    """Tests for thread-safe emit_sync functionality."""

    @pytest.mark.asyncio
    async def test_emit_sync_schedules_emit(self, mock_redis, mock_redis_url):
        """Test that emit_sync schedules emit on the event loop."""
        received_events = []

        async def handler(event):
            received_events.append(event)

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            bus = EventBus(mock_redis_url)
            await bus.connect()
            bus.on("test.event", handler)

            event = Event(type="test.event", data={})
            bus.emit_sync(event)

            # Give the event loop time to process
            await asyncio.sleep(0.1)

            assert len(received_events) == 1

    def test_emit_sync_without_loop(self):
        """Test emit_sync when no event loop is set."""
        bus = EventBus()
        event = Event(type="test.event", data={})

        # Should not raise, just do nothing
        bus.emit_sync(event)


class TestEventBusIntegration:
    """Integration tests for EventBus."""

    @pytest.mark.asyncio
    async def test_full_event_flow(self, mock_redis, mock_redis_url):
        """Test complete event flow: emit -> handler -> publish."""
        published_messages = []

        # Track published messages
        async def mock_publish(channel, data):
            published_messages.append((channel, data))

        mock_redis.publish = mock_publish

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            bus = EventBus(mock_redis_url)
            await bus.connect()

            # Set up handler that publishes to Redis
            async def forward_handler(event):
                await bus.publish("forwarded", event)

            bus.on("original.event", forward_handler)

            # Emit original event
            event = Event(
                type="original.event",
                data={"action": "test"},
                stream_id="stream_1"
            )
            await bus.emit(event)

            # Verify it was published
            assert len(published_messages) == 1
            channel, data = published_messages[0]
            assert channel == "forwarded"
            assert "original.event" in data
