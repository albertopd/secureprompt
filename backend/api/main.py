from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI
from fastapi.logger import logger
from core.config import settings
from database.connection import db_manager
from api.routers import system, authentication, text_scrubbing, file_scrubbing


# Lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
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


# Create app with lifespan
app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Include routers
# Health check at root level (no versioning) - recommended for monitoring/load balancers
app.include_router(system.router)
app.include_router(authentication.router, prefix=settings.API_V1_STR)
app.include_router(text_scrubbing.router, prefix=settings.API_V1_STR)
app.include_router(file_scrubbing.router, prefix=settings.API_V1_STR)
