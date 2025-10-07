from fastapi import APIRouter, Depends

from api.models import ScrubRequest, TextScrubResponse, DescrubRequest
from api.rbac import DESCRUBBER_OR_ADMIN, SCRUBBER_OR_ABOVE
from api.dependencies import get_audit_manager_dep, get_text_scrubber_dep
from database.audit_manager import AuditManager
from scrubbers.text_scrubber import TextScrubber


router = APIRouter(prefix="/text", tags=["text-scrubbing"])


@router.post("/scrub", response_model=TextScrubResponse)
def scrub(
    req: ScrubRequest,
    session=Depends(SCRUBBER_OR_ABOVE),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
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

    id = audit_manager.log(session["corp_key"], "scrub", audits_details)

    return TextScrubResponse(
        scrub_id=str(id),
        scrubbed_text=scrub_result.get("anonymized_text", ""),
        entities=scrub_result.get("entities", []),
    )


@router.post("/descrub")
def descrub(
    req: DescrubRequest,
    session=Depends(DESCRUBBER_OR_ADMIN),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
):
    """Descrub (restore) previously scrubbed content - RESTRICTED to descrubber/admin roles"""
    # TODO: Implement descrubbing logic if applicable
    # TODO: Ensure requesting user has permission to descrub this content
    audit_manager.log(session["corp_key"], "descrub", req.model_dump())
    return {"status": "OK"}
