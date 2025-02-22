import logging
import time
from functools import wraps
from typing import Callable, Dict, Any
import json
from datetime import datetime
import traceback
from prometheus_client import Counter, Histogram, start_http_server
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
RESEARCH_TASKS = Counter('research_tasks_total', 'Total research tasks', ['status'])
ERROR_COUNT = Counter('error_count_total', 'Total errors', ['type'])

class APILogger:
    def __init__(self):
        self.start_prometheus()

    def start_prometheus(self):
        """Start Prometheus metrics server"""
        try:
            prometheus_port = int(os.getenv("PROMETHEUS_PORT", 9090))
            start_http_server(prometheus_port)
            logger.info(f"Prometheus metrics server started on port {prometheus_port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {str(e)}")

    def log_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Log HTTP request details"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    def log_research_task(self, status: str):
        """Log research task status"""
        RESEARCH_TASKS.labels(status=status).inc()

    def log_error(self, error_type: str, error: Exception):
        """Log error details"""
        ERROR_COUNT.labels(type=error_type).inc()
        logger.error(f"Error type: {error_type}")
        logger.error(f"Error message: {str(error)}")
        logger.error(f"Stacktrace: {''.join(traceback.format_tb(error.__traceback__))}")

# Monitoring decorator for API endpoints
def monitor_endpoint(endpoint_name: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 500
            try:
                response = await func(*args, **kwargs)
                status_code = response.status_code if hasattr(response, 'status_code') else 200
                return response
            except Exception as e:
                api_logger.log_error("endpoint_error", e)
                raise
            finally:
                duration = time.time() - start_time
                api_logger.log_request(
                    method=kwargs.get('method', 'UNKNOWN'),
                    endpoint=endpoint_name,
                    status_code=status_code,
                    duration=duration
                )
        return wrapper
    return decorator

class RequestLogMiddleware:
    """Middleware for logging all requests"""
    async def __call__(self, request, call_next):
        start_time = time.time()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration = time.time() - start_time
            status_code = response.status_code if response else 500
            api_logger.log_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration=duration
            )

class StructuredLogger:
    """Structured logging with JSON format"""
    def __init__(self, service_name: str):
        self.service_name = service_name

    def log(self, level: str, message: str, **kwargs):
        """Log a message with structured data"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": level,
            "message": message,
            **kwargs
        }
        log_message = json.dumps(log_data)
        
        if level == "error":
            logger.error(log_message)
        elif level == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)

def setup_monitoring(app):
    """Setup monitoring for the FastAPI application"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Initialize monitoring components
    global api_logger
    api_logger = APILogger()
    
    # Add middleware
    app.middleware("http")(RequestLogMiddleware())
    
    # Create structured logger
    return StructuredLogger("parallax-pal-api")

# Initialize API logger
api_logger = APILogger()