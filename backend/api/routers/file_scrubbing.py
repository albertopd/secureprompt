import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse

from api.routers.authentication import require_auth_flexible
from api.rbac import DESCRUBBER_OR_ADMIN, SCRUBBER_OR_ABOVE
from api.dependencies import get_audit_manager_dep, get_file_scrubber_dep
from api.models import DescrubRequest, FileScrubResponse
from database.audit_manager import AuditManager
from scrubbers.file_scrubber import FileScrubber


router = APIRouter(prefix="/file", tags=["file-scrubbing"])


@router.post("/scrub", response_model=FileScrubResponse)
async def scrub(
    file: UploadFile = File(...),
    session=Depends(SCRUBBER_OR_ABOVE),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
    file_scrubber: FileScrubber = Depends(get_file_scrubber_dep),
):
    """Upload and scrub a file for sensitive information"""
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")

    result = file_scrubber.scrub_file(file.filename, await file.read())

    id = audit_manager.log(session["corp_key"], "file_scrub", {"filename": file.filename})

    return FileScrubResponse(
        scrub_id=str(id),
        entities=result.get("entities", []),
        filename=result.get("filename", ""),
        download_url=result.get("download_url", "")
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


@router.get("/download/{file_id}")
def download(
    file_id: str, token: str | None = None, session=Depends(require_auth_flexible)
):
    """Download a previously processed file"""
    # TODO: Implement proper file storage and retrieval
    # TODO: Ensure the requesting user has permission to access this file
    # try:
    #     record = files_col.find_one({"_id": file_id})
    # except Exception:
    #     raise HTTPException(status_code=400, detail="Invalid file_id")

    # if not record:
    #     raise HTTPException(status_code=404, detail="File record not found")

    # redacted_path = record.get("redacted_path")

    redacted_dir = Path("C:/tmp/secureprompt_files")
    redacted_path = redacted_dir / f"anonymized_{file_id}"

    if not os.path.exists(redacted_path):
        raise HTTPException(status_code=404, detail="File not available")

    return FileResponse(redacted_path, filename=os.path.basename(redacted_path))
