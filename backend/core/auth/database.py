from typing import Optional, Dict, Any
import uopy
from fastapi import HTTPException
from ..database import get_database_connection
from .jwt import jwt_handler
from datetime import datetime

class DatabaseAuth:
    def __init__(self):
        self.session_file = "MVEDITOR.SESSIONS"
        self.user_file = "MVEDITOR.USERS"

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate a user against the Universe database."""
        try:
            with get_database_connection() as conn:
                # First verify the user exists and password is correct
                cmd = uopy.Command(f"LOGTO {username}")
                cmd.run()
                
                # If we get here, authentication was successful
                # Create session record
                session_id = self._create_session(username)
                
                # Generate tokens
                token_data = {
                    "sub": username,
                    "session_id": session_id
                }
                access_token = jwt_handler.create_access_token(token_data)
                refresh_token = jwt_handler.create_refresh_token(token_data)
                
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "username": username,
                    "session_id": session_id
                }
        except uopy.UOError as e:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def _create_session(self, username: str) -> str:
        """Create a new session record in the database."""
        try:
            with get_database_connection() as conn:
                # Generate a unique session ID
                session_id = f"{username}_{datetime.utcnow().timestamp()}"
                
                # Create session record
                # Format: username^session_id^created_at^last_active^status
                session_data = [
                    username,
                    session_id,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    "ACTIVE"
                ]
                
                # Write to MVEDITOR.SESSIONS
                cmd = uopy.Command(f"WRITE {session_data} TO {self.session_file} {session_id}")
                cmd.run()
                
                return session_id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    async def validate_session(self, session_id: str) -> bool:
        """Validate if a session is still active."""
        try:
            with get_database_connection() as conn:
                cmd = uopy.Command(f"READ {self.session_file} {session_id}")
                cmd.run()
                if not cmd.response:
                    return False
                
                # Update last active timestamp
                session_data = cmd.response.split("^")
                session_data[3] = datetime.utcnow().isoformat()
                
                cmd = uopy.Command(f"WRITE {session_data} TO {self.session_file} {session_id}")
                cmd.run()
                
                return True
        except Exception:
            return False

    async def invalidate_session(self, session_id: str) -> None:
        """Invalidate a session."""
        try:
            with get_database_connection() as conn:
                cmd = uopy.Command(f"DELETE {self.session_file} {session_id}")
                cmd.run()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to invalidate session: {str(e)}")

db_auth = DatabaseAuth() 