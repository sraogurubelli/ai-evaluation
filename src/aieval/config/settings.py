"""Application settings using Pydantic Settings."""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", case_sensitive=False)
    
    user: str = Field(default="aieval", description="PostgreSQL user")
    password: str = Field(default="aieval_dev", description="PostgreSQL password")
    db: str = Field(default="aieval", description="PostgreSQL database name")
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    
    @property
    def url(self) -> str:
        """Get database URL."""
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class ServerSettings(BaseSettings):
    """Server configuration."""
    
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=7890, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    model_config = SettingsConfigDict(env_prefix="LOG_", case_sensitive=False)
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log level"
    )
    format: Literal["console", "json"] = Field(
        default="console", description="Log format (console or json)"
    )
    export_logs: bool = Field(default=False, description="Export logs to file")
    dir: str = Field(default="logs", description="Log directory")
    file: str = Field(default="ai-evolution.log", description="Log filename")


class TemporalSettings(BaseSettings):
    """Temporal configuration."""
    
    model_config = SettingsConfigDict(env_prefix="TEMPORAL_", case_sensitive=False)
    
    host: str = Field(default="localhost:7233", description="Temporal server host")
    namespace: str = Field(default="default", description="Temporal namespace")
    task_queue: str = Field(default="ai-evolution", description="Temporal task queue")
    port: int = Field(default=7233, description="Temporal gRPC port")
    ui_port: int = Field(default=8088, description="Temporal UI port")


class LangfuseSettings(BaseSettings):
    """Langfuse configuration."""
    
    model_config = SettingsConfigDict(env_prefix="LANGFUSE_", case_sensitive=False)
    
    secret_key: str | None = Field(default=None, description="Langfuse secret key")
    public_key: str | None = Field(default=None, description="Langfuse public key")
    host: str | None = Field(default=None, description="Langfuse host URL")
    
    @property
    def enabled(self) -> bool:
        """Check if Langfuse is enabled."""
        return bool(self.secret_key and self.public_key and self.host)


class LLMSettings(BaseSettings):
    """LLM API configuration."""
    
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)
    
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY", description="OpenAI API key")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY", description="Anthropic API key")
    
    @property
    def openai_enabled(self) -> bool:
        """Check if OpenAI is enabled."""
        return bool(self.openai_api_key)
    
    @property
    def anthropic_enabled(self) -> bool:
        """Check if Anthropic is enabled."""
        return bool(self.anthropic_api_key)


class MLInfraSettings(BaseSettings):
    """ML Infra adapter configuration."""
    
    model_config = SettingsConfigDict(env_prefix="CHAT_", case_sensitive=False)
    
    base_url: str | None = Field(default=None, description="ML Infra base URL")
    endpoint: str = Field(default="/chat/unified", description="SSE streaming endpoint path")
    platform_url: str | None = Field(default=None, description="ML Infra platform URL")
    dashboard_url: str | None = Field(default=None, description="ML Infra dashboard URL")
    kg_url: str | None = Field(default=None, description="ML Infra knowledge graph URL")
    platform_auth_token: str | None = Field(default=None, description="ML Infra auth token")
    
    account_id: str = Field(default="default", description="Account ID")
    org_id: str = Field(default="default", description="Organization ID")
    project_id: str = Field(default="default", description="Project ID")


class SecuritySettings(BaseSettings):
    """Security configuration."""
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_", case_sensitive=False)
    
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    jwt_secret: str | None = Field(default=None, description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration in hours")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"], description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute per IP")


class MonitoringSettings(BaseSettings):
    """Monitoring configuration."""
    
    model_config = SettingsConfigDict(env_prefix="MONITORING_", case_sensitive=False)
    
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_path: str = Field(default="/metrics", description="Prometheus metrics path")
    opentelemetry_enabled: bool = Field(default=True, description="Enable OpenTelemetry tracing")
    opentelemetry_endpoint: str | None = Field(
        default=None, description="OpenTelemetry collector endpoint"
    )
    opentelemetry_service_name: str = Field(
        default="ai-evolution", description="OpenTelemetry service name"
    )


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment"
    )
    
    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    temporal: TemporalSettings = Field(default_factory=TemporalSettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    ml_infra: MLInfraSettings = Field(default_factory=MLInfraSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
