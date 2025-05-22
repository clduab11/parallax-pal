from typing import Dict, Any
try:
    from pydantic_settings import BaseSettings
    from pydantic import PostgresDsn, HttpUrl, EmailStr, validator
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, PostgresDsn, HttpUrl, EmailStr, validator
import os
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Parallax Pal"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis Cache
    REDIS_URL: str
    REDIS_PASSWORD: str = None
    REDIS_DB: int = 0
    
    # Frontend
    FRONTEND_URL: HttpUrl
    CORS_ORIGINS: list[str] = ["*"]
    
    # OAuth Providers
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: HttpUrl
    
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: HttpUrl
    
    FACEBOOK_CLIENT_ID: str
    FACEBOOK_CLIENT_SECRET: str
    FACEBOOK_REDIRECT_URI: HttpUrl
    
    INSTAGRAM_CLIENT_ID: str
    INSTAGRAM_CLIENT_SECRET: str
    INSTAGRAM_REDIRECT_URI: HttpUrl
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: EmailStr
    SMTP_FROM_NAME: str = "Parallax Pal"
    
    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # GPU Settings
    GPU_MEMORY_THRESHOLD: float = 0.9  # 90% memory usage threshold
    DEFAULT_MODEL: str = "llama2"
    OLLAMA_API_URL: str = "http://localhost:11434"
    
    # Monitoring
    SENTRY_DSN: str = None
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Security
    ALLOWED_HOSTS: list[str] = ["*"]
    SSL_KEYFILE: str = None
    SSL_CERTFILE: str = None
    SECURE_HEADERS: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL is properly formatted"""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=v.get("user"),
            password=v.get("password"),
            host=v.get("host"),
            port=v.get("port"),
            path=f"/{v.get('database')}"
        )

    @validator("REDIS_URL", pre=True)
    def validate_redis_url(cls, v: str) -> str:
        """Ensure REDIS_URL is properly formatted"""
        if isinstance(v, str):
            return v
        return f"redis://{v.get('host')}:{v.get('port')}/{v.get('db', 0)}"

    @validator("CORS_ORIGINS", pre=True)
    def validate_cors_origins(cls, v: Any) -> list[str]:
        """Convert CORS_ORIGINS to list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("ALLOWED_HOSTS", pre=True)
    def validate_allowed_hosts(cls, v: Any) -> list[str]:
        """Convert ALLOWED_HOSTS to list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

def get_db_url() -> str:
    """Get database URL with proper formatting"""
    settings = get_settings()
    return str(settings.DATABASE_URL)

# Environment-specific settings
ENVIRONMENT_SETTINGS: Dict[str, Dict[str, Any]] = {
    "development": {
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "ENABLE_METRICS": False,
    },
    "staging": {
        "DEBUG": False,
        "LOG_LEVEL": "INFO",
        "CORS_ORIGINS": ["https://staging.parallaxpal.com"],
        "ALLOWED_HOSTS": ["staging.parallaxpal.com"],
    },
    "production": {
        "DEBUG": False,
        "LOG_LEVEL": "WARNING",
        "SECURE_HEADERS": True,
        "CORS_ORIGINS": ["https://parallaxpal.com"],
        "ALLOWED_HOSTS": ["parallaxpal.com"],
    }
}

# Load environment-specific settings
settings = get_settings()
env_settings = ENVIRONMENT_SETTINGS.get(settings.ENVIRONMENT, {})
for key, value in env_settings.items():
    setattr(settings, key, value)

# OAuth configurations
OAUTH_SETTINGS = {
    "google": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": str(settings.GOOGLE_REDIRECT_URI),
        "scope": ["openid", "email", "profile"],
    },
    "github": {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "redirect_uri": str(settings.GITHUB_REDIRECT_URI),
        "scope": ["read:user", "user:email"],
    },
    "facebook": {
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "client_secret": settings.FACEBOOK_CLIENT_SECRET,
        "redirect_uri": str(settings.FACEBOOK_REDIRECT_URI),
        "scope": ["email", "public_profile"],
    },
    "instagram": {
        "client_id": settings.INSTAGRAM_CLIENT_ID,
        "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
        "redirect_uri": str(settings.INSTAGRAM_REDIRECT_URI),
        "scope": ["basic"],
    }
}

# Example .env file template
ENV_TEMPLATE = """
# Application
APP_NAME=Parallax Pal
DEBUG=false
ENVIRONMENT=development
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/parallaxpal

# Redis
REDIS_URL=redis://localhost:6379/0

# Frontend
FRONTEND_URL=http://localhost:3000

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:3000/auth/github/callback

FACEBOOK_CLIENT_ID=your-facebook-client-id
FACEBOOK_CLIENT_SECRET=your-facebook-client-secret
FACEBOOK_REDIRECT_URI=http://localhost:3000/auth/facebook/callback

INSTAGRAM_CLIENT_ID=your-instagram-client-id
INSTAGRAM_CLIENT_SECRET=your-instagram-client-secret
INSTAGRAM_REDIRECT_URI=http://localhost:3000/auth/instagram/callback

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=noreply@parallaxpal.com

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Monitoring
SENTRY_DSN=your-sentry-dsn
"""

def generate_env_file():
    """Generate .env file template"""
    with open(".env.example", "w") as f:
        f.write(ENV_TEMPLATE.strip())

if __name__ == "__main__":
    # Generate .env.example file when run directly
    generate_env_file()