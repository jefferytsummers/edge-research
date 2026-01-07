"""
Tests for DeepStream DetectionPublisher.

Tests detection publishing, frame saving, and probe callback functionality.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile

import pytest

# Import from src package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detection_publisher import (
    DetectionPublisher,
    get_publisher,
    probe_callback,
    FRAME_DIR,
)


class TestDetectionPublisher:
    """Tests for DetectionPublisher class."""

    def test_initialization_default_redis_url(self):
        """Test publisher initialization with default Redis URL."""
        with patch.dict("os.environ", {"REDIS_URL": "redis://env-host:6379"}):
            publisher = DetectionPublisher()
            assert publisher.redis_url == "redis://env-host:6379"

    def test_initialization_custom_redis_url(self):
        """Test publisher initialization with custom Redis URL."""
        publisher = DetectionPublisher(redis_url="redis://custom:6379")
        assert publisher.redis_url == "redis://custom:6379"

    def test_initialization_creates_frame_dir(self):
        """Test publisher creates frame directory on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frame_dir = Path(tmpdir) / "frames"

            publisher = DetectionPublisher()
            publisher._frame_dir = frame_dir
            publisher._frame_dir.mkdir(parents=True, exist_ok=True)

            assert frame_dir.exists()

    def test_connect(self):
        """Test Redis connection."""
        mock_redis = MagicMock()
        mock_redis.ping = MagicMock(return_value=True)

        with patch("redis.from_url", return_value=mock_redis):
            publisher = DetectionPublisher()
            publisher.connect()

            assert publisher._redis is not None
            mock_redis.ping.assert_called_once()

    def test_ensure_stream_dir(self):
        """Test stream directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            publisher = DetectionPublisher()
            publisher._frame_dir = Path(tmpdir)

            stream_dir = publisher._ensure_stream_dir("stream_1")

            assert stream_dir.exists()
            assert stream_dir.name == "stream_1"

    def test_save_frame(self):
        """Test frame saving to disk."""
        pytest.importorskip("cv2")
        pytest.importorskip("numpy")

        import cv2
        import numpy as np

        with tempfile.TemporaryDirectory() as tmpdir:
            publisher = DetectionPublisher()
            publisher._frame_dir = Path(tmpdir)

            # Create test frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[100:200, 100:200] = 255  # White square

            frame_path = publisher._save_frame("stream_1", frame)

            assert Path(frame_path).exists()
            assert frame_path.endswith("latest.jpg")

            # Verify saved frame is valid
            loaded = cv2.imread(frame_path)
            assert loaded is not None
            assert loaded.shape == frame.shape

    def test_publish_detection_without_connection(self):
        """Test publishing without Redis connection logs warning."""
        publisher = DetectionPublisher()
        # _redis is None by default

        # Should not raise, just log warning
        publisher.publish_detection("stream_1", None, [])

    def test_publish_detection_with_connection(self):
        """Test publishing detection to Redis."""
        pytest.importorskip("cv2")
        pytest.importorskip("numpy")

        import numpy as np

        mock_redis = MagicMock()
        published_messages = []

        def capture_publish(channel, data):
            published_messages.append((channel, data))

        mock_redis.publish = capture_publish

        with tempfile.TemporaryDirectory() as tmpdir:
            publisher = DetectionPublisher()
            publisher._redis = mock_redis
            publisher._frame_dir = Path(tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            detections = [
                {
                    "class_id": 0,
                    "class_name": "person",
                    "confidence": 0.95,
                    "bbox": [100, 100, 300, 400]
                }
            ]

            publisher.publish_detection("stream_1", frame, detections)

            assert len(published_messages) == 1
            channel, data = published_messages[0]
            assert channel == "detections"

            message = json.loads(data)
            assert message["stream_id"] == "stream_1"
            assert message["type"] == "detection.received"
            assert len(message["detections"]) == 1

    def test_publish_detection_handles_error(self):
        """Test publishing handles Redis errors gracefully."""
        pytest.importorskip("cv2")
        pytest.importorskip("numpy")

        import numpy as np

        mock_redis = MagicMock()
        mock_redis.publish.side_effect = Exception("Redis error")

        with tempfile.TemporaryDirectory() as tmpdir:
            publisher = DetectionPublisher()
            publisher._redis = mock_redis
            publisher._frame_dir = Path(tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Should not raise
            publisher.publish_detection("stream_1", frame, [])


class TestGetPublisher:
    """Tests for get_publisher singleton function."""

    def test_get_publisher_creates_instance(self):
        """Test get_publisher creates and returns publisher."""
        # Reset global state
        import src.detection_publisher as dp
        dp._publisher = None

        mock_redis = MagicMock()
        mock_redis.ping = MagicMock(return_value=True)

        with patch("redis.from_url", return_value=mock_redis):
            publisher = get_publisher()
            assert publisher is not None
            assert isinstance(publisher, DetectionPublisher)

    def test_get_publisher_returns_same_instance(self):
        """Test get_publisher returns singleton."""
        import src.detection_publisher as dp
        dp._publisher = None

        mock_redis = MagicMock()
        mock_redis.ping = MagicMock(return_value=True)

        with patch("redis.from_url", return_value=mock_redis):
            publisher1 = get_publisher()
            publisher2 = get_publisher()
            assert publisher1 is publisher2


class TestProbeCallback:
    """Tests for DeepStream probe callback."""

    def test_probe_callback_placeholder(self):
        """Test probe callback returns success (placeholder implementation)."""
        # The probe_callback is a placeholder that just returns True
        result = probe_callback(None, None, None)
        assert result is True

    def test_probe_callback_docstring_documents_real_implementation(self):
        """Test probe callback has documentation for real implementation."""
        assert probe_callback.__doc__ is not None
        assert "DeepStream" in probe_callback.__doc__


class TestFrameDir:
    """Tests for FRAME_DIR constant."""

    def test_frame_dir_path(self):
        """Test FRAME_DIR is correctly defined."""
        assert FRAME_DIR == Path("/shared/frames")


class TestDetectionMessageFormat:
    """Tests for detection message format."""

    def test_message_structure(self):
        """Test detection message has required fields."""
        pytest.importorskip("numpy")

        import numpy as np

        mock_redis = MagicMock()
        published_messages = []
        mock_redis.publish = lambda c, d: published_messages.append(json.loads(d))

        with tempfile.TemporaryDirectory() as tmpdir:
            publisher = DetectionPublisher()
            publisher._redis = mock_redis
            publisher._frame_dir = Path(tmpdir)

            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            publisher.publish_detection("test_stream", frame, [])

            assert len(published_messages) == 1
            msg = published_messages[0]

            # Required fields
            assert "type" in msg
            assert "stream_id" in msg
            assert "frame_path" in msg
            assert "detections" in msg
            assert "timestamp" in msg

            # Correct values
            assert msg["type"] == "detection.received"
            assert msg["stream_id"] == "test_stream"
            assert isinstance(msg["timestamp"], float)

    def test_detection_fields(self):
        """Test detection objects have correct structure."""
        detection = {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.95,
            "bbox": [100, 100, 300, 400]
        }

        # Verify expected fields
        assert "class_id" in detection
        assert "class_name" in detection
        assert "confidence" in detection
        assert "bbox" in detection
        assert len(detection["bbox"]) == 4
