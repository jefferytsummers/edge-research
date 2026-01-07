"""
Tests for Pydantic data models.

Validates model creation, serialization, and validation.
"""
from datetime import datetime

import pytest

# Import from src package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import (
    Severity,
    Detection,
    DetectionEvent,
    StreamStatus,
    SummaryEvent,
    Alert,
    AlertLevel,
    ProtocolRules,
    StreamConfig,
    HealthStatus,
    ServiceInfo,
    WSStatusUpdate,
    WSAlert,
    WSQuery,
    WSQueryResponse,
)


class TestSeverityEnum:
    """Tests for Severity enum."""

    def test_severity_values(self):
        """Test all severity values are defined."""
        assert Severity.GREEN == "green"
        assert Severity.YELLOW == "yellow"
        assert Severity.RED == "red"

    def test_severity_from_string(self):
        """Test creating severity from string."""
        assert Severity("green") == Severity.GREEN
        assert Severity("yellow") == Severity.YELLOW
        assert Severity("red") == Severity.RED


class TestDetection:
    """Tests for Detection model."""

    def test_detection_creation(self):
        """Test creating a detection with valid data."""
        detection = Detection(
            class_id=0,
            class_name="person",
            confidence=0.95,
            bbox=[100, 100, 300, 400]
        )

        assert detection.class_id == 0
        assert detection.class_name == "person"
        assert detection.confidence == 0.95
        assert detection.bbox == [100, 100, 300, 400]

    def test_detection_confidence_validation(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            Detection(
                class_id=0,
                class_name="person",
                confidence=1.5,  # Invalid
                bbox=[0, 0, 100, 100]
            )

        with pytest.raises(ValueError):
            Detection(
                class_id=0,
                class_name="person",
                confidence=-0.1,  # Invalid
                bbox=[0, 0, 100, 100]
            )

    def test_detection_bbox_length_validation(self):
        """Test bbox must have exactly 4 elements."""
        with pytest.raises(ValueError):
            Detection(
                class_id=0,
                class_name="person",
                confidence=0.9,
                bbox=[0, 0, 100]  # Only 3 elements
            )

    def test_detection_bbox_negative_validation(self):
        """Test bbox coordinates must be non-negative."""
        with pytest.raises(ValueError):
            Detection(
                class_id=0,
                class_name="person",
                confidence=0.9,
                bbox=[-10, 0, 100, 100]  # Negative coordinate
            )


class TestDetectionEvent:
    """Tests for DetectionEvent model."""

    def test_detection_event_creation(self):
        """Test creating a detection event."""
        event = DetectionEvent(
            stream_id="stream_1",
            detections=[
                Detection(
                    class_id=0,
                    class_name="person",
                    confidence=0.9,
                    bbox=[0, 0, 100, 100]
                )
            ]
        )

        assert event.type == "detection.received"
        assert event.stream_id == "stream_1"
        assert len(event.detections) == 1

    def test_detection_event_empty_detections(self):
        """Test detection event with no detections."""
        event = DetectionEvent(stream_id="stream_1")

        assert event.detections == []


class TestStreamStatus:
    """Tests for StreamStatus model."""

    def test_stream_status_creation(self):
        """Test creating a stream status."""
        status = StreamStatus(
            stream_id="stream_1",
            severity=Severity.GREEN,
            icon="reading",
            description="Resident reading quietly"
        )

        assert status.stream_id == "stream_1"
        assert status.severity == Severity.GREEN
        assert status.confidence == 1.0  # Default

    def test_stream_status_custom_confidence(self):
        """Test stream status with custom confidence."""
        status = StreamStatus(
            stream_id="stream_1",
            severity=Severity.YELLOW,
            icon="unclear",
            description="Unable to determine activity",
            confidence=0.5
        )

        assert status.confidence == 0.5


class TestAlert:
    """Tests for Alert model."""

    def test_alert_creation(self):
        """Test creating an alert."""
        alert = Alert(
            stream_id="stream_1",
            level=AlertLevel.WARNING,
            title="Attention needed",
            message="Movement detected in restricted area",
            severity=Severity.YELLOW
        )

        assert alert.stream_id == "stream_1"
        assert alert.level == AlertLevel.WARNING
        assert alert.acknowledged is False  # Default

    def test_alert_levels(self):
        """Test all alert levels."""
        assert AlertLevel.INFO == "info"
        assert AlertLevel.WARNING == "warning"
        assert AlertLevel.CRITICAL == "critical"


class TestProtocolRules:
    """Tests for ProtocolRules model."""

    def test_protocol_rules_creation(self):
        """Test creating protocol rules."""
        rules = ProtocolRules(
            green_rules="Reading, watching TV, sleeping",
            yellow_rules="Pacing, distressed behavior",
            red_rules="Unconscious, severe injury"
        )

        assert "Reading" in rules.green_rules
        assert "Pacing" in rules.yellow_rules
        assert "Unconscious" in rules.red_rules

    def test_protocol_rules_empty_validation(self):
        """Test that rules cannot be empty."""
        with pytest.raises(ValueError):
            ProtocolRules(
                green_rules="",  # Empty not allowed
                yellow_rules="Some rules",
                red_rules="Other rules"
            )


class TestStreamConfig:
    """Tests for StreamConfig model."""

    def test_stream_config_creation(self):
        """Test creating a stream configuration."""
        config = StreamConfig(
            stream_id="stream_1",
            name="Living Room Camera",
            source_uri="rtsp://192.168.1.100:554/stream"
        )

        assert config.stream_id == "stream_1"
        assert config.name == "Living Room Camera"
        assert config.enabled is True  # Default

    def test_stream_config_with_protocols(self):
        """Test stream config with custom protocols."""
        rules = ProtocolRules(
            green_rules="Normal activities",
            yellow_rules="Attention behaviors",
            red_rules="Emergency situations"
        )

        config = StreamConfig(
            stream_id="stream_1",
            name="Bedroom Camera",
            source_uri="rtsp://192.168.1.101:554/stream",
            protocols=rules
        )

        assert config.protocols is not None
        assert "Normal" in config.protocols.green_rules


class TestHealthStatus:
    """Tests for HealthStatus model."""

    def test_health_status_healthy(self):
        """Test healthy status."""
        health = HealthStatus(
            status="healthy",
            service="newport-demo",
            redis_connected=True
        )

        assert health.status == "healthy"
        assert health.redis_connected is True

    def test_health_status_degraded(self):
        """Test degraded status."""
        health = HealthStatus(
            status="degraded",
            service="newport-demo",
            redis_connected=False,
            version="0.1.0",
            uptime_seconds=3600.5
        )

        assert health.status == "degraded"
        assert health.uptime_seconds == 3600.5


class TestServiceInfo:
    """Tests for ServiceInfo model."""

    def test_service_info(self):
        """Test service info creation."""
        info = ServiceInfo(
            name="Newport Demo",
            version="0.1.0"
        )

        assert info.name == "Newport Demo"
        assert info.docs == "/docs"  # Default


class TestWebSocketMessages:
    """Tests for WebSocket message models."""

    def test_ws_status_update(self):
        """Test WebSocket status update message."""
        msg = WSStatusUpdate(
            stream_id="stream_1",
            severity=Severity.GREEN,
            icon="reading",
            description="Reading quietly",
            timestamp="2024-01-01T12:00:00"
        )

        assert msg.type == "status_update"
        assert msg.stream_id == "stream_1"

    def test_ws_query(self):
        """Test WebSocket query message."""
        query = WSQuery(
            stream_id="stream_1",
            question="What is the person doing?",
            request_id="req_123"
        )

        assert query.type == "query"
        assert query.question == "What is the person doing?"

    def test_ws_query_response(self):
        """Test WebSocket query response message."""
        response = WSQueryResponse(
            request_id="req_123",
            answer="The person is reading a book.",
            timestamp="2024-01-01T12:00:00"
        )

        assert response.type == "query_response"
        assert response.answer == "The person is reading a book."


class TestModelSerialization:
    """Tests for model JSON serialization."""

    def test_detection_to_json(self):
        """Test Detection model JSON serialization."""
        detection = Detection(
            class_id=0,
            class_name="person",
            confidence=0.95,
            bbox=[100, 100, 300, 400]
        )

        json_data = detection.model_dump()

        assert json_data["class_id"] == 0
        assert json_data["class_name"] == "person"
        assert json_data["confidence"] == 0.95

    def test_stream_status_to_json(self):
        """Test StreamStatus model JSON serialization."""
        status = StreamStatus(
            stream_id="stream_1",
            severity=Severity.GREEN,
            icon="calm",
            description="All is well"
        )

        json_data = status.model_dump()

        assert json_data["severity"] == "green"
        assert "timestamp" in json_data

    def test_alert_to_json(self):
        """Test Alert model JSON serialization."""
        alert = Alert(
            id="alert_1",
            stream_id="stream_1",
            level=AlertLevel.CRITICAL,
            title="Emergency",
            message="Person on ground",
            severity=Severity.RED
        )

        json_data = alert.model_dump()

        assert json_data["level"] == "critical"
        assert json_data["severity"] == "red"
