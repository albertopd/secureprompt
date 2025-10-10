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
    """Scrub sensitive information from text"""
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
    """Descrub (restore) previously scrubbed content - RESTRICTED to descrubber/admin roles"""
    log_record = log_manager.get_log(req.scrub_id)
    if not log_record:
        raise HTTPException(status_code=404, detail="Scrub record not found")

    # Ensure requesting user has permission to descrub this content
    if log_record.corp_key != session["corp_key"]:
        raise HTTPException(
            status_code=403, detail="Access denied to this scrub record"
        )
    
    if log_record.category != LogRecordCategory.TEXT or log_record.action != LogRecordAction.SCRUB:
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
