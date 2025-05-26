"""Health check endpoints with monitoring integration."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import psutil
import asyncio
import aioredis
from datetime import datetime, timedelta
import os
from sqlalchemy import text
from ..database import get_db
from ..monitoring.cloud_monitoring import CloudMonitoringService
from ..gpu_manager import GPUManager
from ..config import get_settings

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


class HealthChecker:
    """Comprehensive health checking with monitoring integration."""
    
    def __init__(self):
        self.monitoring = CloudMonitoringService()
        self.gpu_manager = GPUManager()
        self._checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "adk": self._check_adk,
            "gpu": self._check_gpu,
            "disk": self._check_disk,
            "memory": self._check_memory,
            "monitoring": self._check_monitoring
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start = datetime.now()
            async with get_db() as db:
                result = await db.execute(text("SELECT 1"))
                latency = (datetime.now() - start).total_seconds() * 1000
                
                # Check connection pool
                pool_size = db.bind.pool.size()
                pool_checked_out = db.bind.pool.checked_out()
                
                return {
                    "status": "healthy",
                    "latency_ms": latency,
                    "pool_size": pool_size,
                    "connections_active": pool_checked_out,
                    "connections_available": pool_size - pool_checked_out
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            redis = await aioredis.create_redis_pool(settings.REDIS_URL)
            start = datetime.now()
            await redis.ping()
            latency = (datetime.now() - start).total_seconds() * 1000
            
            # Get Redis info
            info = await redis.info()
            memory_used = info.get("used_memory", 0)
            connected_clients = info.get("connected_clients", 0)
            
            redis.close()
            await redis.wait_closed()
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "memory_used_mb": memory_used / 1024 / 1024,
                "connected_clients": connected_clients
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_adk(self) -> Dict[str, Any]:
        """Check ADK service availability."""
        try:
            # Check if ADK service is configured
            if not hasattr(settings, "ADK_PROJECT_ID"):
                return {
                    "status": "not_configured",
                    "message": "ADK not configured"
                }
            
            # Try to import ADK components
            from ..services.adk_service import ADKService
            
            # Check agent availability
            adk_service = ADKService()
            agents = {
                "orchestrator": hasattr(adk_service, "orchestrator_agent"),
                "retrieval": hasattr(adk_service, "retrieval_agent"),
                "analysis": hasattr(adk_service, "analysis_agent"),
                "knowledge_graph": hasattr(adk_service, "knowledge_graph_agent"),
                "citation": hasattr(adk_service, "citation_agent")
            }
            
            healthy_agents = sum(1 for available in agents.values() if available)
            
            return {
                "status": "healthy" if healthy_agents == len(agents) else "degraded",
                "agents": agents,
                "healthy_agents": healthy_agents,
                "total_agents": len(agents)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_gpu(self) -> Dict[str, Any]:
        """Check GPU availability and usage."""
        try:
            gpu_status = self.gpu_manager.get_status()
            
            if not gpu_status["gpus"]:
                return {
                    "status": "not_available",
                    "message": "No GPUs detected"
                }
            
            # Calculate average GPU usage
            total_usage = sum(gpu["usage"] for gpu in gpu_status["gpus"])
            avg_usage = total_usage / len(gpu_status["gpus"])
            
            # Check if any GPU is overloaded
            overloaded = any(gpu["usage"] > 90 for gpu in gpu_status["gpus"])
            
            return {
                "status": "unhealthy" if overloaded else "healthy",
                "gpu_count": len(gpu_status["gpus"]),
                "average_usage": avg_usage,
                "gpus": gpu_status["gpus"]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_disk(self) -> Dict[str, Any]:
        """Check disk space availability."""
        try:
            disk_usage = psutil.disk_usage("/")
            
            return {
                "status": "healthy" if disk_usage.percent < 80 else "warning",
                "used_percent": disk_usage.percent,
                "free_gb": disk_usage.free / (1024 ** 3),
                "total_gb": disk_usage.total / (1024 ** 3)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            
            return {
                "status": "healthy" if memory.percent < 80 else "warning",
                "used_percent": memory.percent,
                "available_gb": memory.available / (1024 ** 3),
                "total_gb": memory.total / (1024 ** 3)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_monitoring(self) -> Dict[str, Any]:
        """Check monitoring service status."""
        try:
            # Check if monitoring is configured
            if not self.monitoring.project_id:
                return {
                    "status": "not_configured",
                    "message": "Monitoring not configured"
                }
            
            # Try to write a test metric
            self.monitoring.increment_counter(
                "health_check_performed",
                labels={"check_type": "monitoring"}
            )
            
            return {
                "status": "healthy",
                "project_id": self.monitoring.project_id,
                "metrics_enabled": True,
                "tracing_enabled": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        
        # Run checks in parallel
        tasks = {
            name: asyncio.create_task(check())
            for name, check in self._checks.items()
        }
        
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Determine overall health
        statuses = [check.get("status", "unknown") for check in results.values()]
        
        if all(status == "healthy" for status in statuses):
            overall_status = "healthy"
        elif any(status in ["unhealthy", "error"] for status in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        # Record health check metrics
        self.monitoring.increment_counter(
            "health_checks_total",
            labels={"overall_status": overall_status}
        )
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }


# Initialize health checker
health_checker = HealthChecker()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "parallax-pal-api",
        "version": os.getenv("APP_VERSION", "unknown")
    }


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    # Quick checks for critical services
    try:
        # Check database
        async with get_db() as db:
            await db.execute(text("SELECT 1"))
        
        # Check Redis
        redis = await aioredis.create_redis_pool(settings.REDIS_URL)
        await redis.ping()
        redis.close()
        await redis.wait_closed()
        
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with all subsystem statuses."""
    return await health_checker.check_all()


@router.get("/metrics/summary")
async def metrics_summary():
    """Get a summary of key metrics."""
    monitoring = CloudMonitoringService()
    
    try:
        # Get current metrics from Prometheus
        metrics = {
            "active_users": monitoring.get_gauge_value("active_websocket_connections"),
            "requests_per_minute": monitoring.get_counter_rate("http_requests_total", "1m"),
            "average_latency": monitoring.get_histogram_average("http_request_duration_seconds"),
            "error_rate": monitoring.get_counter_rate("http_errors_total", "5m"),
            "agent_invocations": monitoring.get_counter_value("agent_invocations_total"),
            "cache_hit_rate": monitoring.calculate_cache_hit_rate()
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        return {
            "error": f"Failed to retrieve metrics: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/dependencies")
async def check_dependencies():
    """Check all external dependencies."""
    dependencies = {
        "google_cloud": {
            "vertex_ai": await _check_vertex_ai(),
            "cloud_storage": await _check_cloud_storage(),
            "cloud_monitoring": await _check_cloud_monitoring()
        },
        "external_apis": {
            "openai": await _check_openai_api(),
            "google_search": await _check_google_search_api()
        }
    }
    
    return dependencies


async def _check_vertex_ai() -> Dict[str, Any]:
    """Check Vertex AI availability."""
    try:
        from google.cloud import aiplatform
        aiplatform.init(project=settings.GCP_PROJECT_ID)
        return {"status": "available", "project": settings.GCP_PROJECT_ID}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


async def _check_cloud_storage() -> Dict[str, Any]:
    """Check Cloud Storage availability."""
    try:
        from google.cloud import storage
        client = storage.Client(project=settings.GCP_PROJECT_ID)
        # List buckets to verify access
        buckets = list(client.list_buckets(max_results=1))
        return {"status": "available", "accessible": True}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


async def _check_cloud_monitoring() -> Dict[str, Any]:
    """Check Cloud Monitoring availability."""
    try:
        monitoring = CloudMonitoringService()
        if monitoring.project_id:
            return {"status": "available", "project": monitoring.project_id}
        else:
            return {"status": "not_configured"}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


async def _check_openai_api() -> Dict[str, Any]:
    """Check OpenAI API availability."""
    try:
        import openai
        # Just check if API key is configured
        if settings.OPENAI_API_KEY:
            return {"status": "configured"}
        else:
            return {"status": "not_configured"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _check_google_search_api() -> Dict[str, Any]:
    """Check Google Search API availability."""
    try:
        if settings.GOOGLE_SEARCH_API_KEY and settings.GOOGLE_SEARCH_ENGINE_ID:
            return {"status": "configured"}
        else:
            return {"status": "not_configured"}
    except Exception as e:
        return {"status": "error", "error": str(e)}