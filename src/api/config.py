from typing import Any, Dict, Optional
from pydantic import BaseSettings, PostgresDsn, validator
import os
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    ENV: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    CACHE_TTL: int = 3600

    # Research
    MAX_CONCURRENT_TASKS: int = 5
    TASK_TIMEOUT: int = 300
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

    # Monitoring
    LOG_LEVEL: str = "INFO"
    PROMETHEUS_PORT: int = 9090
    ENABLE_METRICS: bool = True
    METRICS_PREFIX: str = "parallaxpal_"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    MAX_TOKENS: int = 2000

    # Search Engine
    SEARCH_RESULTS_LIMIT: int = 10
    SEARCH_TIMEOUT: int = 30

    # Error Reporting
    ENABLE_ERROR_REPORTING: bool = True
    ERROR_REPORTING_EMAIL: Optional[str] = None

    # Documentation
    DOCS_URL: str = "/api/docs"
    REDOC_URL: str = "/api/redoc"
    OPENAPI_URL: str = "/api/openapi.json"

    # Feature Flags
    ENABLE_CACHING: bool = True
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_AUTH: bool = True
    ENABLE_MONITORING: bool = True

    # Admin
    ADMIN_EMAIL: str
    ADMIN_USERNAME: str = "admin"

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: Optional[str]) -> Any:
        """Validate and possibly modify the database URL."""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            path=f"/{os.getenv('DB_NAME', 'parallaxpal')}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance.
    Uses LRU cache to avoid reading the .env file for every request.
    """
    return Settings()

# Initialize global settings instance
settings = get_settings()

def get_db_url() -> str:
    """Get database URL with SSL mode based on environment."""
    if settings.ENV == "production":
        return str(settings.DATABASE_URL) + "?sslmode=require"
    return str(settings.DATABASE_URL)

def is_production() -> bool:
    """Check if running in production environment."""
    return settings.ENV == "production"

def get_cors_origins() -> list:
    """Get CORS origins based on environment."""
    if is_production():
        return [settings.FRONTEND_URL]
    return ["*"]  # Allow all origins in development

def get_redis_settings() -> Dict[str, Any]:
    """Get Redis connection settings."""
    return {
        "url": settings.REDIS_URL,
        "max_connections": settings.REDIS_MAX_CONNECTIONS,
        "default_ttl": settings.CACHE_TTL
    }

def get_monitoring_settings() -> Dict[str, Any]:
    """Get monitoring configuration."""
    return {
        "prometheus_port": settings.PROMETHEUS_PORT,
        "enable_metrics": settings.ENABLE_METRICS,
        "metrics_prefix": settings.METRICS_PREFIX,
        "log_level": settings.LOG_LEVEL
    }

def get_security_settings() -> Dict[str, Any]:
    """Get security-related settings."""
    return {
        "secret_key": settings.SECRET_KEY,
        "algorithm": settings.ALGORITHM,
        "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
    }

def get_feature_flags() -> Dict[str, bool]:
    """Get feature flag settings."""
    return {
        "caching": settings.ENABLE_CACHING,
        "rate_limiting": settings.ENABLE_RATE_LIMITING,
        "auth": settings.ENABLE_AUTH,
        "monitoring": settings.ENABLE_MONITORING
    }