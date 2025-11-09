"""Tests for configuration management."""

import pytest
import os
from llm_dungeon_master.config import Settings


def test_settings_defaults():
    """Test that settings have sensible defaults."""
    settings = Settings()
    
    assert settings.llm_provider in ["openai", "mock"]
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.database_url.startswith("sqlite://")
    assert settings.log_level == "INFO"


def test_settings_from_env(monkeypatch):
    """Test that settings can be loaded from environment variables."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
    monkeypatch.setenv("HOST", "localhost")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("DEBUG", "False")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    settings = Settings()
    
    assert settings.llm_provider == "openai"
    assert settings.openai_api_key == "test-key-123"
    assert settings.openai_model == "gpt-4"
    assert settings.host == "localhost"
    assert settings.port == 9000
    assert settings.debug is False
    assert settings.database_url == "sqlite:///test.db"
    assert settings.log_level == "DEBUG"


def test_cors_origins_list():
    """Test that CORS origins are properly parsed."""
    settings = Settings()
    settings.cors_origins = "http://localhost:3000,http://localhost:8000,https://example.com"
    
    origins_list = settings.cors_origins_list
    
    assert len(origins_list) == 3
    assert "http://localhost:3000" in origins_list
    assert "http://localhost:8000" in origins_list
    assert "https://example.com" in origins_list


def test_cors_origins_with_spaces():
    """Test CORS origins parsing with spaces."""
    settings = Settings()
    settings.cors_origins = "http://localhost:3000, http://localhost:8000, https://example.com"
    
    origins_list = settings.cors_origins_list
    
    # Should strip spaces
    assert len(origins_list) == 3
    assert all(" " not in origin for origin in origins_list)


def test_llm_provider_validation():
    """Test that LLM provider is validated."""
    settings = Settings()
    
    # Valid providers
    settings.llm_provider = "openai"
    assert settings.llm_provider == "openai"
    
    settings.llm_provider = "mock"
    assert settings.llm_provider == "mock"


def test_database_url_formats():
    """Test different database URL formats."""
    settings = Settings()
    
    # SQLite in-memory
    settings.database_url = "sqlite:///:memory:"
    assert settings.database_url == "sqlite:///:memory:"
    
    # SQLite file
    settings.database_url = "sqlite:///./data/dndgame.db"
    assert settings.database_url == "sqlite:///./data/dndgame.db"
    
    # PostgreSQL
    settings.database_url = "postgresql://user:pass@localhost/dbname"
    assert settings.database_url.startswith("postgresql://")


def test_port_number_range():
    """Test that port can be set to different values."""
    settings = Settings()
    
    settings.port = 8080
    assert settings.port == 8080
    assert isinstance(settings.port, int)
    
    settings.port = 3000
    assert settings.port == 3000


# Phase 8: Enhanced Configuration Tests

def test_new_server_host_setting(monkeypatch):
    """Test new server_host setting."""
    monkeypatch.setenv("SERVER_HOST", "127.0.0.1")
    settings = Settings()
    assert settings.server_host == "127.0.0.1"


def test_new_server_port_setting(monkeypatch):
    """Test new server_port setting."""
    monkeypatch.setenv("SERVER_PORT", "9000")
    settings = Settings()
    assert settings.server_port == 9000


def test_llm_model_setting(monkeypatch):
    """Test llm_model setting."""
    monkeypatch.setenv("LLM_MODEL", "gpt-4")
    settings = Settings()
    assert settings.llm_model == "gpt-4"


def test_postgres_settings(monkeypatch):
    """Test PostgreSQL-specific settings."""
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")
    
    settings = Settings()
    assert settings.postgres_db == "test_db"
    assert settings.postgres_user == "test_user"
    assert settings.postgres_password == "test_pass"


def test_redis_settings(monkeypatch):
    """Test Redis configuration."""
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("REDIS_PASSWORD", "redis_pass")
    
    settings = Settings()
    assert settings.redis_url == "redis://localhost:6379"
    assert settings.redis_password == "redis_pass"


def test_rate_limiting_settings(monkeypatch):
    """Test rate limiting configuration."""
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "120")
    monkeypatch.setenv("RATE_LIMIT_BURST", "20")
    
    settings = Settings()
    assert settings.rate_limit_enabled is True
    assert settings.rate_limit_per_minute == 120
    assert settings.rate_limit_burst == 20


def test_logging_configuration(monkeypatch):
    """Test logging settings."""
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("LOG_FILE", "/var/log/app.log")
    monkeypatch.setenv("LOG_MAX_BYTES", "20971520")
    monkeypatch.setenv("LOG_BACKUP_COUNT", "10")
    
    settings = Settings()
    assert settings.log_format == "json"
    assert settings.log_file == "/var/log/app.log"
    assert settings.log_max_bytes == 20971520
    assert settings.log_backup_count == 10


def test_feature_flags(monkeypatch):
    """Test feature flag settings."""
    monkeypatch.setenv("ENABLE_WEBSOCKET", "false")
    monkeypatch.setenv("ENABLE_API_DOCS", "false")
    monkeypatch.setenv("ENABLE_METRICS", "false")
    
    settings = Settings()
    assert settings.enable_websocket is False
    assert settings.enable_api_docs is False
    assert settings.enable_metrics is False


def test_is_production_property():
    """Test is_production property."""
    settings = Settings()
    settings.debug = True
    assert settings.is_production is False
    
    settings.debug = False
    assert settings.is_production is True


def test_use_postgresql_property():
    """Test use_postgresql property."""
    settings = Settings()
    
    settings.database_url = "sqlite:///./data/test.db"
    assert settings.use_postgresql is False
    
    settings.database_url = "postgresql://user:pass@localhost/db"
    assert settings.use_postgresql is True


def test_use_redis_property():
    """Test use_redis property."""
    settings = Settings()
    
    settings.redis_url = ""
    assert settings.use_redis is False
    
    settings.redis_url = "redis://localhost:6379"
    assert settings.use_redis is True


def test_session_timeout_setting(monkeypatch):
    """Test session timeout configuration."""
    monkeypatch.setenv("SESSION_TIMEOUT", "7200")
    settings = Settings()
    assert settings.session_timeout == 7200
