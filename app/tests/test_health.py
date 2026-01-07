"""
Tests for health check endpoints and application startup.

Verifies the app can start, responds to health checks, and handles Redis connection states.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Import from src package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_endpoint_returns_status(self, test_client):
        """Test that /health endpoint returns proper structure."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "redis_connected" in data
        assert data["service"] == "newport-demo"

    def test_health_includes_version(self, test_client):
        """Test that health response includes version info."""
        response = test_client.get("/health")

        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_health_includes_uptime(self, test_client):
        """Test that health response includes uptime."""
        response = test_client.get("/health")

        data = response.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0

    def test_liveness_endpoint(self, test_client):
        """Test that /health/live endpoint returns alive status."""
        response = test_client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_root_endpoint(self, test_client):
        """Test that root endpoint returns service info."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Newport Demo"
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"

    def test_config_endpoint(self, test_client):
        """Test that /config endpoint returns configuration."""
        response = test_client.get("/config")

        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "app_version" in data
        assert "debug" in data
        assert "log_level" in data
        assert "redis_connected" in data


class TestHealthWithRedisDisconnected:
    """Tests for health checks with Redis disconnected."""

    @pytest.mark.asyncio
    async def test_health_shows_degraded_when_disconnected(self):
        """Test health status is degraded when Redis is not connected."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))
        mock_redis.close = AsyncMock()
        mock_redis.pubsub = MagicMock(return_value=AsyncMock())

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            from src.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/health")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "degraded"
                assert data["redis_connected"] is False

    @pytest.mark.asyncio
    async def test_readiness_returns_503_when_disconnected(self):
        """Test readiness returns 503 when Redis is not connected."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))
        mock_redis.close = AsyncMock()
        mock_redis.pubsub = MagicMock(return_value=AsyncMock())

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            from src.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/health/ready")

                assert response.status_code == 503
                data = response.json()
                assert "not ready" in data["detail"].lower()


class TestApplicationStartup:
    """Tests for application startup behavior."""

    @pytest.mark.asyncio
    async def test_app_starts_successfully_with_redis(self):
        """Test that the application starts successfully with Redis."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.close = AsyncMock()

        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        async def listen_generator():
            while True:
                await asyncio.sleep(100)
                yield {"type": "message", "data": "{}"}

        mock_pubsub.listen = MagicMock(return_value=listen_generator())
        mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            from src.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # App should be running and responding
                response = await client.get("/")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_app_starts_in_degraded_mode_without_redis(self):
        """Test that the application starts in degraded mode without Redis."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))
        mock_redis.close = AsyncMock()
        mock_redis.pubsub = MagicMock(return_value=AsyncMock())

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            from src.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # App should still be running
                response = await client.get("/")
                assert response.status_code == 200

                # But report degraded health
                health = await client.get("/health")
                assert health.json()["status"] == "degraded"


class TestOpenAPIDocs:
    """Tests for OpenAPI documentation availability."""

    def test_docs_endpoint_available(self, test_client):
        """Test that /docs endpoint is available."""
        response = test_client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_available(self, test_client):
        """Test that OpenAPI JSON schema is available."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Newport Demo"


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_for_unknown_endpoint(self, test_client):
        """Test 404 response for unknown endpoints."""
        response = test_client.get("/unknown/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, test_client):
        """Test 405 response for wrong HTTP method."""
        response = test_client.post("/health")
        assert response.status_code == 405
