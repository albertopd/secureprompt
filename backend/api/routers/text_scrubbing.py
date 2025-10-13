"""
Text Scrubbing Router Module

This module provides secure REST API endpoints for text data anonymization and restoration
within the SecurePrompt banking application. It implements role-based access control and
comprehensive audit logging for all text processing operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from api.models import (
    TextScrubRequest,
    TextDescrubResponse,
    TextScrubResponse,
    DescrubRequest,
)
from api.rbac import DESCRUBBER_OR_ADMIN, SCRUBBER_OR_ABOVE
from api.dependencies import get_log_manager_dep, get_text_scrubber_dep
from api.routers.authentication import extract_client_info
from database.log_record import LogRecord, LogRecordAction, LogRecordCategory
from database.log_manager import LogManager
from scrubbers.text_scrubber import TextScrubber


router = APIRouter(prefix="/text", tags=["text-scrubbing"])


@router.post("/scrub", response_model=TextScrubResponse)
def scrub(
    request: Request,
    req: TextScrubRequest,
    session=Depends(SCRUBBER_OR_ABOVE),
    log_manager: LogManager = Depends(get_log_manager_dep),
    text_scrubber: TextScrubber = Depends(get_text_scrubber_dep),
):
    """
    Anonymize sensitive information in text using advanced PII/PHI detection.

    This endpoint processes text content to identify and anonymize personally identifiable
    information (PII) and protected health information (PHI) using Microsoft Presidio
    with specialized Belgian banking entity recognizers. All scrubbing operations are
    logged for compliance and security monitoring.

    Access Control:
    - Requires: SCRUBBER_OR_ABOVE role (scrubber, descrubber, admin)
    - Corp-Key Isolation: Users only access their organization's data
    - JWT Authentication: Secure session-based access control

    Args:
        request (Request): FastAPI request object for client identification
        req (TextScrubRequest): Text scrubbing parameters including content and options
        session (dict): Authenticated user session from RBAC dependency
        log_manager (LogManager): Audit logging manager for tamper-proof records
        text_scrubber (TextScrubber): Presidio-based text anonymization engine

    Returns:
        TextScrubResponse: Scrubbing results including:
            - scrub_id: Unique identifier for audit trail and potential restoration
            - scrubbed_text: Anonymized text with entities replaced
            - entities: List of detected entities with metadata

    Example Request:
        ```json
        {
            "prompt": "Contact John Doe at john@company.com or account BE68539007547034",
            "language": "en",
            "target_risk": "C3"
        }
        ```

    Example Response:
        ```json
        {
            "scrub_id": "507f1f77bcf86cd799439011",
            "scrubbed_text": "Contact <PERSON> at <EMAIL> or account <BELGIAN_ACCOUNT>",
            "entities": [
                {"entity_type": "PERSON", "start": 8, "end": 16, "replacement": "<PERSON>"},
                {"entity_type": "EMAIL", "start": 20, "end": 36, "replacement": "<EMAIL>"}
            ]
        }
        ```
    """
    lang = req.language if req.language else "en"
    target_risk = req.target_risk if req.target_risk else "C4"
    scrub_result = text_scrubber.scrub_text(req.prompt, target_risk, lang)

    log_details = {
        "language": lang,
        "target_risk": target_risk,
        "original_text": req.prompt,
    }
    log_details.update(scrub_result)

    client_info = extract_client_info(request)

    id = log_manager.add_log(
        LogRecord(
            corp_key=session["corp_key"],
            category=LogRecordCategory.TEXT,
            action=LogRecordAction.SCRUB,
            details=log_details,
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
        )
    )

    return TextScrubResponse(
        scrub_id=str(id),
        scrubbed_text=scrub_result.get("scrubbed_text", ""),
        entities=scrub_result.get("entities", []),
    )


@router.post("/descrub")
def descrub(
    request: Request,
    req: DescrubRequest,
    session=Depends(DESCRUBBER_OR_ADMIN),
    log_manager: LogManager = Depends(get_log_manager_dep),
    text_scrubber: TextScrubber = Depends(get_text_scrubber_dep),
):
    """
    Restore previously anonymized text content with strict access controls.

    This highly restricted endpoint allows authorized personnel to restore original
    text content from previously scrubbed records. It implements strict role-based
    access control and requires justification for all restoration operations.

    SECURITY CRITICAL: This endpoint provides access to original sensitive data
    and is restricted to DESCRUBBER_OR_ADMIN roles only with comprehensive auditing.

    Access Control:
    - Requires: DESCRUBBER_OR_ADMIN role (descrubber, admin only)
    - Corp-Key Validation: Access restricted to same user data
    - Record Verification: Validates scrub record existence and type
    - Justification Required: Mandatory business justification for compliance

    Args:
        request (Request): FastAPI request object for client identification
        req (DescrubRequest): Restoration parameters including scrub ID and options
        session (dict): Authenticated user session with descrubber/admin role
        log_manager (LogManager): Audit logging manager for compliance tracking
        text_scrubber (TextScrubber): Text processing engine for selective restoration

    Returns:
        TextDescrubResponse: Restoration results including:
            - scrub_id: Original scrubbing operation identifier
            - original_text: Fully restored original content
            - scrubbed_text: Previously anonymized version
            - descrubbed_text: Current restoration result

    Raises:
        HTTPException (403): Insufficient permissions or corp-key mismatch
        HTTPException (404): Scrub record not found
        HTTPException (400): Invalid record type or missing data

    Example Request:
        ```json
        {
            "scrub_id": "507f1f77bcf86cd799439011",
            "descrub_all": false,
            "entity_replacements": ["<PERSON>", "<EMAIL>"],
            "justification": "Customer service escalation - fraud investigation"
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
        log_record.category != LogRecordCategory.TEXT
        or log_record.action != LogRecordAction.SCRUB
    ):
        raise HTTPException(
            status_code=400, detail="Log record is not a text scrub record"
        )

    if not log_record.details:
        raise HTTPException(
            status_code=400, detail="No details found for this scrub record"
        )

    original_text = log_record.details.get("original_text", "")
    scrubbed_text = log_record.details.get("scrubbed_text", "")
    entities = log_record.details.get("entities", [])

    if req.descrub_all:
        if not original_text:
            raise HTTPException(
                status_code=400, detail="Original text not found in scrub record"
            )
        descrubbed_text = original_text
    else:
        if not req.entity_replacements:
            raise HTTPException(
                status_code=400,
                detail="No entity replacements provided for partial descrubbing",
            )

        if not entities:
            raise HTTPException(
                status_code=400, detail="No entities found in scrub record"
            )

        if not scrubbed_text:
            raise HTTPException(
                status_code=400, detail="Scrubbed text not found in scrub record"
            )

        entities_to_replace = [
            e for e in entities if e.get("replacement") in req.entity_replacements
        ]
        descrubbed_text = text_scrubber.descrub_text(scrubbed_text, entities_to_replace)

    client_info = extract_client_info(request)

    log_manager.add_log(
        LogRecord(
            corp_key=session["corp_key"],
            category=LogRecordCategory.TEXT,
            action=LogRecordAction.DESCRUB,
            details={
                "scrub_id": req.scrub_id,
                "descrub_all": req.descrub_all,
                "entity_replacements": req.entity_replacements,
                "replaced_entities": (
                    entities if req.descrub_all else entities_to_replace
                ),
                "justification": req.justification,
                "original_text": original_text,
                "scrubbed_text": scrubbed_text,
                "descrubbed_text": descrubbed_text,
            },
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
        )
    )

    return TextDescrubResponse(
        scrub_id=req.scrub_id,
        original_text=original_text,
        scrubbed_text=scrubbed_text,
        descrubbed_text=descrubbed_text,
    )
