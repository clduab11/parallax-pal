"""
WebSocket integration for ADK in Parallax Pal

This module provides WebSocket integration with the ADK-based agent system,
enabling real-time updates and bidirectional communication with Starri.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketState

# Import authentication dependencies
from .dependencies.auth import get_current_user
from .models import User
from .database import get_db
from sqlalchemy.orm import Session
import requests

# Set up logging
logger = logging.getLogger(__name__)

class ADKWebSocketManager:
    """
    WebSocket manager for ADK integration
    
    This class manages WebSocket connections, handles client message routing,
    and provides real-time updates from the ADK agent system.
    """
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.session_users: Dict[str, str] = {}  # session_id -> user_id
        self.research_sessions: Dict[str, Dict] = {}
        self.lock = asyncio.Lock()
        
        # ADK communication settings
        self.orchestrator = None
        self.adk_initialized = False
        
        # Progress tracking for real-time updates
        self.progress_handlers: Dict[str, asyncio.Task] = {}
    
    async def initialize(self):
        """
        Initialize ADK communication with the orchestrator agent.
        """
        try:
            # Import and initialize the orchestrator agent
            from agents.orchestrator.orchestrator_agent import OrchestratorAgent
            
            if not self.orchestrator:
                self.orchestrator = OrchestratorAgent()
                
            self.adk_initialized = True
            logger.info("ADK WebSocket manager initialized with local orchestrator agent")
            
        except Exception as e:
            logger.error(f"Error initializing ADK orchestrator: {e}")
            self.adk_initialized = False
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Connect a new WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            user_id: ID of the authenticated user
        """
        await websocket.accept()
        
        async with self.lock:
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            
            # Add to active connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = {}
            
            self.active_connections[user_id][session_id] = websocket
            
            # Update session mapping
            self.user_sessions[user_id] = session_id
            self.session_users[session_id] = user_id
            
            logger.info(f"New connection established for user {user_id}, session {session_id}")
            
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
    
    async def disconnect(self, websocket: WebSocket, user_id: str, session_id: Optional[str] = None):
        """
        Disconnect a WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            user_id: ID of the authenticated user
            session_id: Optional session ID for specific disconnect
        """
        async with self.lock:
            if user_id in self.active_connections:
                if session_id and session_id in self.active_connections[user_id]:
                    # Remove specific session
                    del self.active_connections[user_id][session_id]
                    if session_id in self.session_users:
                        del self.session_users[session_id]
                    logger.info(f"Disconnected session {session_id} for user {user_id}")
                else:
                    # Find and remove session by websocket reference
                    for sess_id, ws in list(self.active_connections[user_id].items()):
                        if ws == websocket:
                            del self.active_connections[user_id][sess_id]
                            if sess_id in self.session_users:
                                del self.session_users[sess_id]
                            logger.info(f"Disconnected session {sess_id} for user {user_id}")
                            break
                
                # Clean up empty user entry
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    if user_id in self.user_sessions:
                        del self.user_sessions[user_id]
                    logger.info(f"Removed empty connection entry for user {user_id}")
    
    async def broadcast_to_user(self, user_id: str, message: Dict):
        """
        Broadcast a message to all sessions of a specific user.
        
        Args:
            user_id: ID of the user to broadcast to
            message: The message to broadcast
        """
        if user_id not in self.active_connections:
            logger.warning(f"Attempted to broadcast to user {user_id} with no active connections")
            return
        
        disconnected = []
        
        for session_id, websocket in self.active_connections[user_id].items():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    disconnected.append(session_id)
            except RuntimeError as e:
                logger.error(f"Error broadcasting to session {session_id}: {str(e)}")
                disconnected.append(session_id)
        
        # Clean up disconnected sessions
        if disconnected:
            async with self.lock:
                for session_id in disconnected:
                    if session_id in self.active_connections[user_id]:
                        del self.active_connections[user_id][session_id]
                        if session_id in self.session_users:
                            del self.session_users[session_id]
                
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    if user_id in self.user_sessions:
                        del self.user_sessions[user_id]
    
    async def send_to_session(self, session_id: str, message: Dict):
        """
        Send a message to a specific session.
        
        Args:
            session_id: ID of the session to send to
            message: The message to send
        """
        if session_id not in self.session_users:
            logger.warning(f"Attempted to send to unknown session {session_id}")
            return
        
        user_id = self.session_users[session_id]
        
        if user_id not in self.active_connections or session_id not in self.active_connections[user_id]:
            logger.warning(f"Session {session_id} for user {user_id} not found in active connections")
            return
        
        websocket = self.active_connections[user_id][session_id]
        
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
            else:
                logger.warning(f"WebSocket for session {session_id} is not connected")
                await self.disconnect(websocket, user_id, session_id)
        except RuntimeError as e:
            logger.error(f"Error sending to session {session_id}: {str(e)}")
            await self.disconnect(websocket, user_id, session_id)
    
    async def handle_client_message(self, user_id: str, session_id: str, message: Dict):
        """
        Handle a message from a WebSocket client.
        
        Args:
            user_id: ID of the user who sent the message
            session_id: ID of the session that sent the message
            message: The message from the client
        """
        message_type = message.get("type", "")
        
        logger.info(f"Received message of type '{message_type}' from user {user_id}, session {session_id}")
        
        if message_type == "ping":
            # Handle ping message
            await self.send_to_session(session_id, {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
        
        elif message_type == "start_research":
            # Handle research request
            await self.handle_research_request(user_id, session_id, message)
        
        elif message_type == "cancel_research":
            # Handle research cancellation
            await self.handle_research_cancellation(user_id, session_id, message)
        
        else:
            # Unknown message type
            logger.warning(f"Unknown message type: {message_type}")
            await self.send_to_session(session_id, {
                "type": "error",
                "error": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def handle_research_request(self, user_id: str, session_id: str, message: Dict):
        """
        Handle a research request from a client.
        
        Args:
            user_id: ID of the user who sent the request
            session_id: ID of the session that sent the request
            message: The research request message
        """
        if not self.adk_initialized:
            await self.send_to_session(session_id, {
                "type": "error",
                "error": "ADK system not initialized",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        query = message.get("query", "")
        continuous_mode = message.get("continuous_mode", False)
        force_refresh = message.get("force_refresh", False)
        
        if not query:
            await self.send_to_session(session_id, {
                "type": "error",
                "error": "No query provided",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Store research session information
        self.research_sessions[request_id] = {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "continuous_mode": continuous_mode,
            "force_refresh": force_refresh,
            "start_time": datetime.now().isoformat(),
            "status": "starting"
        }
        
        # Send acknowledgment to client
        await self.send_to_session(session_id, {
            "type": "research_started",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Forward request to ADK orchestrator  
        try:
            # Ensure orchestrator is initialized
            if not self.orchestrator:
                await self.initialize()
            
            if not self.orchestrator:
                raise Exception("Failed to initialize orchestrator agent")
            
            # Create research request object
            from agents.orchestrator.orchestrator_agent import ResearchRequest
            
            research_request = ResearchRequest(
                query=query,
                continuous_mode=continuous_mode,
                force_refresh=force_refresh,
                max_sources=message.get("max_sources", 20),
                depth_level=message.get("depth_level", "detailed"),
                focus_areas=message.get("focus_areas", []),
                request_id=request_id
            )
            
            # Start research using the real orchestrator
            asyncio.create_task(self.process_research_with_orchestrator(request_id, research_request, user_id))
            
        except Exception as e:
            logger.error(f"Error forwarding research request to ADK: {str(e)}")
            await self.send_to_session(session_id, {
                "type": "research_error",
                "request_id": request_id,
                "error": f"Error starting research: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def process_research_with_orchestrator(self, request_id: str, research_request, user_id: str):
        """
        Process a research request using the real orchestrator agent.
        
        Args:
            request_id: ID of the research request
            research_request: The research request object
            user_id: ID of the user making the request
        """
        try:
            # Update research session status
            if request_id in self.research_sessions:
                self.research_sessions[request_id]["status"] = "processing"
            
            # Start research with the orchestrator
            result = await self.orchestrator.handle_research_request(
                research_request, request_id, user_id
            )
            
            # Start progress monitoring task
            progress_task = asyncio.create_task(
                self.monitor_research_progress(request_id, user_id)
            )
            self.progress_handlers[request_id] = progress_task
            
            logger.info(f"Started research request {request_id} with orchestrator")
            
        except Exception as e:
            logger.error(f"Error processing research with orchestrator: {e}")
            
            # Send error to client
            session_id = self.research_sessions.get(request_id, {}).get("session_id")
            if session_id:
                await self.send_to_session(session_id, {
                    "type": "research_error",
                    "request_id": request_id,
                    "error": f"Error processing research: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
    
    async def monitor_research_progress(self, request_id: str, user_id: str):
        """
        Monitor research progress and send real-time updates to the client.
        
        Args:
            request_id: ID of the research request
            user_id: ID of the user making the request
        """
        try:
            last_status = None
            last_progress = 0
            update_count = 0
            
            while request_id in self.research_sessions:
                try:
                    # Get current status from orchestrator
                    status_info = await self.orchestrator.get_research_status(request_id, user_id)
                    
                    if not status_info:
                        logger.warning(f"No status info for request {request_id}")
                        break
                    
                    current_status = status_info.get("status", "unknown")
                    current_progress = status_info.get("progress", 0)
                    
                    # Send update if status or progress changed significantly
                    progress_changed = abs(current_progress - last_progress) >= 5  # 5% threshold
                    status_changed = current_status != last_status
                    
                    if status_changed or progress_changed or update_count % 10 == 0:  # Force update every 10 cycles
                        session_id = self.research_sessions.get(request_id, {}).get("session_id")
                        if session_id:
                            await self.send_to_session(session_id, {
                                "type": "research_progress",
                                "request_id": request_id,
                                "status": current_status,
                                "progress": current_progress,
                                "agent_activities": status_info.get("agent_activities", []),
                                "timestamp": datetime.now().isoformat()
                            })
                        
                        last_status = current_status
                        last_progress = current_progress
                    
                    # Check if research is complete
                    if current_status in ["completed", "failed", "cancelled"]:
                        await self.handle_research_completion(request_id, user_id, current_status)
                        break
                    
                    update_count += 1
                    await asyncio.sleep(2)  # Check every 2 seconds
                    
                except Exception as e:
                    logger.error(f"Error monitoring progress for {request_id}: {e}")
                    await asyncio.sleep(5)  # Wait longer on error
            
        except Exception as e:
            logger.error(f"Error in progress monitor for {request_id}: {e}")
        finally:
            # Clean up progress handler
            if request_id in self.progress_handlers:
                del self.progress_handlers[request_id]
    
    async def handle_research_completion(self, request_id: str, user_id: str, status: str):
        """
        Handle completion of a research request.
        
        Args:
            request_id: ID of the research request
            user_id: ID of the user making the request
            status: Final status of the research
        """
        try:
            session_id = self.research_sessions.get(request_id, {}).get("session_id")
            if not session_id:
                return
            
            if status == "completed":
                # Get final results
                results = await self.orchestrator.get_research_results(request_id, user_id)
                
                # Generate knowledge graph
                knowledge_graph = await self.orchestrator.generate_knowledge_graph(request_id, user_id)
                
                # Get follow-up questions
                follow_up_questions = await self.orchestrator.get_follow_up_questions(request_id, user_id)
                
                # Send completion message with all results
                await self.send_to_session(session_id, {
                    "type": "research_completed",
                    "request_id": request_id,
                    "results": results,
                    "knowledge_graph": knowledge_graph,
                    "follow_up_questions": follow_up_questions,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif status == "failed":
                await self.send_to_session(session_id, {
                    "type": "research_error",
                    "request_id": request_id,
                    "error": "Research request failed",
                    "timestamp": datetime.now().isoformat()
                })
                
            elif status == "cancelled":
                await self.send_to_session(session_id, {
                    "type": "research_cancelled",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Clean up research session
            if request_id in self.research_sessions:
                self.research_sessions[request_id]["status"] = status
                self.research_sessions[request_id]["end_time"] = datetime.now().isoformat()
                
        except Exception as e:
            logger.error(f"Error handling research completion for {request_id}: {e}")
    
    
    async def handle_research_cancellation(self, user_id: str, session_id: str, message: Dict):
        """
        Handle a research cancellation request from a client.
        
        Args:
            user_id: ID of the user who sent the request
            session_id: ID of the session that sent the request
            message: The cancellation request message
        """
        request_id = message.get("request_id", "")
        
        if not request_id:
            await self.send_to_session(session_id, {
                "type": "error",
                "error": "No request_id provided for cancellation",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Check if the research session exists and belongs to this user
        if request_id not in self.research_sessions:
            await self.send_to_session(session_id, {
                "type": "error",
                "error": f"Research session {request_id} not found",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        if self.research_sessions[request_id]["user_id"] != user_id:
            await self.send_to_session(session_id, {
                "type": "error",
                "error": f"Research session {request_id} does not belong to this user",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Send cancellation request to orchestrator
        try:
            if not self.orchestrator:
                await self.initialize()
                
            if not self.orchestrator:
                raise Exception("Orchestrator not available")
            
            # Cancel the research using the real orchestrator
            result = await self.orchestrator.cancel_research(request_id, user_id)
            
            if result:
                # Cancel was successful
                await self.send_to_session(session_id, {
                    "type": "research_cancelled",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Clean up progress handler
                if request_id in self.progress_handlers:
                    self.progress_handlers[request_id].cancel()
                    del self.progress_handlers[request_id]
                
                # Update research session
                self.research_sessions[request_id]["status"] = "cancelled"
                self.research_sessions[request_id]["end_time"] = datetime.now().isoformat()
                
            else:
                # Cancel failed
                await self.send_to_session(session_id, {
                    "type": "error", 
                    "error": f"Failed to cancel research {request_id}",
                    "timestamp": datetime.now().isoformat()
                })
                    
        except Exception as e:
            logger.error(f"Error cancelling research {request_id}: {e}")
            await self.send_to_session(session_id, {
                "type": "error",
                "error": f"Error cancelling research: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def cleanup_research_session(self, request_id: str, delay: int = 0):
        """
        Clean up a research session after a delay.
        
        Args:
            request_id: ID of the research session to clean up
            delay: Delay in seconds before cleanup
        """
        if delay > 0:
            await asyncio.sleep(delay)
        
        if request_id in self.research_sessions:
            del self.research_sessions[request_id]
            logger.info(f"Cleaned up research session {request_id}")

# Create singleton instance
adk_websocket_manager = ADKWebSocketManager()

async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    WebSocket endpoint for ADK integration.
    
    Args:
        websocket: The WebSocket connection
        db: Database session
        current_user: The authenticated user
    """
    if not current_user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    user_id = str(current_user.id)
    
    # Accept the connection and add to manager
    await adk_websocket_manager.connect(websocket, user_id)
    
    try:
        # Listen for messages
        while True:
            message = await websocket.receive_json()
            
            # Extract session ID from message
            session_id = message.get("session_id", "")
            
            if not session_id:
                # If no session ID, check if user has a session
                if user_id in adk_websocket_manager.user_sessions:
                    session_id = adk_websocket_manager.user_sessions[user_id]
                else:
                    # Create error response
                    await websocket.send_json({
                        "type": "error",
                        "error": "No session ID provided",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
            
            # Process the message
            await adk_websocket_manager.handle_client_message(user_id, session_id, message)
    
    except WebSocketDisconnect:
        # Handle disconnection
        await adk_websocket_manager.disconnect(websocket, user_id)
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        # Try to disconnect cleanly
        try:
            await adk_websocket_manager.disconnect(websocket, user_id)
        except:
            pass