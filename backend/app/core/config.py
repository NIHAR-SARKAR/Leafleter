"""Application settings using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Leafleter"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"

    # Token lifetimes in minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 14400
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./leafleter.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5240", "http://localhost:3000"]

    # Object Storage
    OBJECT_STORAGE_DRIVER: Literal["local", "s3"] = "local"
    OBJECT_STORAGE_ENDPOINT: str | None = None
    OBJECT_STORAGE_ACCESS_KEY: str | None = None
    OBJECT_STORAGE_SECRET_KEY: str | None = None
    OBJECT_STORAGE_BUCKET: str = "leafleter"
    OBJECT_STORAGE_REGION: str = "us-east-1"
    LOCAL_STORAGE_PATH: str = "./storage"

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_JOBSTORE_URL: str | None = None

    # Search engine provider API keys
    SERPAPI_API_KEY: str | None = None
    BING_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    GOOGLE_CSE_KEY: str | None = None
    GOOGLE_CSE_CX: str | None = None

    # AI provider API keys (also stored per-provider; these are global fallbacks)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    BEDROCK_ACCESS_KEY: str | None = None
    BEDROCK_SECRET_KEY: str | None = None
    KIMI_API_KEY: str | None = None
    QWEN_API_KEY: str | None = None

    # SMTP
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5240"

    # Intelligence Core
    ENABLE_INTELLIGENCE_CORE: bool = True
    ENABLE_AUTO_WORKFLOWS: bool = True
    ENABLE_SMART_ALERTS: bool = True
    ENABLE_AUTO_REPORTS: bool = True
    ENABLE_ACTION_AI_GENERATION: bool = False
    INTELLIGENCE_DB_PATH: str = "data/intelligence.db"
    DAILY_PULSE_HOUR: int = 9
    DAILY_PULSE_TIMEZONE: str = "UTC"
    TOPIC_ANOMALITY_THRESHOLD_PCT: int = 20
    COMPETITOR_MENTION_THRESHOLD: int = 2
    ALERT_AGGREGATION_HOURS: int = 24
    REPORT_TRIGGER_ALERT_COUNT: int = 3
    CONTEXT_MEMORY_MAX_EVENTS: int = 50
    WORKFLOW_RETRY_ATTEMPTS: int = 3
    PRIORITY_QUEUE_MAX_SIZE: int = 50
    INTELLIGENCE_AI_MODEL: str = "gpt-4"
    ACTION_GENERATION_MAX_PER_EVENT: int = 3

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        if isinstance(v, list):
            return v
        raise ValueError("CORS_ORIGINS must be a list or comma-separated string")

    @property
    def is_sqlite(self) -> bool:
        """Check if the configured database is SQLite."""
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
