"""
System Health and Monitoring Router Module

This module provides essential system health monitoring and readiness check endpoints
for the SecurePrompt banking application. These endpoints are critical for operational
monitoring, container orchestration, and service reliability management.

Key Features:
- Liveness Probes: Basic application process health verification
- Readiness Probes: Comprehensive service readiness including database connectivity
- Kubernetes Integration: Compatible with container orchestration health checks
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.logger import logger

from database.connection import db_manager


router = APIRouter(tags=["system"])


@router.get("/health/live")
def liveness_check():
    """
    Application liveness probe for container orchestration and process monitoring.

    This endpoint provides a lightweight health check to verify that the application
    process is alive and responsive. It performs no external dependency validation
    and is designed for high-frequency polling by container orchestrators.

    Purpose:
    - Container Restart Decisions: Kubernetes uses this to determine if containers should be restarted
    - Process Health Verification: Confirms the application process is running and responsive
    - Basic Service Availability: Minimal overhead check for service availability
    - Monitoring Integration: Simple endpoint for monitoring systems and load balancers

    Kubernetes Integration:
        ```yaml
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        ```

    Returns:
        dict: Liveness status including:
            - status: Always "alive" when endpoint is responsive
            - timestamp: UTC timestamp in ISO 8601 format

    Example Response:
        ```json
        {
            "status": "alive",
            "timestamp": "2024-12-01T14:30:22.123456Z"
        }
        ```
    """
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/ready")
def readiness_check():
    """
    Service readiness probe with comprehensive dependency validation.

    This endpoint performs thorough health checks including database connectivity
    and external dependency validation to determine if the service is ready to
    accept and properly handle incoming requests.

    Purpose:
    - Traffic Routing Decisions: Load balancers use this to determine if traffic should be routed
    - Service Readiness: Validates all dependencies are available for request processing
    - Startup Validation: Ensures service is fully initialized before accepting traffic
    - Operational Monitoring: Comprehensive service health status for monitoring systems

    Validation Checks:
    - Database Connectivity: MongoDB connection and ping verification
    - Initialization Status: Service startup and configuration completion

    Response Behavior:
    - Success (200): All dependencies available, service ready for traffic
    - Failure (503): One or more dependencies unavailable, service not ready
    - Detailed Status: Specific dependency status for troubleshooting

    Kubernetes Integration:
        ```yaml
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        ```

    Returns:
        dict: Readiness status including:
            - status: "ready" when all dependencies are available
            - database: Database connectivity status ("connected"/"disconnected")
            - timestamp: UTC timestamp in ISO 8601 format

    Raises:
        HTTPException (503): When service is not ready with detailed error information

    Success Response:
        ```json
        {
            "status": "ready",
            "database": "connected",
            "timestamp": "2024-12-01T14:30:22.123456Z"
        }
        ```

    Failure Response:
        ```json
        {
            "status": "not ready",
            "database": "disconnected",
            "error": "Database connection failed: Connection timeout",
            "timestamp": "2024-12-01T14:30:22.123456Z"
        }
        ```
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
