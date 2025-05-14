import asyncio
import websockets
import json
import logging
import requests
from typing import Dict, Any
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/workspace/test_workspace"

async def get_auth_token(username: str = "test_user", password: str = "test_password") -> str:
    """Get authentication token from the server."""
    try:
        # Use form data for login endpoint
        response = requests.post(
            f"{SERVER_URL}/auth/login",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"  # Required by OAuth2PasswordRequestForm
            }
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        logger.error(f"Failed to get auth token: {str(e)}")
        raise

async def test_websocket_connection():
    """Test WebSocket connection and message handling."""
    try:
        # Get authentication token
        token = await get_auth_token()
        if not token:
            logger.error("Failed to obtain authentication token")
            return False

        # Connect to WebSocket with token
        async with websockets.connect(
            f"ws://localhost:8000/ws/workspace/test-workspace?token={token}"
        ) as websocket:
            # Test sending a cursor update
            cursor_message = {
                "type": "cursor_update",
                "data": {
                    "position": {"line": 1, "character": 10}
                }
            }
            await websocket.send(json.dumps(cursor_message))
            
            # Test sending a chat message
            chat_message = {
                "type": "chat_message",
                "data": {
                    "message": "Hello from test client!"
                }
            }
            await websocket.send(json.dumps(chat_message))
            
            # Wait for any responses
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    logger.info(f"Received message: {response}")
            except asyncio.TimeoutError:
                logger.info("No more messages received")
            
            return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

async def main():
    """Run the WebSocket test."""
    try:
        # First check if server is running
        response = requests.get(f"{SERVER_URL}/health")
        if response.status_code == 200:
            logger.info("Server is running and healthy")
        else:
            logger.error("Server health check failed")
            return

        # Run WebSocket test
        await test_websocket_connection()
        logger.info("WebSocket test completed successfully")

    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to server. Is it running?")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 