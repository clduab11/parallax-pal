"""
Enhanced Parallax Pal API with complete ADK integration

This is the main entry point for the enhanced API with native ADK support,
advanced security, distributed state management, and innovation features.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

# Import routers
from .routers import auth, subscription, adk
from .dependencies.auth import get_current_user
from .models import User

# Security and middleware
from .middleware.rate_limiter import RateLimiter
from .security.validation import ErrorResponse

# WebSocket manager
from .websocket_adk_enhanced import EnhancedADKWebSocketManager

# State management
from .state.distributed_state import DistributedStateManager

# Features
from .features import (
    VoiceInteractionHandler,
    CollaborativeResearchManager,
    ResearchExporter
)

# Monitoring
from .monitoring import structured_logger
from google.cloud import logging as cloud_logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize structured logging for production
if os.getenv('ENVIRONMENT') == 'production':
    client = cloud_logging.Client()
    client.setup_logging()


# Global instances
websocket_manager: EnhancedADKWebSocketManager = None
state_manager: DistributedStateManager = None
rate_limiter: RateLimiter = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager
    
    Handles startup and shutdown tasks
    """
    global websocket_manager, state_manager, rate_limiter
    
    # Startup
    logger.info("Starting Parallax Pal Enhanced API...")
    
    # Initialize state manager
    state_manager = DistributedStateManager(
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
        firestore_project=os.getenv('GOOGLE_CLOUD_PROJECT')
    )
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379')
    )
    
    # Initialize WebSocket manager
    websocket_manager = EnhancedADKWebSocketManager()
    await websocket_manager.initialize()
    
    # Initialize feature managers
    app.state.voice_handler = VoiceInteractionHandler(websocket_manager.adk)
    app.state.collab_manager = CollaborativeResearchManager(
        state_manager,
        websocket_manager,
        websocket_manager.adk
    )
    app.state.exporter = ResearchExporter()
    
    structured_logger.log(
        "info",
        "Parallax Pal API started successfully",
        environment=os.getenv('ENVIRONMENT', 'development')
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down Parallax Pal Enhanced API...")
    
    # Cleanup
    await websocket_manager.shutdown()
    await state_manager.close()
    await rate_limiter.close()
    
    structured_logger.log("info", "Parallax Pal API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Parallax Pal API",
    description="Multi-Agent Research Platform powered by Google Cloud ADK",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv('ALLOWED_HOSTS', 'localhost,*.parallaxpal.app').split(',')
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    
    if rate_limiter:
        return await rate_limiter.middleware(
            max_requests=60,  # Per minute
            window_seconds=60
        )(request, call_next)
    
    return await call_next(request)

# Request ID middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to all requests"""
    
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(subscription.router, prefix="/api/subscription", tags=["Subscription"])
app.include_router(adk.router, prefix="/api/adk", tags=["ADK"])

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    # Check critical services
    checks = {
        "api": "healthy",
        "websocket": "healthy" if websocket_manager else "unavailable",
        "state_manager": "healthy" if state_manager else "unavailable",
        "rate_limiter": "healthy" if rate_limiter else "unavailable"
    }
    
    # Check ADK agents if available
    if websocket_manager and hasattr(websocket_manager, 'adk'):
        try:
            agent_health = await websocket_manager.adk.get_agent_health()
            checks["adk_agents"] = agent_health['overall_status']
        except Exception:
            checks["adk_agents"] = "error"
    
    # Overall health
    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    
    return {
        "status": overall,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoint
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user)
):
    """
    Main WebSocket endpoint for real-time research
    
    Handles:
    - Research queries
    - Real-time updates
    - Voice interaction
    - Collaborative sessions
    """
    
    session_id = None
    
    try:
        # Connect with rate limiting
        session_id = await websocket_manager.connect(
            websocket,
            str(current_user.id),
            current_user.subscription_tier
        )
        
        if not session_id:
            return  # Connection rejected
        
        # Handle messages
        while True:
            data = await websocket.receive_json()
            await websocket_manager.handle_message(
                websocket,
                session_id,
                data
            )
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json(
                ErrorResponse.get("websocket_error", session_id)
            )
        except:
            pass
    finally:
        if session_id:
            await websocket_manager.disconnect(session_id)

# Voice interaction endpoints
@app.post("/api/voice/transcribe")
async def transcribe_audio(
    audio_file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    """Transcribe audio to text"""
    
    if not app.state.voice_handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice service unavailable"
        )
    
    # Read audio data
    audio_data = await audio_file.read()
    
    # Process voice
    result = await app.state.voice_handler.process_voice_query(
        audio_data,
        audio_format=audio_file.filename.split('.')[-1],
        session_id=str(current_user.id)
    )
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Transcription failed')
        )
    
    return result

@app.post("/api/voice/synthesize")
async def synthesize_speech(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Convert text to speech"""
    
    if not app.state.voice_handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice service unavailable"
        )
    
    result = await app.state.voice_handler.generate_audio_response(
        text=request.get('text', ''),
        emotion=request.get('emotion', 'default'),
        format=request.get('format', 'mp3')
    )
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Synthesis failed')
        )
    
    return result

# Collaboration endpoints
@app.post("/api/collaboration/create")
async def create_collaboration(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new collaborative research session"""
    
    collab_id = await app.state.collab_manager.create_collaboration(
        owner_id=str(current_user.id),
        title=request.get('title', 'Untitled Research'),
        description=request.get('description', ''),
        settings=request.get('settings')
    )
    
    return {
        "collaboration_id": collab_id,
        "status": "created"
    }

@app.post("/api/collaboration/{collab_id}/join")
async def join_collaboration(
    collab_id: str,
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Join an existing collaboration"""
    
    result = await app.state.collab_manager.join_collaboration(
        collab_id,
        str(current_user.id),
        request.get('invite_code')
    )
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Failed to join collaboration')
        )
    
    return result

# Export endpoints
@app.post("/api/export")
async def export_research(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Export research results in various formats"""
    
    # Check user tier for export format access
    allowed_formats = {
        'free': ['txt', 'json'],
        'basic': ['txt', 'json', 'pdf'],
        'pro': ['txt', 'json', 'pdf', 'docx', 'notion'],
        'enterprise': ['txt', 'json', 'pdf', 'docx', 'notion', 'custom']
    }
    
    user_formats = allowed_formats.get(current_user.subscription_tier, allowed_formats['free'])
    requested_format = request.get('format', 'pdf')
    
    if requested_format not in user_formats:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Export format '{requested_format}' not available for your tier"
        )
    
    # Get research data
    task_id = request.get('task_id')
    if not task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task ID required"
        )
    
    # Retrieve research data from state
    research_data = await state_manager.get_session_state(f"task:{task_id}")
    if not research_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found"
        )
    
    # Export
    result = await app.state.exporter.export_research(
        research_data.get('results', {}),
        requested_format,
        request.get('template', 'academic'),
        request.get('options', {})
    )
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Export failed')
        )
    
    return result

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized responses"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.get(
            exc.detail if isinstance(exc.detail, str) else "server_error",
            request_id
        )
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse.get("server_error", request_id)
    )

# Admin endpoints (protected)
from .dependencies.auth import check_admin_role

@app.get("/api/admin/metrics")
async def get_system_metrics(
    current_user: User = Depends(check_admin_role)
):
    """Get system metrics (admin only)"""
    
    metrics = {
        "active_connections": len(websocket_manager.local_connections) if websocket_manager else 0,
        "total_users": 0,  # Would query from database
        "active_research_tasks": 0,  # Would query from state manager
        "agent_health": None
    }
    
    # Get agent health
    if websocket_manager and hasattr(websocket_manager, 'adk'):
        try:
            metrics["agent_health"] = await websocket_manager.adk.get_agent_health()
        except Exception:
            pass
    
    # Get recent metrics from state manager
    if state_manager:
        metrics["requests_today"] = await state_manager.get_metrics("research_completed", 1)
    
    return metrics

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv('ENVIRONMENT') != 'production',
        log_level="info",
        access_log=True
    )