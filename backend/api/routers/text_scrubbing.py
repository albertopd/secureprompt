from fastapi import APIRouter, Depends, HTTPException, Request

from api.models import (
    ScrubRequest,
    TextDescrubResponse,
    TextScrubResponse,
    DescrubRequest,
)
from api.rbac import DESCRUBBER_OR_ADMIN, SCRUBBER_OR_ABOVE
from api.dependencies import get_audit_manager_dep, get_text_scrubber_dep
from api.routers.authentication import extract_client_info
from database.log_manager import (
    LogRecordAction,
    LogRecordCategory,
    LogManager,
    LogRecord,
)
from scrubbers.text_scrubber import TextScrubber


router = APIRouter(prefix="/text", tags=["text-scrubbing"])


@router.post("/scrub", response_model=TextScrubResponse)
def scrub(
    request: Request,
    req: ScrubRequest,
    session=Depends(SCRUBBER_OR_ABOVE),
    audit_manager: LogManager = Depends(get_audit_manager_dep),
    text_scrubber: TextScrubber = Depends(get_text_scrubber_dep),
):
    """Scrub sensitive information from text"""
    lang = req.language if req.language else "en"
    target_risk = req.target_risk if req.target_risk else "C4"
    scrub_result = text_scrubber.anonymize_text(req.prompt, target_risk, lang)

    audits_details = {
        "language": lang,
        "target_risk": target_risk,
        "original_text": req.prompt,
    }
    audits_details.update(scrub_result)

    client_info = extract_client_info(request)

    id = audit_manager.add_log(
        LogRecord(
            corp_key=session["corp_key"],
            category=LogRecordCategory.TEXT,
            action=LogRecordAction.SCRUB,
            details=audits_details,
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
        )
    )

    return TextScrubResponse(
        scrub_id=str(id),
        scrubbed_text=scrub_result.get("anonymized_text", ""),
        entities=scrub_result.get("entities", []),
    )


@router.post("/descrub")
def descrub(
    request: Request,
    req: DescrubRequest,
    session=Depends(DESCRUBBER_OR_ADMIN),
    audit_manager: LogManager = Depends(get_audit_manager_dep),
):
    """Descrub (restore) previously scrubbed content - RESTRICTED to descrubber/admin roles"""
    # TODO: Ensure requesting user has permission to descrub this content
    audit_record = audit_manager.get_log(req.scrub_id)
    if not audit_record:
        raise HTTPException(status_code=404, detail="Scrub record not found")

    if not audit_record.details:
        raise HTTPException(
            status_code=400, detail="No details found for this scrub record"
        )

    if req.descrub_all:
        original_text = audit_record.details.get("original_text", "")
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

        entities = audit_record.details.get("entities", [])
        if not entities:
            raise HTTPException(
                status_code=400, detail="No entities found in scrub record"
            )

        scrubbed_text = audit_record.details.get("anonymized_text", "")
        if not scrubbed_text:
            raise HTTPException(
                status_code=400, detail="Scrubbed text not found in scrub record"
            )

        descrubbed_text = scrubbed_text
        for entity_replacement in req.entity_replacements:
            entity = next(
                (e for e in entities if e.get("replacement") == entity_replacement),
                None,
            )
            if entity and entity.get("original"):
                descrubbed_text = descrubbed_text.replace(
                    entity["replacement"], entity["original"]
                )

    client_info = extract_client_info(request)

    audit_manager.add_log(
        LogRecord(
            corp_key=session["corp_key"],
            category=LogRecordCategory.TEXT,
            action=LogRecordAction.DESCRUB,
            details={
                "scrub_id": req.scrub_id,
                "descrub_all": req.descrub_all,
                "entity_replacements": req.entity_replacements,
                "justification": req.justification,
                "original_text": audit_record.details.get("original_text", ""),
                "scrubbed_text": audit_record.details.get("anonymized_text", ""),
                "descrubbed_text": descrubbed_text,
            },
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
        )
    )

    return TextDescrubResponse(scrub_id=req.scrub_id, descrubbed_text=descrubbed_text)
