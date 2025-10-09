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
    Get system-wide audit statistics and summary information.

    Returns total counts by category and action across all logs.
    Requires auditor, descrubber, or admin role.
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
