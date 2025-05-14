from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Active connections by workspace_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # User information by WebSocket connection
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        # Cursor positions by workspace_id -> {user_id: position}
        self.cursor_positions: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
    async def connect(self, websocket: WebSocket, workspace_id: str, user_id: str, username: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        
        # Initialize workspace connections if needed
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = set()
            self.cursor_positions[workspace_id] = {}
        
        # Store connection
        self.active_connections[workspace_id].add(websocket)
        self.connection_info[websocket] = {
            "user_id": user_id,
            "username": username,
            "workspace_id": workspace_id,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        # Notify others of new connection
        await self.broadcast_user_joined(workspace_id, user_id, username)
        
        # Send current cursor positions to new user
        if self.cursor_positions[workspace_id]:
            await websocket.send_json({
                "type": "cursor_positions",
                "data": self.cursor_positions[workspace_id]
            })
        
        logger.info(f"User {username} connected to workspace {workspace_id}")
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        try:
            info = self.connection_info.get(websocket)
            if info:
                workspace_id = info["workspace_id"]
                user_id = info["user_id"]
                username = info["username"]
                
                # Remove from active connections
                if workspace_id in self.active_connections:
                    self.active_connections[workspace_id].remove(websocket)
                    if not self.active_connections[workspace_id]:
                        del self.active_connections[workspace_id]
                        del self.cursor_positions[workspace_id]
                
                # Remove cursor position
                if workspace_id in self.cursor_positions and user_id in self.cursor_positions[workspace_id]:
                    del self.cursor_positions[workspace_id][user_id]
                
                # Remove connection info
                del self.connection_info[websocket]
                
                # Notify others of disconnection
                await self.broadcast_user_left(workspace_id, user_id, username)
                
                logger.info(f"User {username} disconnected from workspace {workspace_id}")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
    
    async def broadcast(self, workspace_id: str, message: Dict[str, Any]):
        """Broadcast a message to all clients in a workspace."""
        if workspace_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[workspace_id]:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error(f"Error broadcasting message: {str(e)}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast_user_joined(self, workspace_id: str, user_id: str, username: str):
        """Broadcast user joined notification."""
        await self.broadcast(workspace_id, {
            "type": "user_joined",
            "data": {
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    async def broadcast_user_left(self, workspace_id: str, user_id: str, username: str):
        """Broadcast user left notification."""
        await self.broadcast(workspace_id, {
            "type": "user_left",
            "data": {
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    async def update_cursor_position(self, workspace_id: str, user_id: str, username: str, position: Dict[str, Any]):
        """Update and broadcast cursor position."""
        if workspace_id not in self.cursor_positions:
            self.cursor_positions[workspace_id] = {}
        
        self.cursor_positions[workspace_id][user_id] = {
            "username": username,
            "position": position,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(workspace_id, {
            "type": "cursor_update",
            "data": {
                "user_id": user_id,
                "username": username,
                "position": position,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    async def broadcast_chat_message(self, workspace_id: str, user_id: str, username: str, message: str):
        """Broadcast a chat message."""
        await self.broadcast(workspace_id, {
            "type": "chat_message",
            "data": {
                "user_id": user_id,
                "username": username,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

# Create a global instance of the connection manager
manager = ConnectionManager() 