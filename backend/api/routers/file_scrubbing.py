import logging
import os
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse

from core.config import settings
from api.routers.authentication import require_auth_flexible, extract_client_info
from api.rbac import DESCRUBBER_OR_ADMIN, SCRUBBER_OR_ABOVE
from api.dependencies import get_file_manager_dep, get_log_manager_dep, get_file_scrubber_dep
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
    """Upload and scrub a file for sensitive information"""
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")

    result = file_scrubber.scrub_file(file.filename, await file.read(), target_risk, language)

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
                "entities": result.get("entities", [])
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
        entities=result.get("entities", [])
    )


@router.post("/descrub")
def descrub(
    request: Request,
    req: DescrubRequest,
    session=Depends(DESCRUBBER_OR_ADMIN),
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    """Descrub (restore) previously scrubbed content - RESTRICTED to descrubber/admin roles"""
    # TODO: Implement descrubbing logic if applicable
    # TODO: Ensure requesting user has permission to descrub this content

    client_info = extract_client_info(request)

    log_manager.add_log(
        LogRecord(
            corp_key=session["corp_key"],
            category=LogRecordCategory.FILE,
            action=LogRecordAction.DESCRUB,
            details=req.model_dump(),
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
        )
    )
    return {"status": "OK"}


@router.get("/download/{id}")
def download(
    request: Request,
    id: str,
    token: str | None = None,
    session=Depends(require_auth_flexible),
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    if not id:
        raise HTTPException(status_code=400, detail="ID is required")

    log_record = log_manager.get_log(id)
    if not log_record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Ensure requesting user has permission to download this content
    if log_record.corp_key != session["corp_key"]:
        raise HTTPException(
            status_code=403, detail="Access denied to this record"
        )

    if not log_record.details:
        raise HTTPException(
            status_code=400, detail="No details found for this record"
        )
    
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
