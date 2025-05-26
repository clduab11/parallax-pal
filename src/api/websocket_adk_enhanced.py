"""
Enhanced WebSocket integration with native ADK support

This module provides improved WebSocket integration with proper ADK agents,
distributed state management, and enhanced security.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketState

# Security and validation
from .security.validation import (
    WebSocketMessageValidator, 
    ErrorResponse,
    validate_user_id,
    validate_session_id
)

# Authentication
from .dependencies.auth import get_current_user
from .models import User
from .database import get_db
from sqlalchemy.orm import Session

# ADK Integration
from .adk_integration import ParallaxPalADK

# State management
from .state.distributed_state import DistributedStateManager

# Rate limiting
from .middleware.rate_limiter import WebSocketRateLimiter, RateLimiter

# Monitoring
from .monitoring import structured_logger

logger = logging.getLogger(__name__)


class EnhancedADKWebSocketManager:
    """
    Enhanced WebSocket manager with native ADK integration
    
    Features:
    - Native ADK agent integration
    - Distributed state management
    - Enhanced security and rate limiting
    - Real-time progress tracking
    - Multi-instance coordination
    """
    
    def __init__(self):
        """Initialize enhanced WebSocket manager"""
        
        # ADK Integration
        self.adk = ParallaxPalADK()
        
        # State Management
        self.state_manager = DistributedStateManager()
        
        # Rate Limiting
        rate_limiter = RateLimiter()
        self.ws_rate_limiter = WebSocketRateLimiter(rate_limiter)
        
        # Connection tracking (local for this instance)
        self.local_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Background task management
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        logger.info("Enhanced ADK WebSocket manager initialized")
    
    async def initialize(self):
        """Initialize manager and start background tasks"""
        
        # Start event subscription for multi-instance coordination
        task = asyncio.create_task(self._handle_distributed_events())
        self.background_tasks.add(task)
        
        # Start health monitoring
        task = asyncio.create_task(self._monitor_agent_health())
        self.background_tasks.add(task)
        
        logger.info("WebSocket manager background tasks started")
    
    async def shutdown(self):
        """Gracefully shutdown the manager"""
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Close state manager connections
        await self.state_manager.close()
        
        logger.info("WebSocket manager shutdown complete")
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: str,
        user_tier: str = "free"
    ) -> Optional[str]:
        """
        Connect a new WebSocket client with rate limiting
        
        Args:
            websocket: The WebSocket connection
            user_id: ID of the authenticated user
            user_tier: User subscription tier
            
        Returns:
            Session ID if connected, None if rate limited
        """
        # Validate user ID
        if not validate_user_id(user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        # Check rate limits
        allowed, reason = await self.ws_rate_limiter.check_websocket_limit(
            user_id,
            max_connections=self._get_connection_limit(user_tier)
        )
        
        if not allowed:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=reason
            )
            return None
        
        # Accept connection
        await websocket.accept()
        
        async with self.lock:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Add to local connections
            if user_id not in self.local_connections:
                self.local_connections[user_id] = {}
            
            self.local_connections[user_id][session_id] = websocket
            
            # Store metadata
            self.connection_metadata[session_id] = {
                'user_id': user_id,
                'user_tier': user_tier,
                'connected_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            
            # Register in distributed state
            await self.state_manager.add_user_session(user_id, session_id)
            await self.ws_rate_limiter.register_connection(user_id, session_id)
            
            # Log connection
            structured_logger.log(
                "info",
                "WebSocket connected",
                user_id=user_id,
                session_id=session_id
            )
            
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "features": self._get_tier_features(user_tier)
            })
            
            return session_id
    
    async def disconnect(self, session_id: str):
        """Disconnect a WebSocket client"""
        
        async with self.lock:
            # Get metadata
            metadata = self.connection_metadata.get(session_id)
            if not metadata:
                return
            
            user_id = metadata['user_id']
            
            # Remove from local connections
            if user_id in self.local_connections:
                self.local_connections[user_id].pop(session_id, None)
                
                if not self.local_connections[user_id]:
                    del self.local_connections[user_id]
            
            # Remove metadata
            del self.connection_metadata[session_id]
            
            # Update distributed state
            await self.state_manager.remove_user_session(user_id, session_id)
            await self.ws_rate_limiter.unregister_connection(user_id, session_id)
            
            # Clean up any active research tasks
            await self._cleanup_session_tasks(session_id)
            
            structured_logger.log(
                "info",
                "WebSocket disconnected",
                user_id=user_id,
                session_id=session_id
            )
    
    async def handle_message(
        self,
        websocket: WebSocket,
        session_id: str,
        message: dict
    ):
        """
        Handle incoming WebSocket message with validation
        
        Args:
            websocket: The WebSocket connection
            session_id: Session identifier
            message: Incoming message
        """
        try:
            # Validate message
            validated_msg = WebSocketMessageValidator(**message)
            
            # Update last activity
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]['last_activity'] = datetime.now().isoformat()
            
            # Route to appropriate handler
            handlers = {
                'research_query': self._handle_research_query,
                'follow_up_question': self._handle_follow_up,
                'cancel_research': self._handle_cancel_research,
                'get_status': self._handle_get_status,
                'export_results': self._handle_export,
                'share_research': self._handle_share,
                'ping': self._handle_ping
            }
            
            handler = handlers.get(validated_msg.type)
            if handler:
                await handler(websocket, session_id, validated_msg.data)
            else:
                await self._send_error(
                    websocket,
                    "invalid_input",
                    session_id
                )
                
        except ValueError as e:
            await self._send_error(
                websocket,
                "invalid_input",
                session_id
            )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(
                websocket,
                "server_error",
                session_id
            )
    
    async def _handle_research_query(
        self,
        websocket: WebSocket,
        session_id: str,
        data: dict
    ):
        """Handle research query request"""
        
        metadata = self.connection_metadata.get(session_id, {})
        user_id = metadata.get('user_id')
        user_tier = metadata.get('user_tier', 'free')
        
        # Check operation rate limit
        from .middleware.rate_limiter import OperationRateLimiter
        op_limiter = OperationRateLimiter(self.ws_rate_limiter.rate_limiter)
        
        allowed, limit_info = await op_limiter.check_operation_limit(
            user_id,
            'research_query',
            user_tier
        )
        
        if not allowed:
            await self._send_error(
                websocket,
                "rate_limited",
                session_id,
                limit_info
            )
            return
        
        # Validate research query
        from .security.validation import ResearchQueryValidator
        
        try:
            validated_query = ResearchQueryValidator(**data)
        except ValueError as e:
            await self._send_error(
                websocket,
                "invalid_input",
                session_id
            )
            return
        
        # Create research task
        task_id = await self.state_manager.create_research_task(
            user_id,
            validated_query.query,
            validated_query.mode
        )
        
        # Start research in background
        task = asyncio.create_task(
            self._process_research(
                websocket,
                session_id,
                task_id,
                validated_query
            )
        )
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "research_started",
            "task_id": task_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _process_research(
        self,
        websocket: WebSocket,
        session_id: str,
        task_id: str,
        query: 'ResearchQueryValidator'
    ):
        """Process research query with ADK agents"""
        
        try:
            # Update task status
            await self.state_manager.update_task_progress(
                task_id, 0, status="started"
            )
            
            # Stream research results
            async for event in self.adk.stream_research(
                query.query,
                self.connection_metadata[session_id]['user_id'],
                session_id,
                query.mode
            ):
                # Update task progress
                await self.state_manager.update_task_progress(
                    task_id,
                    event['progress'],
                    agent=event.get('agent'),
                    status=event.get('type'),
                    partial_results=event.get('content') if event['type'] == 'result' else None
                )
                
                # Send to WebSocket
                await websocket.send_json({
                    "type": "research_update",
                    "task_id": task_id,
                    "session_id": session_id,
                    **event
                })
                
                # Check if research is complete
                if event.get('type') == 'complete':
                    await self._finalize_research(
                        websocket,
                        session_id,
                        task_id,
                        event.get('content', {})
                    )
                    
        except Exception as e:
            logger.error(f"Research processing error: {e}")
            
            # Update task status
            await self.state_manager.update_task_progress(
                task_id, 100, status="error"
            )
            
            # Send error to client
            await self._send_error(
                websocket,
                "research_failed",
                session_id
            )
    
    async def _finalize_research(
        self,
        websocket: WebSocket,
        session_id: str,
        task_id: str,
        results: dict
    ):
        """Finalize research and send complete results"""
        
        # Update metrics
        await self.state_manager.increment_metric('research_completed')
        
        # Send completion message
        await websocket.send_json({
            "type": "research_completed",
            "task_id": task_id,
            "session_id": session_id,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_follow_up(
        self,
        websocket: WebSocket,
        session_id: str,
        data: dict
    ):
        """Handle follow-up question"""
        
        # Get previous context from state
        task_id = data.get('task_id')
        if not task_id:
            await self._send_error(
                websocket,
                "invalid_input",
                session_id
            )
            return
        
        # Retrieve task context
        # (Implementation continues with context-aware follow-up)
        pass
    
    async def _handle_cancel_research(
        self,
        websocket: WebSocket,
        session_id: str,
        data: dict
    ):
        """Cancel ongoing research"""
        
        task_id = data.get('task_id')
        if not task_id:
            return
        
        # Update task status
        await self.state_manager.update_task_progress(
            task_id, 100, status="cancelled"
        )
        
        # Send confirmation
        await websocket.send_json({
            "type": "research_cancelled",
            "task_id": task_id,
            "session_id": session_id
        })
    
    async def _handle_ping(
        self,
        websocket: WebSocket,
        session_id: str,
        data: dict
    ):
        """Handle ping message"""
        
        await websocket.send_json({
            "type": "pong",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _send_error(
        self,
        websocket: WebSocket,
        error_type: str,
        session_id: str,
        additional_info: Optional[dict] = None
    ):
        """Send standardized error message"""
        
        error_response = ErrorResponse.get(error_type, session_id)
        
        if additional_info:
            error_response.update(additional_info)
        
        await websocket.send_json({
            "type": "error",
            "session_id": session_id,
            **error_response
        })
    
    def _get_connection_limit(self, tier: str) -> int:
        """Get connection limit based on tier"""
        limits = {
            'free': 2,
            'basic': 5,
            'pro': 10,
            'enterprise': 50
        }
        return limits.get(tier, 2)
    
    def _get_tier_features(self, tier: str) -> dict:
        """Get features available for tier"""
        features = {
            'free': {
                'max_queries_hour': 10,
                'export_formats': ['txt', 'json'],
                'knowledge_graph': True,
                'voice_input': False
            },
            'basic': {
                'max_queries_hour': 50,
                'export_formats': ['txt', 'json', 'pdf'],
                'knowledge_graph': True,
                'voice_input': False
            },
            'pro': {
                'max_queries_hour': 200,
                'export_formats': ['txt', 'json', 'pdf', 'docx', 'notion'],
                'knowledge_graph': True,
                'voice_input': True
            },
            'enterprise': {
                'max_queries_hour': 1000,
                'export_formats': ['txt', 'json', 'pdf', 'docx', 'notion', 'custom'],
                'knowledge_graph': True,
                'voice_input': True
            }
        }
        return features.get(tier, features['free'])
    
    async def _cleanup_session_tasks(self, session_id: str):
        """Clean up any active tasks for a session"""
        
        # Cancel any running research tasks
        # (Implementation depends on task tracking)
        pass
    
    async def _handle_distributed_events(self):
        """Handle events from other instances"""
        
        channels = ['research_updates', 'system_events']
        
        try:
            async with self.state_manager.subscribe_to_events(channels) as events:
                async for event in events:
                    await self._process_distributed_event(event)
        except Exception as e:
            logger.error(f"Error in distributed event handler: {e}")
    
    async def _process_distributed_event(self, event: dict):
        """Process event from another instance"""
        
        # Handle different event types
        # (Implementation depends on event types)
        pass
    
    async def _monitor_agent_health(self):
        """Monitor ADK agent health"""
        
        while True:
            try:
                health = await self.adk.get_agent_health()
                
                # Broadcast health status if degraded
                if health['overall_status'] != 'healthy':
                    await self.state_manager.publish_event(
                        'system_events',
                        {
                            'type': 'agent_health',
                            'status': health
                        }
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Back off on error