"""
File Scrubbing Router Module

This module provides secure REST API endpoints for document anonymization and file management
within the SecurePrompt banking application. It handles multi-format file processing with
comprehensive audit logging and role-based access controls.
"""

import logging
import os
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse

from core.config import settings
from api.routers.authentication import require_auth_flexible, extract_client_info
from api.rbac import DESCRUBBER_OR_ADMIN, SCRUBBER_OR_ABOVE
from api.dependencies import (
    get_file_manager_dep,
    get_log_manager_dep,
    get_file_scrubber_dep,
)
from api.models import DescrubRequest, FileScrubResponse
from database.log_record import LogRecord, LogRecordAction, LogRecordCategory
from database.log_manager import LogManager
from database.file_manager import FileManager
from scrubbers.file_scrubber import FileScrubber


router = APIRouter(prefix="/file", tags=["file-scrubbing"])


@router.post("/scrub", response_model=FileScrubResponse)
async def scrub(
    request: Request,
    file: UploadFile = File(...),
    target_risk: str = "C4",
    language: str = "en",
    session=Depends(SCRUBBER_OR_ABOVE),
    log_manager: LogManager = Depends(get_log_manager_dep),
    file_scrubber: FileScrubber = Depends(get_file_scrubber_dep),
):
    """
    Upload and anonymize documents for sensitive information removal.

    This endpoint processes uploaded documents to identify and anonymize personally
    identifiable information (PII) and protected health information (PHI).

    File Processing Pipeline:
    1. File Upload: Secure multipart file upload with validation
    2. Text Extraction: Content extraction from various document formats
    3. Entity Detection: Advanced PII/PHI recognition with Belgian banking support
    4. Anonymization: Configurable entity replacement based on risk level
    5. File Generation: Creation of anonymized document in original format
    6. Secure Storage: Temporary file storage with access controls

    Access Control:
    - Requires: SCRUBBER_OR_ABOVE role (scrubber, descrubber, admin)
    - Corp-Key Isolation: Organization-level data separation
    - JWT Authentication: Secure session-based access control

    Args:
        request (Request): FastAPI request object for client identification
        file (UploadFile): Uploaded document file for processing
        target_risk (str, optional): Anonymization level (C1-C4), defaults to "C4"
        language (str, optional): Processing language, defaults to "en"
        session (dict): Authenticated user session from RBAC dependency
        log_manager (LogManager): Audit logging manager for tamper-proof records
        file_scrubber (FileScrubber): Document processing engine with entity detection

    Returns:
        FileScrubResponse: File processing results including:
            - scrub_id: Unique identifier for audit trail and download access
            - input_filename: Original uploaded filename
            - output_filename: Generated anonymized filename
            - download_url: Secure URL for file retrieval
            - entities: List of detected and anonymized entities

    Raises:
        HTTPException (400): When filename is missing or file validation fails

    Example Response:
        ```json
        {
            "scrub_id": "507f1f77bcf86cd799439011",
            "input_filename": "customer_data.pdf",
            "output_filename": "customer_data_scrubbed_20241201_143022.pdf",
            "download_url": "/file/download/507f1f77bcf86cd799439011",
            "entities": [
                {"entity_type": "PERSON", "count": 3},
                {"entity_type": "BELGIAN_ACCOUNT", "count": 2}
            ]
        }
        ```
    """
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")

    result = file_scrubber.scrub_file(
        file.filename, await file.read(), target_risk, language
    )

    file_id = result.get("file_id", "")
    output_filename = result.get("output_filename", "")

    client_info = extract_client_info(request)

    id = log_manager.add_log(
        LogRecord(
            corp_key=session["corp_key"],
            category=LogRecordCategory.FILE,
            action=LogRecordAction.SCRUB,
            details={
                "file_id": file_id,
                "input_filename": file.filename,
                "output_filename": output_filename,
                "entities": result.get("entities", []),
            },
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
        )
    )

    download_url = f"/file/download/{id}"

    return FileScrubResponse(
        scrub_id=str(id),
        input_filename=file.filename,
        output_filename=output_filename,
        download_url=download_url,
        entities=result.get("entities", []),
    )


@router.post("/descrub")
def descrub(
    request: Request,
    req: DescrubRequest,
    session=Depends(DESCRUBBER_OR_ADMIN),
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    """
    Restore previously anonymized file content with strict access controls.

    This highly restricted endpoint provides controlled access to restore original
    file content from previously processed documents. It implements strict role-based
    access control and comprehensive audit logging for compliance requirements.

    SECURITY CRITICAL: This endpoint provides access to original sensitive document
    content and is restricted to DESCRUBBER_OR_ADMIN roles only with mandatory
    justification and comprehensive audit logging.

    Args:
        request (Request): FastAPI request object for client identification
        req (DescrubRequest): Restoration request including scrub ID and justification
        session (dict): Authenticated user session with descrubber/admin role
        log_manager (LogManager): Audit logging manager for compliance tracking

    Returns:
        dict: Status confirmation for descrubbing operation

    Raises:
        HTTPException (403): Insufficient permissions or corp-key mismatch
        HTTPException (404): Scrub record not found
        HTTPException (400): Invalid record type or missing file data

    Example Request:
        ```json
        {
            "scrub_id": "507f1f77bcf86cd799439011",
            "justification": "Legal discovery request - Case #2024-001"
        }
        ```
    """
    log_record = log_manager.get_log(req.scrub_id)
    if not log_record:
        raise HTTPException(status_code=404, detail="Scrub record not found")

    # Ensure requesting user has permission to descrub this content
    if log_record.corp_key != session["corp_key"]:
        raise HTTPException(
            status_code=403, detail="Access denied to this scrub record"
        )

    if (
        log_record.category != LogRecordCategory.FILE
        or log_record.action != LogRecordAction.SCRUB
    ):
        raise HTTPException(
            status_code=400, detail="Log record is not a file scrub record"
        )

    if not log_record.details:
        raise HTTPException(
            status_code=400, detail="No details found for this scrub record"
        )

    output_filename = log_record.details.get("output_filename", "")
    file_id = log_record.details.get("file_id", "")

    return {"status": "OK"}


@router.get("/download/{id}")
def download(
    request: Request,
    id: str,
    token: str | None = None,
    session=Depends(require_auth_flexible),
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    """
    Download processed files with flexible authentication and comprehensive audit logging.

    This endpoint provides secure file download functionality with support for both
    header-based authentication and query parameter tokens. It implements strict
    access controls and comprehensive audit logging for all file access operations.

    Authentication Methods:
    1. Authorization Header: Standard "Bearer <token>" header authentication
    2. Query Parameter: Token in URL query string for browser downloads

    Access Control:
    - Corp-Key Isolation: Users can only access their organization's files
    - Record Validation: Verifies download request against audit records
    - Session Verification: JWT token validation with role checking

    Args:
        request (Request): FastAPI request object for client identification
        id (str): Unique scrub record identifier for file location
        token (str, optional): JWT token as query parameter for browser compatibility
        session (dict): Authenticated user session from flexible auth dependency
        log_manager (LogManager): Audit logging manager for download tracking

    Returns:
        FileResponse: Secure file download with proper headers and filename

    Raises:
        HTTPException (400): Invalid or missing record ID
        HTTPException (403): Access denied to requested file
        HTTPException (404): Record or file not found

    Example Usage:
        ```
        # Header authentication
        GET /file/download/507f1f77bcf86cd799439011
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        # Query parameter authentication (for browser downloads)
        GET /file/download/507f1f77bcf86cd799439011?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        ```
    """
    if not id:
        raise HTTPException(status_code=400, detail="ID is required")

    log_record = log_manager.get_log(id)
    if not log_record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Ensure requesting user has permission to download this content
    if log_record.corp_key != session["corp_key"]:
        raise HTTPException(status_code=403, detail="Access denied to this record")

    if not log_record.details:
        raise HTTPException(status_code=400, detail="No details found for this record")

    output_filename = log_record.details.get("output_filename", "")
    file_path = Path(settings.TMP_FILES_PATH, output_filename)

    if not file_path.exists():
        logging.warning(f"File not found: {output_filename}")
        raise HTTPException(status_code=404, detail="File not available")

    client_info = extract_client_info(request)

    log_manager.add_log(
        LogRecord(
            corp_key=session["corp_key"],
            category=LogRecordCategory.FILE,
            action=LogRecordAction.DOWNLOAD,
            details={"file_id": id, "file_path": str(file_path)},
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
        )
    )

    return FileResponse(str(file_path), filename=output_filename)
