"""
Newport Demo - DeepStream Package

DeepStream detection pipeline and Redis publishing.
"""
from .detection_publisher import (
    DetectionPublisher,
    get_publisher,
    probe_callback,
    FRAME_DIR,
)

__all__ = [
    "DetectionPublisher",
    "get_publisher",
    "probe_callback",
    "FRAME_DIR",
]
