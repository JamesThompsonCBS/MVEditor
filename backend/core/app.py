from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
import uopy
from .config import Settings
from .database import get_database_connection
from .routers import workspace, auth, files, editor, websocket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MVEditor API",
    description="Backend API for MVEditor - A MultiValue Database Editor",
    version="25.04.46.1"  # Following our versioning convention
)

# Load settings
settings = Settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Global error handler caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "message": str(exc)
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    try:
        # Test database connection
        with get_database_connection() as conn:
            cmd = uopy.Command("LIST VOC")
            cmd.run()
        return {
            "status": "healthy",
            "database": "connected",
            "version": app.version
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "message": "Welcome to MVEditor API",
        "version": app.version,
        "documentation": "/docs"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting MVEditor API...")
    try:
        # Test database connection on startup
        with get_database_connection() as conn:
            logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}", exc_info=True)
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MVEditor API...")

# Include routers
app.include_router(auth.router)
app.include_router(workspace.router)
app.include_router(files.router)
app.include_router(editor.router)
app.include_router(websocket.router) 