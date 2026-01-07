"""
Newport Demo - FastAPI Application Entry Point

Multi-stream behavioral monitoring application.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


@app.get("/", response_model=ServiceInfo)
async def root() -> ServiceInfo:
    """Root endpoint with service information."""
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
    """
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "debug": settings.debug,
        "log_level": settings.log_level,
        "redis_connected": event_bus.is_connected if event_bus else False,
        "vlm_inference_interval": settings.vlm_inference_interval,
        "vlm_debounce_count": settings.vlm_debounce_count,
    }
