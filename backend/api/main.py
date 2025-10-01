import uuid
import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from api.models import LoginRequest, ScrubRequest, DescrubRequest
from scrubbers.text_scrubber import TextScrubber
from scrubbers.file_scrubber import FileScrubber
from audit.auditor import Auditor
from database.mongo import get_collection

app = FastAPI(title="SecurePrompt API")

SESSIONS = {}
text_scrubber = TextScrubber()
file_scrubber = FileScrubber()
auditor = Auditor()
files_col = get_collection("files")


def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    if token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return SESSIONS[token]

@app.post("/api/v1/login")
def login(req: LoginRequest):
    token = str(uuid.uuid4())
    SESSIONS[token] = {"username": req.username}
    auditor.log(req.username, "login", {})
    return {"token": token}

@app.post("/api/v1/logout")
def logout(session=Depends(require_auth), authorization: str = Header(None)):
    token = authorization.split(" ", 1)[1]
    if token in SESSIONS:
        del SESSIONS[token]
    auditor.log(session["username"], "logout", {})
    return {"status": "logged_out"}

@app.post("/api/v1/scrub")
def scrub(req: ScrubRequest, session=Depends(require_auth)):
    lang = req.language if req.language else "en"
    scrub_result = text_scrubber.scrub(req.prompt, req.target_risk, lang)
    auditor.log(session["username"], "scrub", scrub_result)
    return scrub_result

## Added endpoint for text anonymization 
@app.post("/api/v1/text/anonymize")
def anonymize_text(req: ScrubRequest, session=Depends(require_auth)):
    lang = req.language if req.language else "en"
    anon_result = text_scrubber.anonymize_text(req.prompt, req.target_risk, lang)
    auditor.log(session["username"], "anonymize_text", {"target_risk": req.target_risk, "anonymized_text": anon_result}) #Indlude original text ?
    return anon_result


@app.post("/api/v1/file/scrub")
async def scrub_file(file: UploadFile = File(...), session=Depends(require_auth)):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")
    result = file_scrubber.scrub_file(file.filename, await file.read())
    auditor.log(session["username"], "file_scrub", {"filename": file.filename})
    return result

@app.get("/api/v1/file/download/{file_id}")
def download_file(file_id: str, session=Depends(require_auth)):
    try:
        record = files_col.find_one({"_id": file_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file_id")

    if not record:
        raise HTTPException(status_code=404, detail="File record not found")

    redacted_path = record.get("redacted_path")
    if not redacted_path or not os.path.exists(redacted_path):
        raise HTTPException(status_code=404, detail="File not available")

    return FileResponse(redacted_path, filename=os.path.basename(redacted_path))

@app.post("/api/v1/descrub")
def descrub(req: DescrubRequest, session=Depends(require_auth)):
    auditor.log(session["username"], "descrub", req.dict())
    return {"status": "OK"}
