"""
Pytest configuration and shared fixtures for Newport Demo tests.
"""
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Ensure the src package is importable
import sys
from pathlib import Path

# Add the app directory to path for imports
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.publish = AsyncMock(return_value=1)
    mock.close = AsyncMock()

    # Mock pubsub
    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()

    async def listen_generator():
        # Yield one test message then stop
        yield {"type": "subscribe", "channel": "test", "data": 1}
        # Simulate waiting for more messages
        await asyncio.sleep(0.1)

    mock_pubsub.listen = MagicMock(return_value=listen_generator())
    mock.pubsub = MagicMock(return_value=mock_pubsub)

    return mock


@pytest.fixture
def mock_redis_url():
    """Return mock Redis URL."""
    return "redis://mock:6379"


@pytest_asyncio.fixture
async def event_bus(mock_redis, mock_redis_url):
    """Create an EventBus with mocked Redis."""
    from src.event_bus import EventBus

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        bus = EventBus(mock_redis_url)
        await bus.connect()
        yield bus
        await bus.disconnect()


@pytest.fixture
def test_client():
    """Create a test client with mocked Redis."""
    from src.main import app

    # Mock Redis connection for app startup
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.close = AsyncMock()

    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()

    async def listen_generator():
        while True:
            await asyncio.sleep(100)
            yield {"type": "message", "data": "{}"}

    mock_pubsub.listen = MagicMock(return_value=listen_generator())
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        with TestClient(app) as client:
            yield client


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client with mocked Redis."""
    from src.main import app

    # Mock Redis connection for app startup
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.close = AsyncMock()

    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()

    async def listen_generator():
        while True:
            await asyncio.sleep(100)
            yield {"type": "message", "data": "{}"}

    mock_pubsub.listen = MagicMock(return_value=listen_generator())
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client


@pytest.fixture
def sample_detection_event():
    """Sample detection event data."""
    return {
        "type": "detection.received",
        "stream_id": "stream_1",
        "frame_path": "/shared/frames/stream_1/latest.jpg",
        "detections": [
            {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.95,
                "bbox": [100, 100, 300, 400]
            }
        ],
        "timestamp": 1704067200.0
    }


@pytest.fixture
def sample_summary_event():
    """Sample VLM summary event data."""
    return {
        "type": "summary.received",
        "stream_id": "stream_1",
        "data": {
            "severity": "green",
            "icon": "reading",
            "description": "Resident reading in chair",
            "confidence": 0.9
        },
        "timestamp": 1704067200.0
    }
