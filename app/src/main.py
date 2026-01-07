"""
Newport Demo - FastAPI Application Entry Point

Multi-stream behavioral monitoring application.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings, get_settings, configure_logging
from .event_bus import EventBus
from .models import HealthStatus, ServiceInfo
from .websocket import router as ws_router, setup_event_handlers

# Configure logging on module load
configure_logging()
logger = logging.getLogger(__name__)

# Global instances
event_bus: Optional[EventBus] = None
redis_subscriber_task: Optional[asyncio.Task] = None
startup_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global event_bus, redis_subscriber_task, startup_time

    settings = get_settings()
    startup_time = time.time()

    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    # Startup
    try:
        event_bus = EventBus(settings.redis_url)
        await event_bus.connect()

        if event_bus.is_connected:
            logger.info("Successfully connected to Redis")

            # Set up WebSocket event handlers
            setup_event_handlers(event_bus)
            logger.info("WebSocket event handlers configured")

            # Start Redis subscriber
            redis_subscriber_task = asyncio.create_task(
                event_bus.subscribe_redis(settings.redis_channels)
            )
            logger.info(f"Redis subscriber started for channels: {settings.redis_channels}")
        else:
            logger.warning("Redis connection failed, running in degraded mode")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Continue without Redis - degraded mode
        event_bus = EventBus(settings.redis_url)

    logger.info(f"Application startup complete in {time.time() - startup_time:.2f}s")

    yield

    # Shutdown
    logger.info("Initiating graceful shutdown")

    if redis_subscriber_task:
        redis_subscriber_task.cancel()
        try:
            await redis_subscriber_task
        except asyncio.CancelledError:
            logger.debug("Redis subscriber task cancelled")

    if event_bus:
        await event_bus.disconnect()

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Multi-stream behavioral monitoring for edge AI",
        version=settings.app_version,
        lifespan=lifespan,
        debug=settings.debug,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(ws_router)

    return app


# Create application instance
app = create_app()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    Health check endpoint.

    Returns service health status including Redis connection state.
    """
    settings = get_settings()
    redis_connected = event_bus.is_connected if event_bus else False

    status = "healthy" if redis_connected else "degraded"

    return HealthStatus(
        status=status,
        service="newport-demo",
        redis_connected=redis_connected,
        version=settings.app_version,
        uptime_seconds=time.time() - startup_time if startup_time > 0 else 0,
    )


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Returns 200 only when the service is fully ready to accept traffic.
    """
    if not event_bus or not event_bus.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Service not ready: Redis not connected"
        )
    return {"status": "ready"}


@app.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint.

    Returns 200 as long as the service is running (not deadlocked).
    """
    return {"status": "alive"}


@app.get("/api/info", response_model=ServiceInfo)
async def api_info() -> ServiceInfo:
    """API info endpoint with service information."""
    settings = get_settings()
    return ServiceInfo(
        name=settings.app_name,
        version=settings.app_version,
        docs="/docs"
    )


@app.get("/config")
async def get_current_config():
    """
    Get current configuration (non-sensitive values).

    For debugging and operational visibility.
    Includes model_ready flag for frontend to show loading state.
    """
    import json
    settings = get_settings()

    # Check pipeline status from Redis
    model_ready = False
    pipeline_status = "offline"
    pipeline_message = "Pipeline not running"
    pipeline_progress = 0

    # Status is considered stale if older than 15 seconds (updates come every 5s)
    STALE_THRESHOLD_SECONDS = 15

    if event_bus and event_bus.is_connected:
        try:
            status_json = await event_bus._redis.get("pipeline:stream_0:status")
            if status_json:
                status_data = json.loads(status_json)
                status_timestamp = status_data.get("timestamp", 0)

                # Check if status is stale
                age_seconds = time.time() - status_timestamp
                if age_seconds > STALE_THRESHOLD_SECONDS:
                    # Status is stale - pipeline likely stopped
                    pipeline_status = "offline"
                    pipeline_message = "Pipeline not responding (last seen {:.0f}s ago)".format(age_seconds)
                else:
                    # Status is fresh
                    pipeline_status = status_data.get("status", "unknown")
                    pipeline_message = status_data.get("message", "")
                    pipeline_progress = status_data.get("progress", 0) or 0
                    model_ready = pipeline_status == "running"
        except Exception:
            pass

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "debug": settings.debug,
        "log_level": settings.log_level,
        "redis_connected": event_bus.is_connected if event_bus else False,
        "vlm_inference_interval": settings.vlm_inference_interval,
        "vlm_debounce_count": settings.vlm_debounce_count,
        "model_ready": model_ready,
        "pipeline_status": pipeline_status,
        "pipeline_message": pipeline_message,
        "pipeline_progress": pipeline_progress,
    }


@app.get("/api/pipeline/status")
async def get_pipeline_status(stream_id: str = "stream_0"):
    """
    Get current pipeline status for a stream.

    Returns the AI model build status and pipeline state.
    Used by frontend to show loading indicators.
    """
    if not event_bus or not event_bus.is_connected:
        return {
            "status": "unknown",
            "message": "Redis not connected",
            "stream_id": stream_id,
            "timestamp": time.time()
        }

    try:
        # Get status from Redis key (set by DeepStream)
        status_json = await event_bus._redis.get(f"pipeline:{stream_id}:status")
        if status_json:
            import json
            return json.loads(status_json)
        else:
            return {
                "status": "offline",
                "message": "Pipeline not started",
                "stream_id": stream_id,
                "timestamp": time.time()
            }
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "stream_id": stream_id,
            "timestamp": time.time()
        }


# Static file serving for frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for all non-API routes."""
        # Check if it's a static file
        file_path = FRONTEND_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA routing
        return FileResponse(FRONTEND_DIR / "index.html")
