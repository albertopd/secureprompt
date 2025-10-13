"""
SecurePrompt FastAPI Application

This module contains the main FastAPI application for the SecurePrompt system,
a text and file scrubbing/de-scrubbing service with role-based access control
and audit logging features.

The application provides APIs for:
- Text/File scrubbing and de-scrubbing
- User authentication with JWT tokens and role-based access
- Comprehensive audit logging
- Health monitoring endpoints

Security Features:
- Role-based access control (scrubber, descrubber, auditor, admin)
- Device and browser identification logging
- Client IP tracking and location identification
"""

from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI
from fastapi.logger import logger
from core.config import settings
from database.connection import db_manager
from api.routers import system, authentication, text_scrubbing, file_scrubbing, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler for managing application startup and shutdown.

    Manages the MongoDB database connection lifecycle:
    - Initializes database connection on startup
    - Ensures proper cleanup on shutdown

    Args:
        app (FastAPI): The FastAPI application instance

    Yields:
        None: Control back to FastAPI to start serving requests

    Raises:
        Exception: If database initialization fails
    """
    # Initialize MongoDB connection using the database manager
    try:
        db_manager.initialize()
        logger.info("MongoDB connection initialized")

        # Yield control back to FastAPI to start serving requests
        yield

    finally:
        # Cleanup at shutdown
        try:
            db_manager.close()
            logger.info("MongoDB connection closed")
        except Exception:
            logger.error("Error closing MongoDB client", exc_info=True)


# Create FastAPI application with lifecycle management
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    description="""
    SecurePrompt API - Text/file scrubbing and de-scrubbing service with comprehensive security features.
    """,
    version="1.0.0",
)

# Include API routers with appropriate prefixes
# System/Health endpoints at root level (no versioning) for monitoring compatibility
app.include_router(system.router)

# Versioned API endpoints under /api/v1 prefix
app.include_router(authentication.router, prefix=settings.API_V1_STR)
app.include_router(text_scrubbing.router, prefix=settings.API_V1_STR)
app.include_router(file_scrubbing.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
