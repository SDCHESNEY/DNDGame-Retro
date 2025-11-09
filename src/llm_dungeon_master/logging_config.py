"""Logging configuration for LLM Dungeon Master.

Provides structured JSON logging for production and pretty console logging for development.
Includes log rotation, health check endpoints, and container monitoring support.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import structlog


def get_log_level() -> int:
    """Get log level from environment variable."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def get_log_format() -> str:
    """Get log format from environment variable."""
    return os.getenv("LOG_FORMAT", "pretty").lower()


def setup_logging() -> None:
    """Configure logging based on environment settings.
    
    In production (LOG_FORMAT=json), uses structured JSON logging.
    In development (LOG_FORMAT=pretty), uses colored console output.
    """
    log_level = get_log_level()
    log_format = get_log_format()
    
    # Create logs directory if it doesn't exist
    log_dir = Path(os.getenv("LOG_FILE", "./logs/rpg_dungeon.log")).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    if log_format == "json":
        # Production: JSON logging
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Pretty console logging
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Add rotating file handler
    log_file = os.getenv("LOG_FILE", "./logs/rpg_dungeon.log")
    max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB default
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setLevel(log_level)
    
    if log_format == "json":
        file_handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    
    logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__ of the module)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class HealthCheckLogger:
    """Logger for health check and monitoring endpoints."""
    
    def __init__(self):
        self.logger = get_logger("health_check")
        self._start_time = datetime.now()
    
    def log_health_check(self, component: str, status: str, details: Dict[str, Any]) -> None:
        """Log a health check result.
        
        Args:
            component: Component name (e.g., "database", "redis", "api")
            status: Health status ("healthy", "degraded", "unhealthy")
            details: Additional details about the health check
        """
        self.logger.info(
            "health_check",
            component=component,
            status=status,
            details=details,
            uptime_seconds=(datetime.now() - self._start_time).total_seconds(),
        )
    
    def log_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Log a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
        """
        self.logger.info(
            "metric",
            metric_name=metric_name,
            value=value,
            tags=tags or {},
        )


class RequestLogger:
    """Logger for API requests and responses."""
    
    def __init__(self):
        self.logger = get_logger("api")
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: int = None,
        session_id: int = None,
    ) -> None:
        """Log an API request.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            user_id: Optional user ID
            session_id: Optional session ID
        """
        self.logger.info(
            "api_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            session_id=session_id,
        )
    
    def log_websocket_connection(
        self,
        event: str,
        session_id: int = None,
        player_id: int = None,
        connection_id: str = None,
    ) -> None:
        """Log a WebSocket connection event.
        
        Args:
            event: Event type ("connect", "disconnect", "message")
            session_id: Optional session ID
            player_id: Optional player ID
            connection_id: Optional connection ID
        """
        self.logger.info(
            f"websocket_{event}",
            session_id=session_id,
            player_id=player_id,
            connection_id=connection_id,
        )


class LLMLogger:
    """Logger for LLM API interactions."""
    
    def __init__(self):
        self.logger = get_logger("llm")
    
    def log_llm_request(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        cost_usd: float = None,
    ) -> None:
        """Log an LLM API request.
        
        Args:
            provider: LLM provider name
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            duration_ms: Request duration in milliseconds
            cost_usd: Optional cost in USD
        """
        self.logger.info(
            "llm_request",
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
        )


class DatabaseLogger:
    """Logger for database operations."""
    
    def __init__(self):
        self.logger = get_logger("database")
    
    def log_query(
        self,
        query_type: str,
        table: str,
        duration_ms: float,
        rows_affected: int = None,
    ) -> None:
        """Log a database query.
        
        Args:
            query_type: Query type ("SELECT", "INSERT", "UPDATE", "DELETE")
            table: Table name
            duration_ms: Query duration in milliseconds
            rows_affected: Optional number of rows affected
        """
        self.logger.info(
            "database_query",
            query_type=query_type,
            table=table,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
        )
    
    def log_connection_pool_stats(
        self,
        active: int,
        idle: int,
        max_size: int,
    ) -> None:
        """Log database connection pool statistics.
        
        Args:
            active: Number of active connections
            idle: Number of idle connections
            max_size: Maximum pool size
        """
        self.logger.info(
            "connection_pool_stats",
            active=active,
            idle=idle,
            max_size=max_size,
            utilization=active / max_size if max_size > 0 else 0,
        )


# Initialize logging on module import
setup_logging()

# Export logger instances
health_check_logger = HealthCheckLogger()
request_logger = RequestLogger()
llm_logger = LLMLogger()
database_logger = DatabaseLogger()
