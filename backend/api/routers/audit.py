"""
Audit and Compliance Router Module

This module provides comprehensive audit trail access and compliance reporting
capabilities for the SecurePrompt banking application.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from api.models import (
    LogListResponse,
    LogSearchResponse,
    LogRecordResponse,
    PaginationInfo,
    LogSearchFilters,
)
from api.rbac import AUDITOR_OR_ADMIN
from api.dependencies import get_log_manager_dep
from database.log_manager import LogManager


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=LogListResponse)
def list_logs(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of logs per page"),
    session=Depends(AUDITOR_OR_ADMIN),
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    """
    Retrieve paginated audit logs.

    This endpoint provides access to the complete audit trail with pagination
    support for efficient large dataset handling. All logs are retrieved from
    the MongoDB collection.

    Features:
    - Paginated Retrieval: Efficient handling of large audit datasets
    - Complete Audit Data: Full log records with all metadata and client information
    - Role-Based Access: Restricted to auditor/admin roles for security
    - Performance Optimized: Efficient MongoDB queries with proper indexing

    Access Control:
    - Requires: AUDITOR_OR_ADMIN role (auditor, admin)
    - Authentication: JWT token validation with session management

    Args:
        page (int): Page number for pagination (1-based, minimum 1)
        page_size (int): Number of records per page (1-100, default 20)
        session (dict): Authenticated user session from RBAC dependency
        log_manager (LogManager): Audit log manager for data access

    Returns:
        LogListResponse: Paginated audit logs including:
            - logs: Array of complete log records with all metadata
            - pagination: Pagination information with total counts and navigation

    Raises:
        HTTPException (500): Database errors or system failures

    Example Response:
        ```json
        {
            "logs": [
                {
                    "id": "507f1f77bcf86cd799439011",
                    "corp_key": "COMPANY_001",
                    "category": "SECURITY",
                    "action": "LOGIN",
                    "device_info": "Windows 10/11",
                    "browser_info": "Chrome 120.0",
                    "client_ip": "192.168.1.100",
                    "timestamp": "2024-12-01T14:30:22Z",
                    "details": {"email": "user@company.com", "role": "scrubber"}
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_pages": 15,
                "total_records": 300,
                "has_next": true,
                "has_previous": false
            }
        }
        ```
    """
    try:
        result = log_manager.list_logs(page=page, page_size=page_size)

        # Convert results to response format
        log_responses = []
        for log_record in result["logs"]:
            log_responses.append(
                LogRecordResponse(
                    id=str(log_record["id"]),
                    corp_key=log_record["corp_key"],
                    category=log_record["category"],
                    action=log_record["action"],
                    details=log_record.get("details", {}),
                    device_info=log_record.get("device_info"),
                    browser_info=log_record.get("browser_info"),
                    client_ip=log_record.get("client_ip"),
                    user_agent=log_record.get("user_agent"),
                    timestamp=log_record["timestamp"],
                )
            )

        return LogListResponse(
            logs=log_responses, pagination=PaginationInfo(**result["pagination"])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@router.get("/search", response_model=LogSearchResponse)
def search_logs(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of logs per page"),
    corp_key: Optional[str] = Query(None, description="Filter by corporate key"),
    category: Optional[str] = Query(
        None, description="Filter by log category (security, text, file, system)"
    ),
    action: Optional[str] = Query(
        None, description="Filter by action (login, logout, scrub, descrub, download)"
    ),
    start_date: Optional[str] = Query(
        None, description="Start date (ISO format: 2023-01-01T00:00:00Z)"
    ),
    end_date: Optional[str] = Query(
        None, description="End date (ISO format: 2023-12-31T23:59:59Z)"
    ),
    session=Depends(AUDITOR_OR_ADMIN),
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    """
    Advanced audit log search with comprehensive filtering and compliance reporting.

    Search Capabilities:
    - Corporate Key: Organization-level audit filtering (COMPANY_001, COMPANY_002)
    - Log Categories: SECURITY (auth events), TEXT (scrubbing), FILE (documents), SYSTEM (health)
    - Action Types: LOGIN, LOGOUT, SCRUB, DESCRUB, DOWNLOAD, UPLOAD, HEALTH_CHECK
    - Time Ranges: Flexible date filtering with precision to seconds
    - Combined Filters: Multiple simultaneous criteria for precise audit analysis
    - Paginated Results: Efficient handling of large result sets with pagination

    Access Control:
    - Requires: AUDITOR_OR_ADMIN role (auditor, admin)
    - Authentication: JWT token validation with session management

    Args:
        page (int): Page number for pagination (1-based, minimum 1)
        page_size (int): Number of records per page (1-100, default 20)
        corp_key (str, optional): Filter by corporate identifier for organization-specific audits
        category (str, optional): Filter by log category (SECURITY, TEXT, FILE, SYSTEM)
        action (str, optional): Filter by specific action type (LOGIN, SCRUB, etc.)
        start_date (str, optional): Start date in ISO 8601 format for date range filtering
        end_date (str, optional): End date in ISO 8601 format for date range filtering
        session (dict): Authenticated user session from RBAC dependency
        log_manager (LogManager): Audit log manager for advanced search capabilities

    Returns:
        LogSearchResponse: Filtered audit results including:
            - logs: Array of matching log records with complete metadata
            - pagination: Pagination information for result navigation
            - filters: Applied filter criteria for result context

    Raises:
        HTTPException (500): Database errors, invalid date formats, or system failures

    Example Query:
        ```
        GET /audit/search?corp_key=COMPANY_001&category=SECURITY&action=LOGIN&start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z&page=1&page_size=50
        ```

    Example Response:
        ```json
        {
            "logs": [...],
            "pagination": {...},
            "filters": {
                "corp_key": "COMPANY_001",
                "category": "SECURITY",
                "action": "LOGIN",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z"
            }
        }
        ```
    """
    try:
        result = log_manager.search_logs(
            page=page,
            page_size=page_size,
            corp_key=corp_key,
            category=category,
            action=action,
            start_date=start_date,
            end_date=end_date,
        )

        # Convert results to response format
        log_responses = []
        for log_record in result["logs"]:
            log_responses.append(
                LogRecordResponse(
                    id=str(log_record["id"]),
                    corp_key=log_record["corp_key"],
                    category=log_record["category"],
                    action=log_record["action"],
                    details=log_record.get("details", {}),
                    device_info=log_record.get("device_info"),
                    browser_info=log_record.get("browser_info"),
                    client_ip=log_record.get("client_ip"),
                    user_agent=log_record.get("user_agent"),
                    timestamp=log_record["timestamp"],
                )
            )

        return LogSearchResponse(
            logs=log_responses,
            pagination=PaginationInfo(**result["pagination"]),
            filters=LogSearchFilters(**result["filters"]),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching logs: {str(e)}")


@router.get("/stats")
def get_audit_stats(
    session=Depends(AUDITOR_OR_ADMIN),
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    """
    Generate comprehensive audit statistics and compliance reporting metrics.

    This endpoint provides system-wide audit analytics including activity summaries,
    category distributions, and action frequency analysis. Essential for compliance
    reporting, security monitoring, and operational analytics.

    Features:
    - System-Wide Analytics: Complete audit trail statistical analysis
    - Category Breakdown: Distribution analysis by log categories (security, text, file, system)

    Statistical Metrics:
    - Total Log Count: Complete audit record volume across all categories
    - Category Distribution: Breakdown by SECURITY, TEXT, FILE, SYSTEM events
    - Action Analysis: Frequency distribution of LOGIN, LOGOUT, SCRUB, DESCRUB operations
    - Trend Indicators: Activity patterns for operational monitoring

    Access Control:
    - Requires: AUDITOR_OR_ADMIN role (auditor, admin)
    - Authentication: JWT token validation with session management

    Args:
        session (dict): Authenticated user session from RBAC dependency
        log_manager (LogManager): Audit log manager for statistical aggregation

    Returns:
        dict: Comprehensive audit statistics including:
            - total_logs: Total number of audit records across all categories
            - categories: Distribution breakdown by log category with counts
            - actions: Frequency analysis by action type with counts

    Raises:
        HTTPException (500): Database aggregation errors or system failures

    Example Response:
        ```json
        {
            "total_logs": 15847,
            "categories": {
                "SECURITY": 3421,
                "TEXT": 7892,
                "FILE": 3156,
                "SYSTEM": 1378
            },
            "actions": {
                "LOGIN": 1834,
                "LOGOUT": 1587,
                "SCRUB": 4521,
                "DESCRUB": 289,
                "DOWNLOAD": 2635,
                "UPLOAD": 521,
                "HEALTH_CHECK": 4460
            }
        }
        ```
    """
    try:
        # Get total system-wide counts
        total_logs = log_manager.logs.count_documents({})

        # Get counts by category
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        category_stats = list(log_manager.logs.aggregate(category_pipeline))

        # Get counts by action
        action_pipeline = [
            {"$group": {"_id": "$action", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        action_stats = list(log_manager.logs.aggregate(action_pipeline))

        return {
            "total_logs": total_logs,
            "categories": {item["_id"]: item["count"] for item in category_stats},
            "actions": {item["_id"]: item["count"] for item in action_stats},
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving audit stats: {str(e)}"
        )
