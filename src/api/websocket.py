"""
WebSocket handling for real-time communication with frontend
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Callable, Awaitable
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, auth
from .database import get_db
from .monitoring import structured_logger

# Set up logging
logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    WebSocket connection manager with enhanced error handling and security
    
    Handles WebSocket connections, disconnections, and broadcasting of messages
    to specific clients or groups.
    """
    
    def __init__(self):
        # Active connections
        self.active_connections: Dict[str, WebSocket] = {}
        # Map user_id to connection_id for authenticated sessions
        self.user_connections: Dict[int, Set[str]] = {}
        # Connection event handlers
        self.disconnect_handlers: List[Callable[[str], Awaitable[None]]] = []
        
    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """
        Accept a new WebSocket connection with error handling
        
        Args:
            websocket: The WebSocket connection
            connection_id: Unique ID for this connection
        """
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            logger.info(f"WebSocket connected: {connection_id}")
            structured_logger.log("info", "WebSocket connected", connection_id=connection_id)
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {str(e)}")
            structured_logger.log("error", "WebSocket connection failed", 
                                error_type=type(e).__name__)
            # Close the connection if accept failed
            try:
                await websocket.close(code=1011)  # 1011 = Server error
            except Exception:
                pass  # Ignore errors during cleanup
    
    async def disconnect(self, connection_id: str) -> None:
        """
        Handle WebSocket disconnection with proper cleanup
        
        Args:
            connection_id: The connection ID to disconnect
        """
        if connection_id in self.active_connections:
            # Get websocket reference before removing from active_connections
            websocket = self.active_connections[connection_id]
            
            # Remove from active_connections
            del self.active_connections[connection_id]
            
            # Remove from user_connections if authenticated
            for user_id, connections in list(self.user_connections.items()):
                if connection_id in connections:
                    connections.remove(connection_id)
                    if not connections:
                        del self.user_connections[user_id]
                    break
            
            # Run disconnect handlers
            for handler in self.disconnect_handlers:
                try:
                    await handler(connection_id)
                except Exception as e:
                    logger.error(f"Error in disconnect handler: {str(e)}")
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            structured_logger.log("info", "WebSocket disconnected", connection_id=connection_id)
            
            # Ensure connection is closed
            try:
                await websocket.close()
            except Exception:
                pass  # Ignore errors during cleanup
    
    def register_user_connection(self, user_id: int, connection_id: str) -> None:
        """
        Register connection as authenticated for a specific user
        
        Args:
            user_id: The user ID
            connection_id: The connection ID
        """
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        logger.info(f"User {user_id} registered with connection {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str) -> bool:
        """
        Send a message to a specific connection with error handling
        
        Args:
            message: The message to send
            connection_id: The connection ID to send to
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Attempted to send message to non-existent connection: {connection_id}")
            return False
            
        websocket = self.active_connections[connection_id]
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")
            structured_logger.log("error", "WebSocket send failed",
                               connection_id=connection_id, 
                               error_type=type(e).__name__)
            
            # Handle potential disconnection
            if isinstance(e, (WebSocketDisconnect, ConnectionError)):
                await self.disconnect(connection_id)
            return False
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]) -> int:
        """
        Send a message to all connections for a specific user
        
        Args:
            user_id: The user ID to send to
            message: The message to send
            
        Returns:
            int: Number of connections that received the message successfully
        """
        if user_id not in self.user_connections:
            return 0
            
        sent_count = 0
        for connection_id in self.user_connections[user_id]:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
                
        return sent_count
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all active connections
        
        Args:
            message: The message to broadcast
            
        Returns:
            int: Number of connections that received the message successfully
        """
        sent_count = 0
        for connection_id in list(self.active_connections.keys()):
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
                
        return sent_count
    
    async def broadcast_research_update(self, 
                                     task_id: int,
                                     message: str,
                                     update_type: str = "progress",
                                     web_results: Optional[List[Dict[str, Any]]] = None,
                                     ai_analyses: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Broadcast a research update to all relevant clients
        
        Args:
            task_id: The research task ID
            message: The message content
            update_type: Type of update (progress, result, error)
            web_results: Optional list of web search results
            ai_analyses: Optional list of AI analysis results
        """
        try:
            # Construct the update message
            update = {
                "type": update_type,
                "task_id": task_id,
                "message": message,
                "timestamp": str(datetime.utcnow())
            }
            
            # Add optional data if provided
            if web_results:
                update["webResults"] = web_results
            if ai_analyses:
                update["aiAnalyses"] = ai_analyses
                
            # Get the task owner from the database
            db = next(get_db())
            task = db.query(models.ResearchTask).filter(models.ResearchTask.id == task_id).first()
            
            if task and task.owner_id:
                # Send to the task owner's connections
                sent_count = await self.send_to_user(task.owner_id, {
                    "event": "research_update",
                    "data": update
                })
                
                if sent_count == 0:
                    # Store the update for retrieval later
                    logger.info(f"No active connections for task {task_id}, storing update")
            else:
                # Task not found, broadcast to all (development/admin mode)
                await self.broadcast({
                    "event": "research_update",
                    "data": update
                })
                
        except Exception as e:
            logger.error(f"Error broadcasting research update: {str(e)}")
            structured_logger.log("error", "Research update broadcast failed",
                                 task_id=task_id,
                                 error_type=type(e).__name__)


# Create a global connection manager
manager = ConnectionManager()


async def get_token_from_query(websocket: WebSocket) -> Optional[str]:
    """Extract token from WebSocket query parameters"""
    try:
        token = websocket.query_params.get("token")
        return token
    except Exception:
        return None


async def get_websocket_user(websocket: WebSocket, db: Session = Depends(get_db)) -> Optional[models.User]:
    """
    Authenticate WebSocket connection using JWT token
    
    Args:
        websocket: The WebSocket connection
        db: Database session
        
    Returns:
        Optional[models.User]: Authenticated user or None
    """
    token = await get_token_from_query(websocket)
    if not token:
        return None
        
    try:
        payload = auth.decode_token(token)
        if not payload:
            return None
            
        username = payload.get("sub")
        if not username:
            return None
            
        user = db.query(models.User).filter(
            models.User.username == username,
            models.User.is_active == True
        ).first()
        
        return user
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        return None


async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint with enhanced error handling and authentication
    
    Args:
        websocket: The WebSocket connection
        db: Database session
    """
    connection_id = f"ws_{id(websocket)}_{datetime.utcnow().timestamp()}"
    user = await get_websocket_user(websocket, db)
    
    try:
        # Accept connection
        await manager.connect(websocket, connection_id)
        
        # Register authenticated user
        if user:
            manager.register_user_connection(user.id, connection_id)
            await manager.send_personal_message({
                "event": "auth_status",
                "data": {
                    "authenticated": True,
                    "username": user.username
                }
            }, connection_id)
        else:
            await manager.send_personal_message({
                "event": "auth_status",
                "data": {
                    "authenticated": False
                }
            }, connection_id)
        
        # Main WebSocket message handling loop
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_json()
                
                # Process message based on event type
                event_type = data.get("event")
                event_data = data.get("data", {})
                
                if event_type == "ping":
                    # Handle ping/keepalive
                    await manager.send_personal_message({
                        "event": "pong",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    }, connection_id)
                
                elif event_type == "research_query":
                    # Handle research query (requires authentication)
                    if not user:
                        await manager.send_personal_message({
                            "event": "research_update",
                            "data": {
                                "type": "error",
                                "message": "Authentication required for research queries"
                            }
                        }, connection_id)
                        continue
                    
                    # Extract query data
                    query = event_data.get("query")
                    mode = event_data.get("mode", "web")
                    use_ollama = event_data.get("useOllama", False)
                    
                    # Validate query
                    if not query or not isinstance(query, str) or len(query) > 1000:
                        await manager.send_personal_message({
                            "event": "research_update",
                            "data": {
                                "type": "error",
                                "message": "Invalid query format or too long (max 1000 chars)"
                            }
                        }, connection_id)
                        continue
                    
                    # Create research task
                    task = models.ResearchTask(
                        query=query,
                        owner_id=user.id,
                        continuous_mode=mode == "continuous",
                        used_ollama=use_ollama
                    )
                    db.add(task)
                    db.commit()
                    db.refresh(task)
                    
                    # Send acknowledgment
                    await manager.send_personal_message({
                        "event": "research_update",
                        "data": {
                            "type": "start",
                            "task_id": task.id,
                            "message": f"Research task started: {query}"
                        }
                    }, connection_id)
                    
                    # Start processing in background
                    # (This would typically call your research_service)
                    # Here we just send a mock update for demonstration
                    await asyncio.sleep(1)
                    await manager.broadcast_research_update(
                        task_id=task.id,
                        message="Starting research...",
                        update_type="progress"
                    )
                
                else:
                    # Unknown event type
                    logger.warning(f"Unknown WebSocket event: {event_type}")
                    await manager.send_personal_message({
                        "event": "error",
                        "data": {
                            "message": f"Unknown event type: {event_type}"
                        }
                    }, connection_id)
                
        except WebSocketDisconnect:
            # Handle normal disconnection
            logger.info(f"WebSocket disconnected: {connection_id}")
            await manager.disconnect(connection_id)
            
        except json.JSONDecodeError:
            # Handle invalid JSON
            logger.warning(f"Invalid JSON received from {connection_id}")
            await manager.send_personal_message({
                "event": "error",
                "data": {
                    "message": "Invalid message format (not valid JSON)"
                }
            }, connection_id)
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"WebSocket error: {str(e)}")
            structured_logger.log("error", "WebSocket error",
                                connection_id=connection_id,
                                error_type=type(e).__name__)
            try:
                await manager.send_personal_message({
                    "event": "error",
                    "data": {
                        "message": "An unexpected error occurred"
                    }
                }, connection_id)
            except Exception:
                pass  # Ignore send errors during error handling
            
    finally:
        # Ensure connection is closed and cleaned up
        await manager.disconnect(connection_id)


# Register WebSocket route in the FastAPI app
def setup_websocket(app):
    """
    Set up WebSocket routes in the FastAPI app
    
    Args:
        app: The FastAPI application
    """
    # Add WebSocket route
    app.add_websocket_route("/ws", websocket_endpoint)
    
    # Log setup completion
    logger.info("WebSocket routes initialized")
    structured_logger.log("info", "WebSocket routes initialized")
    
    # Return the global connection manager for reference
    return manager