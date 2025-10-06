import sys
import uuid
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from api.models import LoginRequest, ScrubRequest, DescrubRequest
from scrubbers.text_scrubber import TextScrubber
from scrubbers.file_scrubber import FileScrubber
from audit.auditor import Auditor
from database.mongo import get_collection
from datetime import datetime
from pymongo import MongoClient
from fastapi.logger import logger

app = FastAPI(title="SecurePrompt API")

SESSIONS = {}
text_scrubber = TextScrubber()
file_scrubber = FileScrubber()
auditor = Auditor()

# Use the get_collection function to connect to MongoDB
users_col = get_collection("employees")
logs_col = get_collection("logs")

def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    if token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return SESSIONS[token]

# Update login route to handle MongoDB field names
@app.post("/api/v1/login")
def login(req: LoginRequest):
    logger.info("Received login request for email: %s", req.email)
    # Log the incoming request data
    print(f"Login attempt: email={req.email}, CorpKey={req.CorpKey}")

    # Check user credentials in MongoDB
    user = users_col.find_one({"email": req.email, "CorpKey": req.CorpKey})
    logger.debug("MongoDB query result: %s", user)

    if not user:
        logger.warning("Invalid login attempt for email: %s", req.email)
        # Log failed login attempt
        print(f"Login failed for email={req.email}")
        logs_col.insert_one({
            "email": req.email,
            "action": "login",
            "status": "failure",
            "timestamp": datetime.utcnow()
        })
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print(f"Received email: {req.email}, CorpKey: {req.CorpKey}")
    print(f"Query result: {user}")
    # Generate session token
    token = str(uuid.uuid4())
    SESSIONS[token] = {"email": req.email, "role": user["role"]}

    # Log successful login
    logs_col.insert_one({
        "email": req.email,
        "action": "login",
        "status": "success",
        "timestamp": datetime.utcnow()
    })

    return {
        "token": token,
        "first_name": user["First Name"],
        "last_name": user["Last Name"],
        "role": user["role"]
    }

@app.post("/api/v1/logout")
def logout(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.split(" ", 1)[1]
    if token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Log the logout action
    user = SESSIONS.pop(token)
    logs_col.insert_one({
        "e-mail": user.get("email"),
        "action": "logout",
        "status": "success",
        "timestamp": datetime.utcnow()
    })

    return {"message": "Successfully logged out"}

"""
@app.post("/api/v1/scrub")
def scrub(req: ScrubRequest, session=Depends(require_auth)):
    lang = req.language if req.language else "en"
    scrub_result = text_scrubber.anonymize_text(req.prompt, req.target_risk, lang)
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
def download_file(file_id: str):
    try:
        record = files_col.find_one({"_id": file_id})
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid file_id") from exc

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
"""