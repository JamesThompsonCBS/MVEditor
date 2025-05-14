from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from pydantic import BaseModel
from ..auth.jwt import jwt_handler
from ..auth.database import db_auth

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    username: str
    session_id: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint that authenticates user and returns JWT tokens."""
    return await db_auth.authenticate_user(form_data.username, form_data.password)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = jwt_handler.verify_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Validate session
        session_id = payload.get("session_id")
        if not await db_auth.validate_session(session_id):
            raise HTTPException(status_code=401, detail="Session expired")
        
        # Create new tokens
        username = payload.get("sub")
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
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)):
    """Logout endpoint that invalidates the current session."""
    try:
        session_id = current_user.get("session_id")
        await db_auth.invalidate_session(session_id)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)):
    """Get current user information."""
    return current_user 