"""
DeepStream Detection Publisher - Publishes detections to Redis.

Probe callback for DeepStream pipeline that extracts detections
and publishes them to Redis for VLM processing.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Frame output directory (shared with VLM container)
FRAME_DIR = Path("/shared/frames")


class DetectionPublisher:
    """
    Publishes detections from DeepStream to Redis.

    Used as a probe callback in DeepStream pipeline.
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379")
        self._redis = None
        self._frame_dir = FRAME_DIR

        # Ensure frame directory exists
        self._frame_dir.mkdir(parents=True, exist_ok=True)

    def connect(self):
        """Connect to Redis (synchronous for DeepStream probe context)."""
        import redis
        self._redis = redis.from_url(self.redis_url)
        self._redis.ping()
        logger.info(f"Connected to Redis at {self.redis_url}")

    def _ensure_stream_dir(self, stream_id: str) -> Path:
        """Ensure stream directory exists."""
        stream_dir = self._frame_dir / stream_id
        stream_dir.mkdir(parents=True, exist_ok=True)
        return stream_dir

    def _save_frame(self, stream_id: str, frame: np.ndarray) -> str:
        """Save frame to shared volume."""
        stream_dir = self._ensure_stream_dir(stream_id)
        frame_path = stream_dir / "latest.jpg"

        # Encode and save
        cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        return str(frame_path)

    def publish_detection(
        self,
        stream_id: str,
        frame: np.ndarray,
        detections: List[Dict]
    ):
        """
        Publish detection event to Redis.

        Args:
            stream_id: Camera/stream identifier
            frame: Video frame (numpy array, BGR)
            detections: List of detection dicts with:
                - class_id: int
                - class_name: str
                - confidence: float
                - bbox: [x1, y1, x2, y2]
        """
        if not self._redis:
            logger.warning("Redis not connected")
            return

        # Save frame to shared volume
        frame_path = self._save_frame(stream_id, frame)

        # Build message
        message = {
            "type": "detection.received",
            "stream_id": stream_id,
            "frame_path": frame_path,
            "detections": detections,
            "timestamp": time.time()
        }

        # Publish to Redis
        try:
            self._redis.publish("detections", json.dumps(message))
            logger.debug(f"Published {len(detections)} detections for {stream_id}")
        except Exception as e:
            logger.error(f"Failed to publish: {e}")


# Global publisher instance (for DeepStream probe callback)
_publisher: Optional[DetectionPublisher] = None


def get_publisher() -> DetectionPublisher:
    """Get or create global publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = DetectionPublisher()
        _publisher.connect()
    return _publisher


def probe_callback(pad, info, user_data):
    """
    DeepStream probe callback for extracting detections.

    This function is called by DeepStream for each batch of frames.
    It extracts detection metadata and publishes to Redis.

    Usage in DeepStream pipeline:
        nvinfer_src_pad.add_probe(Gst.PadProbeType.BUFFER, probe_callback, 0)
    """
    # Import DeepStream bindings
    # import pyds  # NVIDIA DeepStream Python bindings

    # Placeholder implementation
    # In real implementation:
    # 1. Get batch meta from info
    # 2. Iterate over frame meta
    # 3. Extract object meta (detections)
    # 4. Get frame data
    # 5. Publish via DetectionPublisher

    """
    # Real implementation would look like:
    import pyds

    gst_buffer = info.get_buffer()
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    l_frame = batch_meta.frame_meta_list
    while l_frame:
        frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        stream_id = f"stream_{frame_meta.source_id}"

        detections = []
        l_obj = frame_meta.obj_meta_list
        while l_obj:
            obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            detections.append({
                "class_id": obj_meta.class_id,
                "class_name": obj_meta.obj_label,
                "confidence": obj_meta.confidence,
                "bbox": [
                    obj_meta.rect_params.left,
                    obj_meta.rect_params.top,
                    obj_meta.rect_params.left + obj_meta.rect_params.width,
                    obj_meta.rect_params.top + obj_meta.rect_params.height
                ]
            })
            l_obj = l_obj.next

        # Get frame (requires nvbufsurface mapping)
        # frame = get_frame_from_buffer(gst_buffer, frame_meta)

        # Publish
        publisher = get_publisher()
        publisher.publish_detection(stream_id, frame, detections)

        l_frame = l_frame.next

    return Gst.PadProbeReturn.OK
    """

    logger.debug("Probe callback invoked (placeholder)")
    return True  # Gst.PadProbeReturn.OK


def main():
    """Test the publisher."""
    logging.basicConfig(level=logging.INFO)

    publisher = DetectionPublisher()
    publisher.connect()

    # Create test frame
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(
        test_frame, "Test Frame", (200, 240),
        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
    )

    # Test detection
    detections = [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.95,
            "bbox": [100, 100, 300, 400]
        }
    ]

    publisher.publish_detection("test_stream", test_frame, detections)
    logger.info("Test detection published")


if __name__ == "__main__":
    main()
