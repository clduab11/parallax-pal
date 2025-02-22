"""
Parallax Pal API
===============

A production-ready research and analytics platform that transforms raw data into actionable insights.
"""

import logging
from logging.config import dictConfig
import os
from .config import settings

__version__ = "1.0.0"

# Configure logging based on environment
LOG_LEVEL = settings.LOG_LEVEL.upper()

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "json_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "logs/parallax_api.json",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "simple",
            "filename": "logs/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "ERROR",
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console", "json_file", "error_file"],
    },
    "loggers": {
        "parallax_pal": {
            "level": LOG_LEVEL,
            "handlers": ["console", "json_file", "error_file"],
            "propagate": False,
        },
        "uvicorn": {
            "level": LOG_LEVEL,
            "handlers": ["console", "json_file"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["console", "error_file"],
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Apply logging configuration
dictConfig(logging_config)

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Log startup information
logger.info(
    "Parallax Pal API initializing",
    extra={
        "version": __version__,
        "environment": settings.ENV,
        "debug_mode": settings.DEBUG,
    }
)

# Import components that need to be available at package level
from .models import (
    User,
    ResearchTask,
    ResearchStatus,
    UserRole,
    ResearchAnalytics,
    APIKey
)

from .auth import (
    get_current_user,
    get_current_active_user,
    check_admin_role,
    create_access_token,
    get_password_hash,
    verify_password
)

from .research import research_service
from .cache import cache
from .monitoring import setup_monitoring, structured_logger

__all__ = [
    # Models
    "User",
    "ResearchTask",
    "ResearchStatus",
    "UserRole",
    "ResearchAnalytics",
    "APIKey",
    
    # Auth
    "get_current_user",
    "get_current_active_user",
    "check_admin_role",
    "create_access_token",
    "get_password_hash",
    "verify_password",
    
    # Services
    "research_service",
    "cache",
    
    # Monitoring
    "setup_monitoring",
    "structured_logger",
]