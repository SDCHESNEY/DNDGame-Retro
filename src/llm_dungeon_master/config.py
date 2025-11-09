"""Configuration management for the LLM Dungeon Master."""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Supports both development (SQLite) and production (PostgreSQL/Redis) configurations.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    llm_provider: Literal["openai", "anthropic", "mock"] = "mock"
    llm_model: str = "gpt-4-turbo-preview"
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"  # Deprecated, use llm_model
    anthropic_api_key: str = ""
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    host: str = "0.0.0.0"  # Deprecated, use server_host
    port: int = 8000  # Deprecated, use server_port
    debug: bool = True
    
    # Database Configuration
    database_url: str = "sqlite:///./data/dndgame.db"
    postgres_db: str = "rpg_dungeon"
    postgres_user: str = "rpguser"
    postgres_password: str = ""
    sql_echo: bool = False
    
    # Redis Configuration (optional, for caching and session management)
    redis_url: str = ""
    redis_password: str = ""
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    session_timeout: int = 3600  # seconds
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "pretty"  # Options: json, pretty
    log_file: str = "./logs/rpg_dungeon.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # Feature Flags
    enable_websocket: bool = True
    enable_api_docs: bool = True
    enable_metrics: bool = True
    
    # Monitoring
    health_check_enabled: bool = True
    metrics_enabled: bool = True
    
    # Development
    hot_reload: bool = True
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug
    
    @property
    def use_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.database_url.startswith("postgresql")
    
    @property
    def use_redis(self) -> bool:
        """Check if Redis is configured."""
        return bool(self.redis_url)


# Global settings instance
settings = Settings()
