from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Any
import json
import logging
from ..auth.jwt import jwt_handler
from ..websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
    responses={404: {"description": "Not found"}},
)

async def get_current_user_ws(websocket: WebSocket) -> Dict[str, Any]:
    """Get current user from WebSocket connection."""
    try:
        # Get token from query parameters
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            raise HTTPException(status_code=401, detail="Missing authentication token")
        
        # Verify token using WebSocket-specific method
        user = jwt_handler.verify_ws_token(token)
        return user
    except Exception as e:
        await websocket.close(code=4001, reason="Invalid authentication token")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@router.websocket("/workspace/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    """WebSocket endpoint for workspace collaboration."""
    try:
        # Authenticate user
        user = await get_current_user_ws(websocket)
        user_id = user["sub"]
        username = user.get("username", user_id)
        
        # Connect to workspace
        await manager.connect(websocket, workspace_id, user_id, username)
        
        try:
            while True:
                # Receive and process messages
                data = await websocket.receive_json()
                
                if not isinstance(data, dict) or "type" not in data:
                    continue
                
                message_type = data["type"]
                message_data = data.get("data", {})
                
                # Handle different message types
                if message_type == "cursor_update":
                    await manager.update_cursor_position(
                        workspace_id,
                        user_id,
                        username,
                        message_data.get("position", {})
                    )
                elif message_type == "chat_message":
                    await manager.broadcast_chat_message(
                        workspace_id,
                        user_id,
                        username,
                        message_data.get("message", "")
                    )
                else:
                    logger.warning(f"Unknown message type: {message_type}")
        
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error in websocket connection: {str(e)}")
            await manager.disconnect(websocket)
    
    except Exception as e:
        logger.error(f"Error establishing websocket connection: {str(e)}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass 