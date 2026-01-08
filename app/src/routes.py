"""
API routes for Newport Demo application.

Provides REST endpoints for feeds, protocols, alerts, and status.
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .models import (
    Alert,
    AlertLevel,
    ProtocolRules,
    Severity,
    StreamConfig,
    StreamStatus,
)
from .storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


# Request/Response models

class AddFeedRequest(BaseModel):
    """Request body for adding a feed."""
    name: str
    source_uri: str


class TestConnectionRequest(BaseModel):
    """Request body for testing a connection."""
    source_url: str


class ConnectionTestResult(BaseModel):
    """Result of connection test."""
    success: bool
    resolution: Optional[str] = None
    fps: Optional[float] = None
    error: Optional[str] = None


class AppConfigResponse(BaseModel):
    """Full application configuration."""
    feeds: List[StreamConfig]
    protocols: ProtocolRules
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StatusResponse(BaseModel):
    """Current status response."""
    streams: List[StreamStatus]
    active_alerts: int


class AlertsResponse(BaseModel):
    """Alerts list response."""
    alerts: List[Alert]


# Configuration endpoints

@router.get("/config", response_model=AppConfigResponse)
async def get_config():
    """Get full application configuration."""
    storage = get_storage()
    feeds = storage.get_feeds()
    protocols = storage.get_protocols()

    return AppConfigResponse(
        feeds=feeds,
        protocols=protocols,
        updated_at=datetime.utcnow().isoformat(),
    )


# Feed endpoints

@router.get("/config/feeds", response_model=List[StreamConfig])
async def list_feeds():
    """List all configured feeds."""
    storage = get_storage()
    return storage.get_feeds()


@router.post("/config/feeds", response_model=StreamConfig)
async def add_feed(request: AddFeedRequest):
    """Add a new feed."""
    storage = get_storage()
    feed = storage.add_feed(name=request.name, source_uri=request.source_uri)
    logger.info(f"Added feed: {feed.stream_id} - {feed.name}")
    return feed


@router.get("/config/feeds/{stream_id}", response_model=StreamConfig)
async def get_feed(stream_id: str):
    """Get a specific feed."""
    storage = get_storage()
    feed = storage.get_feed(stream_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return feed


@router.delete("/config/feeds/{stream_id}")
async def delete_feed(stream_id: str):
    """Delete a feed."""
    storage = get_storage()
    if not storage.delete_feed(stream_id):
        raise HTTPException(status_code=404, detail="Feed not found")
    logger.info(f"Deleted feed: {stream_id}")
    return {"status": "deleted", "stream_id": stream_id}


@router.post("/config/feeds/test", response_model=ConnectionTestResult)
async def test_feed_connection(request: TestConnectionRequest):
    """
    Test an RTSP connection.

    Note: Full connection testing requires the DeepStream container.
    This endpoint validates the URL format and performs basic checks.
    """
    source_url = request.source_url

    # Basic URL validation
    if not source_url:
        return ConnectionTestResult(
            success=False,
            error="URL is required"
        )

    # Check for supported protocols
    supported_protocols = ("rtsp://", "rtsps://", "file://", "http://", "https://")
    if not any(source_url.startswith(p) for p in supported_protocols):
        return ConnectionTestResult(
            success=False,
            error=f"Unsupported protocol. Use one of: {', '.join(supported_protocols)}"
        )

    # For now, return success for valid-looking URLs
    # Full testing would probe the stream via DeepStream
    # TODO: Implement actual RTSP probe via DeepStream container
    if source_url.startswith("rtsp://") or source_url.startswith("rtsps://"):
        return ConnectionTestResult(
            success=True,
            resolution="1920x1080",
            fps=30.0,
        )
    elif source_url.startswith("file://"):
        return ConnectionTestResult(
            success=True,
            resolution="1280x720",
            fps=30.0,
        )
    else:
        return ConnectionTestResult(
            success=True,
            resolution="unknown",
        )


# Protocol endpoints

@router.get("/config/protocols", response_model=ProtocolRules)
async def get_protocols():
    """Get current protocol rules."""
    storage = get_storage()
    return storage.get_protocols()


@router.post("/config/protocols", response_model=ProtocolRules)
async def save_protocols(protocols: ProtocolRules):
    """Save protocol rules."""
    storage = get_storage()
    saved = storage.save_protocols(protocols)
    logger.info("Protocol rules updated")
    return saved


@router.put("/config/protocols", response_model=ProtocolRules)
async def update_protocols(protocols: ProtocolRules):
    """Update protocol rules (alias for POST)."""
    return await save_protocols(protocols)


# Alert endpoints

@router.get("/alerts", response_model=AlertsResponse)
async def list_alerts(include_resolved: bool = False, limit: int = 100):
    """List alerts."""
    storage = get_storage()
    alerts = storage.get_alerts(include_resolved=include_resolved, limit=limit)
    return AlertsResponse(alerts=alerts)


@router.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str):
    """Get a specific alert."""
    storage = get_storage()
    alert = storage.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    storage = get_storage()
    alert = storage.acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    logger.info(f"Alert acknowledged: {alert_id}")
    return alert


@router.post("/alerts/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    storage = get_storage()
    alert = storage.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    logger.info(f"Alert resolved: {alert_id}")
    return alert


# Status endpoint

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get current status of all streams.

    Returns stream statuses and active alert count.
    Note: Stream statuses are populated from WebSocket updates.
    """
    storage = get_storage()
    active_alerts = storage.get_unacknowledged_count()

    # TODO: Get actual stream statuses from in-memory state
    # For now, return feeds with default status
    feeds = storage.get_feeds()
    streams = []
    for feed in feeds:
        streams.append(StreamStatus(
            stream_id=feed.stream_id,
            severity=Severity.GREEN,
            icon="\U0001F50D",
            description="Initializing...",
            confidence=0.0,
            timestamp=datetime.utcnow(),
        ))

    return StatusResponse(
        streams=streams,
        active_alerts=active_alerts,
    )
