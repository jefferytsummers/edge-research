"""
Pytest configuration and shared fixtures for DeepStream tests.
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure the src package is importable
import sys

src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture
def mock_redis():
    """Create a mock synchronous Redis client."""
    mock = MagicMock()
    mock.ping = MagicMock(return_value=True)
    mock.publish = MagicMock(return_value=1)
    mock.close = MagicMock()
    return mock


@pytest.fixture
def temp_frame_dir():
    """Create a temporary directory for frames."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_frame():
    """Create a sample test frame."""
    try:
        import numpy as np
        return np.zeros((480, 640, 3), dtype=np.uint8)
    except ImportError:
        pytest.skip("numpy not available")


@pytest.fixture
def sample_detections():
    """Sample detection data."""
    return [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.95,
            "bbox": [100, 100, 300, 400]
        },
        {
            "class_id": 1,
            "class_name": "chair",
            "confidence": 0.87,
            "bbox": [200, 200, 350, 450]
        }
    ]
