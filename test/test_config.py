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
    settings.database_url = "sqlite:///./dndgame.db"
    assert settings.database_url == "sqlite:///./dndgame.db"
    
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
