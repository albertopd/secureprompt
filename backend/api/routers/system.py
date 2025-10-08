from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.logger import logger

from database.connection import db_manager


router = APIRouter(tags=["system"])


@router.get("/health/live")
def liveness_check():
    """
    Liveness probe endpoint.
    Simple check to verify the application process is alive.
    Used by Kubernetes liveness probes.
    """
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/ready")
def readiness_check():
    """
    Readiness probe endpoint.
    Checks if the service is ready to handle requests (including database connectivity).
    Used by Kubernetes readiness probes.
    """
    try:
        # Test database connection
        client = db_manager.client
        # Simple ping to verify database is accessible
        client.admin.command("ping")

        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not ready",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )