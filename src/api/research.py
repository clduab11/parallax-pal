from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
import logging

from . import models
from .cache import cache
from .research_core import research_core
from .monitoring import structured_logger
from .database import get_db
from .config import settings

logger = logging.getLogger(__name__)

class ResearchService:
    """Service layer for research operations with multi-model AI analysis"""

    async def process_research_task(
        self,
        db: Session,
        task_id: int,
        query: str,
        use_ollama: bool = False,
        continuous_mode: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Process a research task asynchronously using multiple AI models
        
        Args:
            db: Database session
            task_id: ID of the research task
            query: Research query
            use_ollama: Whether to include Ollama model in analysis
            continuous_mode: Whether to use continuous research mode
        """
        task = db.query(models.ResearchTask).filter(models.ResearchTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return None
            
        try:
            # Update task status
            task.status = models.ResearchStatus.IN_PROGRESS
            db.commit()
            
            start_time = datetime.now()
            
            # Process research through core engine with multiple models
            research_results = await research_core.process_research_query(
                query=query,
                use_ollama=use_ollama,
                continuous_mode=continuous_mode,
                max_iterations=settings.MAX_RETRIES if continuous_mode else 1
            )
            
            # Validate sources
            valid_sources = await research_core.validate_sources([
                result['url'] for result in research_results['web_results']
            ])
            
            # Filter web results to valid sources
            valid_web_results = [
                result for result in research_results['web_results']
                if result['url'] in valid_sources
            ]
            
            # Update task with results
            task.status = models.ResearchStatus.COMPLETED
            task.result = research_results['synthesis']
            task.web_results = valid_web_results
            task.ai_analyses = research_results['ai_analyses']
            task.models_used = research_results['models_used']
            
            # Calculate metrics
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            # Create analytics entry
            analytics = models.ResearchAnalytics(
                task_id=task.id,
                processing_time=processing_time,
                token_count=len(research_results['synthesis'].split()),
                source_count=len(valid_sources),
                model_count=len(research_results['models_used'])
            )
            db.add(analytics)
            
            # Cache results
            if settings.ENABLE_CACHING:
                cache_key = f"research_task_{task_id}"
                cache.set(cache_key, {
                    'task_id': task.id,
                    'status': task.status,
                    'result': task.result,
                    'web_results': task.web_results,
                    'ai_analyses': task.ai_analyses,
                    'models_used': task.models_used,
                    'analytics': {
                        'processing_time_ms': processing_time,
                        'source_count': len(valid_sources),
                        'model_count': len(research_results['models_used'])
                    }
                }, timeout=3600)  # Cache for 1 hour
            
            db.commit()
            
            structured_logger.log("info", "Research task completed",
                task_id=task.id,
                processing_time_ms=processing_time,
                source_count=len(valid_sources),
                model_count=len(research_results['models_used'])
            )
            
            return {
                'task_id': task.id,
                'status': task.status,
                'result': task.result,
                'web_results': task.web_results,
                'ai_analyses': task.ai_analyses,
                'models_used': task.models_used,
                'analytics': {
                    'processing_time_ms': processing_time,
                    'source_count': len(valid_sources),
                    'model_count': len(research_results['models_used']),
                    'token_count': analytics.token_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            task.status = models.ResearchStatus.FAILED
            task.error_message = str(e)
            db.commit()
            
            structured_logger.log("error", "Research task failed",
                task_id=task.id,
                error=str(e)
            )
            
            return None
            
    async def get_task_status(
        self,
        db: Session,
        task_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get the current status of a research task"""
        
        # Try to get from cache first
        if settings.ENABLE_CACHING:
            cache_key = f"research_task_{task_id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                structured_logger.log("debug", "Cache hit for task status",
                    task_id=task_id
                )
                return cached_result
        
        task = db.query(models.ResearchTask).filter(models.ResearchTask.id == task_id).first()
        if not task:
            return None
            
        response = {
            'task_id': task.id,
            'status': task.status,
            'created_at': task.created_at,
            'updated_at': task.updated_at
        }
        
        if task.status == models.ResearchStatus.COMPLETED:
            response.update({
                'result': task.result,
                'web_results': task.web_results,
                'ai_analyses': task.ai_analyses,
                'models_used': task.models_used
            })
            if task.analytics:
                response['analytics'] = {
                    'processing_time_ms': task.analytics.processing_time,
                    'token_count': task.analytics.token_count,
                    'source_count': task.analytics.source_count,
                    'model_count': task.analytics.model_count
                }
        elif task.status == models.ResearchStatus.FAILED:
            response['error'] = task.error_message
            
        return response
    
    async def list_user_tasks(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[models.ResearchTask]:
        """List research tasks for a user"""
        return (
            db.query(models.ResearchTask)
            .filter(models.ResearchTask.owner_id == user_id)
            .order_by(models.ResearchTask.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

research_service = ResearchService()