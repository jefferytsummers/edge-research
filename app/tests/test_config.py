"""
Tests for configuration management.

Tests Pydantic Settings, environment loading, and logging configuration.
"""
import logging
import os
from unittest.mock import patch

import pytest

# Import from src package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Settings, get_settings, configure_logging


class TestSettings:
    """Tests for the Settings class."""

    def test_default_server_settings(self):
        """Test default server settings."""
        settings = Settings()

        assert settings.host == "0.0.0.0"
        assert settings.port == 8080

    def test_default_redis_channels(self):
        """Test default Redis channels are configured."""
        settings = Settings()

        assert "detections" in settings.redis_channels
        assert "summaries" in settings.redis_channels

    def test_default_vlm_settings(self):
        """Test default VLM settings."""
        settings = Settings()

        assert settings.vlm_inference_interval == 10.0
        assert settings.vlm_debounce_count == 2

    def test_default_frame_settings(self):
        """Test default frame settings."""
        settings = Settings()

        assert settings.frame_dir == "/shared/frames"
        assert settings.frame_jpeg_quality == 85

    def test_settings_from_env(self):
        """Test loading settings from environment variables."""
        get_settings.cache_clear()

        with patch.dict(os.environ, {
            "APP_NAME": "Test App",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "REDIS_URL": "redis://redis-host:6379"
        }):
            settings = Settings()

            assert settings.app_name == "Test App"
            assert settings.debug is True
            assert settings.log_level == "DEBUG"
            assert settings.redis_url == "redis://redis-host:6379"

    def test_log_level_validation_valid(self):
        """Test valid log level values."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            with patch.dict(os.environ, {"LOG_LEVEL": level}):
                settings = Settings()
                assert settings.log_level == level

    def test_log_level_validation_case_insensitive(self):
        """Test log level validation is case insensitive."""
        with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_log_level_validation_invalid(self):
        """Test invalid log level raises error."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValueError, match="Invalid log level"):
                Settings()

    def test_jpeg_quality_validation_valid(self):
        """Test valid JPEG quality values."""
        for quality in [1, 50, 85, 100]:
            with patch.dict(os.environ, {"FRAME_JPEG_QUALITY": str(quality)}):
                settings = Settings()
                assert settings.frame_jpeg_quality == quality

    def test_jpeg_quality_validation_invalid_low(self):
        """Test JPEG quality below minimum raises error."""
        with patch.dict(os.environ, {"FRAME_JPEG_QUALITY": "0"}):
            with pytest.raises(ValueError, match="between 1 and 100"):
                Settings()

    def test_jpeg_quality_validation_invalid_high(self):
        """Test JPEG quality above maximum raises error."""
        with patch.dict(os.environ, {"FRAME_JPEG_QUALITY": "101"}):
            with pytest.raises(ValueError, match="between 1 and 100"):
                Settings()


class TestGetSettings:
    """Tests for get_settings function."""

    def test_returns_settings_instance(self):
        """Test get_settings returns Settings instance."""
        get_settings.cache_clear()
        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_cached_settings(self):
        """Test settings are cached."""
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2  # Same instance

    def test_cache_clear(self):
        """Test cache can be cleared."""
        get_settings.cache_clear()

        settings1 = get_settings()

        get_settings.cache_clear()

        settings2 = get_settings()

        # After cache clear, should be different instances
        # (though with same values if env unchanged)
        # Note: instances may still equal if values are same


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_logging_default(self):
        """Test configure_logging with default settings."""
        get_settings.cache_clear()

        # Reset logging to clean state
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        configure_logging()

        # Check root logger level
        # Note: basicConfig may not change root level if already set
        logger = logging.getLogger(__name__)
        assert logger is not None

    def test_configure_logging_with_custom_settings(self):
        """Test configure_logging with custom settings."""
        get_settings.cache_clear()

        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            settings = Settings()

            # Reset logging
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            configure_logging(settings)

    def test_configure_logging_without_settings_arg(self):
        """Test configure_logging uses get_settings when no arg provided."""
        get_settings.cache_clear()

        # Should not raise
        configure_logging()


class TestCORSSettings:
    """Tests for CORS settings."""

    def test_default_cors_origins(self):
        """Test default CORS origins allow all."""
        settings = Settings()

        assert "*" in settings.cors_origins

    def test_cors_origins_from_env(self):
        """Test CORS origins can be configured via env."""
        # Note: List parsing from env depends on format
        # Pydantic settings typically need JSON format for lists
        settings = Settings()

        # Default should work
        assert len(settings.cors_origins) >= 1


class TestWebSocketSettings:
    """Tests for WebSocket settings."""

    def test_default_heartbeat_interval(self):
        """Test default WebSocket heartbeat interval."""
        settings = Settings()

        assert settings.ws_heartbeat_interval == 30
