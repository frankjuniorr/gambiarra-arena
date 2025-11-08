"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Server
    host: str = "0.0.0.0"
    port: int = 3000
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # CORS
    cors_origins: list[str] = ["*"]

    # Rate Limiting
    rate_limit_max: int = 100
    rate_limit_window: int = 60

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_payload: int = 1048576

    # Session
    pin_length: int = 6
    session_timeout_ms: int = 7200000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
