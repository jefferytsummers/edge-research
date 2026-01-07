"""
Pytest configuration and shared fixtures for VLM tests.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure the src package is importable
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Create a mock async Redis client."""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.publish = AsyncMock(return_value=1)
    mock.close = AsyncMock()

    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()

    async def listen_generator():
        yield {"type": "subscribe", "channel": "test", "data": 1}
        await asyncio.sleep(0.1)

    mock_pubsub.listen = MagicMock(return_value=listen_generator())
    mock.pubsub = MagicMock(return_value=mock_pubsub)

    return mock


@pytest.fixture
def sample_protocols():
    """Sample protocol configuration."""
    from src.protocol_evaluator import ProtocolConfig

    return ProtocolConfig(
        green_rules="Reading, watching TV, sleeping normally in bed, eating meals, sitting calmly",
        yellow_rules="Out of camera view, crouching in corners, minor injuries, pacing erratically",
        red_rules="Unconscious on ground, severe injury, room is empty, self-harm behavior"
    )


@pytest.fixture
def sample_detections():
    """Sample detection data."""
    return [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.95,
            "bbox": [100, 100, 300, 400]
        }
    ]
