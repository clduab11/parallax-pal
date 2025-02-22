from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import models, auth
from .database import get_db, init_db
from .research import research_service
from .cache import cache, cache_response
from .monitoring import setup_monitoring, monitor_endpoint, StructuredLogger

# Initialize FastAPI app with enhanced metadata
app = FastAPI(
    title="Parallax Pal API",
    description="""
    Parallax Pal API - Research and Analytics Integration Platform
    
    Features:
    * Secure authentication with JWT
    * Research task management
    * Real-time progress tracking
    * Analytics integration
    * Admin dashboard
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Set up monitoring and logging
logger = setup_monitoring(app)
structured_logger = StructuredLogger("parallax-pal-api")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Events
@app.on_event("startup")
async def startup_event():
    """Initialize database and monitoring on startup"""
    init_db()
    structured_logger.log("info", "Application started successfully")

# Authentication Endpoints
@app.post("/token", 
    response_model=Dict[str, str],
    tags=["authentication"],
    summary="Obtain JWT access token",
    description="Authenticate user credentials and return JWT token for API access")
@monitor_endpoint("login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = await auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        structured_logger.log("warning", "Failed login attempt", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    structured_logger.log("info", "Successful login", username=user.username)
    return {"access_token": access_token, "token_type": "bearer"}

# Research Endpoints
@app.post("/api/research/tasks",
    response_model=Dict[str, Any],
    tags=["research"],
    summary="Create new research task",
    description="Submit a new research query for processing")
@monitor_endpoint("create_research_task")
async def create_research_task(
    query: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = models.ResearchTask(
        query=query,
        owner_id=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Process task asynchronously
    background_tasks.add_task(
        research_service.process_research_task,
        db,
        task.id,
        query
    )
    
    structured_logger.log("info", "Research task created",
        task_id=task.id,
        user_id=current_user.id
    )
    
    return {"task_id": task.id, "status": task.status}

@app.get("/api/research/tasks/{task_id}",
    response_model=Dict[str, Any],
    tags=["research"],
    summary="Get research task details",
    description="Retrieve status and results of a specific research task")
@monitor_endpoint("get_research_task")
@cache_response(timeout=300)  # Cache for 5 minutes
async def get_research_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = await research_service.get_task_status(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check task ownership
    db_task = db.query(models.ResearchTask).filter(models.ResearchTask.id == task_id).first()
    if db_task.owner_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        structured_logger.log("warning", "Unauthorized task access attempt",
            task_id=task_id,
            user_id=current_user.id
        )
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
        
    return task

@app.get("/api/research/tasks",
    response_model=List[Dict[str, Any]],
    tags=["research"],
    summary="List research tasks",
    description="Get paginated list of research tasks for current user")
@monitor_endpoint("list_research_tasks")
@cache_response(timeout=60)  # Cache for 1 minute
async def list_research_tasks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    tasks = db.query(models.ResearchTask)\
        .filter(models.ResearchTask.owner_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return tasks

# Admin Endpoints
@app.get("/api/admin/tasks",
    response_model=List[Dict[str, Any]],
    tags=["admin"],
    summary="Admin: List all tasks",
    description="Get paginated list of all research tasks (admin only)")
@monitor_endpoint("admin_list_tasks")
@cache_response(timeout=60)
async def admin_list_all_tasks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_admin_role)
):
    tasks = db.query(models.ResearchTask)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return tasks

# Health Check Endpoints
@app.get("/",
    tags=["health"],
    summary="Basic health check",
    description="Simple health check endpoint")
@monitor_endpoint("health_check")
async def root():
    return {"status": "online", "service": "Parallax Pal API"}

@app.get("/api/health",
    tags=["health"],
    summary="Detailed health check",
    description="Get detailed health status of the API and its dependencies")
@monitor_endpoint("detailed_health_check")
async def health_check():
    redis_status = "healthy" if cache.client.ping() else "unhealthy"
    db_status = "healthy"
    try:
        db = next(get_db())
        db.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "database": db_status,
            "cache": redis_status
        }
    }

# Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    structured_logger.log("error", "HTTP error",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    structured_logger.log("error", "Unexpected error",
        error_type=type(exc).__name__,
        error_details=str(exc),
        path=request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Custom OpenAPI Schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)