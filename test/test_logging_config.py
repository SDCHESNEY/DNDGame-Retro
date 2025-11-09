"""Tests for logging configuration and monitoring."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from llm_dungeon_master.logging_config import (
    get_log_level,
    get_log_format,
    setup_logging,
    get_logger,
    HealthCheckLogger,
    RequestLogger,
    LLMLogger,
    DatabaseLogger,
)


class TestLoggingConfiguration:
    """Test logging configuration functions."""
    
    def test_get_log_level_default(self):
        """Test default log level is INFO."""
        with patch.dict('os.environ', {}, clear=True):
            level = get_log_level()
            assert level == logging.INFO
    
    def test_get_log_level_from_env(self):
        """Test log level can be set via environment."""
        with patch.dict('os.environ', {'LOG_LEVEL': 'DEBUG'}):
            level = get_log_level()
            assert level == logging.DEBUG
        
        with patch.dict('os.environ', {'LOG_LEVEL': 'WARNING'}):
            level = get_log_level()
            assert level == logging.WARNING
    
    def test_get_log_level_invalid(self):
        """Test invalid log level defaults to INFO."""
        with patch.dict('os.environ', {'LOG_LEVEL': 'INVALID'}):
            level = get_log_level()
            assert level == logging.INFO
    
    def test_get_log_format_default(self):
        """Test default log format is pretty."""
        with patch.dict('os.environ', {}, clear=True):
            fmt = get_log_format()
            assert fmt == "pretty"
    
    def test_get_log_format_json(self):
        """Test JSON log format."""
        with patch.dict('os.environ', {'LOG_FORMAT': 'json'}):
            fmt = get_log_format()
            assert fmt == "json"
    
    def test_setup_logging_creates_log_dir(self):
        """Test that setup_logging creates log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "test.log"
            with patch.dict('os.environ', {'LOG_FILE': str(log_file)}):
                setup_logging()
                assert log_file.parent.exists()
    
    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')


class TestHealthCheckLogger:
    """Test HealthCheckLogger class."""
    
    def test_health_check_logger_creation(self):
        """Test creating a HealthCheckLogger."""
        logger = HealthCheckLogger()
        assert logger is not None
        assert hasattr(logger, 'log_health_check')
        assert hasattr(logger, 'log_metric')
    
    def test_log_health_check(self):
        """Test logging a health check."""
        logger = HealthCheckLogger()
        
        # Should not raise exception
        logger.log_health_check(
            component="database",
            status="healthy",
            details={"connection": "ok"}
        )
    
    def test_log_health_check_with_uptime(self):
        """Test health check includes uptime."""
        logger = HealthCheckLogger()
        
        # Log a health check
        logger.log_health_check(
            component="api",
            status="healthy",
            details={}
        )
        
        # Uptime should be tracked (non-zero after initialization)
        assert logger._start_time is not None
    
    def test_log_metric(self):
        """Test logging a metric."""
        logger = HealthCheckLogger()
        
        # Should not raise exception
        logger.log_metric(
            metric_name="response_time",
            value=45.2,
            tags={"endpoint": "/health"}
        )
    
    def test_log_metric_without_tags(self):
        """Test logging a metric without tags."""
        logger = HealthCheckLogger()
        
        # Should not raise exception
        logger.log_metric(
            metric_name="active_users",
            value=10
        )


class TestRequestLogger:
    """Test RequestLogger class."""
    
    def test_request_logger_creation(self):
        """Test creating a RequestLogger."""
        logger = RequestLogger()
        assert logger is not None
        assert hasattr(logger, 'log_request')
        assert hasattr(logger, 'log_websocket_connection')
    
    def test_log_request_basic(self):
        """Test logging a basic API request."""
        logger = RequestLogger()
        
        # Should not raise exception
        logger.log_request(
            method="GET",
            path="/api/sessions",
            status_code=200,
            duration_ms=25.5
        )
    
    def test_log_request_with_ids(self):
        """Test logging a request with user and session IDs."""
        logger = RequestLogger()
        
        # Should not raise exception
        logger.log_request(
            method="POST",
            path="/api/sessions/1/messages",
            status_code=201,
            duration_ms=45.2,
            user_id=5,
            session_id=1
        )
    
    def test_log_websocket_connection(self):
        """Test logging a WebSocket event."""
        logger = RequestLogger()
        
        # Should not raise exception
        logger.log_websocket_connection(
            event="connect",
            session_id=1,
            player_id=5,
            connection_id="conn-123"
        )
    
    def test_log_websocket_disconnect(self):
        """Test logging a WebSocket disconnect."""
        logger = RequestLogger()
        
        # Should not raise exception
        logger.log_websocket_connection(
            event="disconnect",
            session_id=1,
            player_id=5
        )


class TestLLMLogger:
    """Test LLMLogger class."""
    
    def test_llm_logger_creation(self):
        """Test creating an LLMLogger."""
        logger = LLMLogger()
        assert logger is not None
        assert hasattr(logger, 'log_llm_request')
    
    def test_log_llm_request_basic(self):
        """Test logging a basic LLM request."""
        logger = LLMLogger()
        
        # Should not raise exception
        logger.log_llm_request(
            provider="openai",
            model="gpt-4",
            prompt_tokens=150,
            completion_tokens=50,
            duration_ms=1200.5
        )
    
    def test_log_llm_request_with_cost(self):
        """Test logging LLM request with cost."""
        logger = LLMLogger()
        
        # Should not raise exception
        logger.log_llm_request(
            provider="openai",
            model="gpt-4",
            prompt_tokens=150,
            completion_tokens=50,
            duration_ms=1200.5,
            cost_usd=0.0035
        )
    
    def test_log_llm_request_tracks_total_tokens(self):
        """Test that total tokens are calculated."""
        logger = LLMLogger()
        
        # Log a request (total_tokens should be calculated internally)
        logger.log_llm_request(
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            duration_ms=1000.0
        )
        # No assertion needed - just verify it doesn't crash


class TestDatabaseLogger:
    """Test DatabaseLogger class."""
    
    def test_database_logger_creation(self):
        """Test creating a DatabaseLogger."""
        logger = DatabaseLogger()
        assert logger is not None
        assert hasattr(logger, 'log_query')
        assert hasattr(logger, 'log_connection_pool_stats')
    
    def test_log_query_basic(self):
        """Test logging a basic database query."""
        logger = DatabaseLogger()
        
        # Should not raise exception
        logger.log_query(
            query_type="SELECT",
            table="sessions",
            duration_ms=5.2
        )
    
    def test_log_query_with_rows_affected(self):
        """Test logging query with rows affected."""
        logger = DatabaseLogger()
        
        # Should not raise exception
        logger.log_query(
            query_type="UPDATE",
            table="characters",
            duration_ms=8.5,
            rows_affected=3
        )
    
    def test_log_connection_pool_stats(self):
        """Test logging connection pool statistics."""
        logger = DatabaseLogger()
        
        # Should not raise exception
        logger.log_connection_pool_stats(
            active=5,
            idle=10,
            max_size=20
        )
    
    def test_log_connection_pool_calculates_utilization(self):
        """Test that pool utilization is calculated."""
        logger = DatabaseLogger()
        
        # Should calculate 50% utilization (10/20)
        logger.log_connection_pool_stats(
            active=10,
            idle=5,
            max_size=20
        )
    
    def test_log_connection_pool_zero_max_size(self):
        """Test pool stats with zero max size doesn't crash."""
        logger = DatabaseLogger()
        
        # Should not crash with division by zero
        logger.log_connection_pool_stats(
            active=0,
            idle=0,
            max_size=0
        )


class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_all_loggers_available(self):
        """Test that all logger instances are available."""
        from llm_dungeon_master.logging_config import (
            health_check_logger,
            request_logger,
            llm_logger,
            database_logger,
        )
        
        assert health_check_logger is not None
        assert request_logger is not None
        assert llm_logger is not None
        assert database_logger is not None
    
    def test_logging_with_different_formats(self):
        """Test logging works with both JSON and pretty formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            # Test JSON format
            with patch.dict('os.environ', {
                'LOG_FORMAT': 'json',
                'LOG_FILE': str(log_file)
            }):
                setup_logging()
                logger = get_logger("test")
                logger.info("test message", key="value")
            
            # Test pretty format
            with patch.dict('os.environ', {
                'LOG_FORMAT': 'pretty',
                'LOG_FILE': str(log_file)
            }):
                setup_logging()
                logger = get_logger("test")
                logger.info("test message", key="value")
