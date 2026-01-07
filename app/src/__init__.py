"""
Newport Demo - App Package

Multi-stream behavioral monitoring FastAPI application.
"""
from .event_bus import EventBus, Event
from .websocket import ConnectionManager, manager, setup_event_handlers
from .config import Settings, get_settings, configure_logging
from .models import (
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
)

__all__ = [
    # Event bus
    "EventBus",
    "Event",
    # WebSocket
    "ConnectionManager",
    "manager",
    "setup_event_handlers",
    # Config
    "Settings",
    "get_settings",
    "configure_logging",
    # Models
    "Severity",
    "Detection",
    "DetectionEvent",
    "StreamStatus",
    "SummaryEvent",
    "Alert",
    "AlertLevel",
    "ProtocolRules",
    "StreamConfig",
    "HealthStatus",
    "ServiceInfo",
]
