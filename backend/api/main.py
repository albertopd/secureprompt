import os
import jwt
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from api.models import LoginRequest, ScrubRequest, DescrubRequest
from scrubbers.text_scrubber import TextScrubber
from scrubbers.file_scrubber import FileScrubber
from database.users_db import UsersDatabase
from database.audits_db import AuditsDatabase
from pathlib import Path
from datetime import datetime, timezone
from fastapi.logger import logger


TOKEN_JWT_SECRET = os.getenv("JWT_SECRET", "secrete-should-be-long-and-random")
TOKEN_EXPIRY_SECONDS = int(os.environ.get("TOKEN_EXPIRY_SECONDS", 3600))  # 1 hour default
SESSIONS = []  # In-memory session store for demo purposes


app = FastAPI(title="SecurePrompt API")
text_scrubber = TextScrubber()
file_scrubber = FileScrubber()


def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, TOKEN_JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "token": token,
        "corp_key": payload.get("corp_key"),
        "email": payload.get("email"),
        "first_name": payload.get("first_name"),
        "last_name": payload.get("last_name"),
        "role": payload.get("role")
    }


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/login")
def login(req: LoginRequest):
    logger.info(f"Login attempt: email={req.email}")

    # Check user credentials in MongoDB
    with UsersDatabase() as users_db:
        user = users_db.check_user_credentials(req.email, req.password)

        if not user:
            logger.warning("Invalid login attempt for email: %s", req.email)
            raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT token
    payload = {
        "corp_key": user["corp_key"],
        "email": req.email,
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc).timestamp() + TOKEN_EXPIRY_SECONDS
    }

    token = jwt.encode(payload, TOKEN_JWT_SECRET, algorithm="HS256")
    SESSIONS.append(token)

    with AuditsDatabase() as audits_db:
        audits_db.log(user["corp_key"], "login", {"status": "success"})

    return {
        "status": "success",
        "token": token
    }


@app.post("/api/v1/logout")
def logout(session=Depends(require_auth)):
    logger.info(f"Logout attempt: email={session['email']}")

    SESSIONS.remove(session["token"])

    with AuditsDatabase() as audits_db:
        audits_db.log(session["corp_key"], "logout", {"status": "success"})

    return {"status": "success"}


@app.post("/api/v1/scrub")
def scrub(req: ScrubRequest, session=Depends(require_auth)):
    lang = req.language if req.language else "en"
    target_risk = req.target_risk if req.target_risk else "C4"
    scrub_result = text_scrubber.anonymize_text(req.prompt, target_risk, lang)

    audits_details = {
        "language": lang,
        "target_risk": target_risk,
        "original_text": req.prompt
    }
    audits_details.update(scrub_result)

    with AuditsDatabase() as audits_db:
        audits_db.log(session["corp_key"], "scrub", audits_details)

    return scrub_result


## Added endpoint for text anonymization
@app.post("/api/v1/text/anonymize")
def anonymize_text(req: ScrubRequest, session=Depends(require_auth)):
    lang = req.language if req.language else "en"
    anon_result = text_scrubber.anonymize_text(req.prompt, req.target_risk, lang)

    with AuditsDatabase() as auditor:
        auditor.log(
            session["corp_key"],
            "anonymize_text",
            {"target_risk": req.target_risk, "anonymized_text": anon_result},
        )  # Include original text ?
    return anon_result


@app.post("/api/v1/file/scrub")
async def scrub_file(file: UploadFile = File(...), session=Depends(require_auth)):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")
    result = file_scrubber.scrub_file(file.filename, await file.read())

    with AuditsDatabase() as audits_db:
        audits_db.log(session["corp_key"], "file_scrub", {"filename": file.filename})

    return result


@app.get("/api/v1/file/download/{file_id}")
def download_file(file_id: str):
    # try:
    #     record = files_col.find_one({"_id": file_id})
    # except Exception:
    #     raise HTTPException(status_code=400, detail="Invalid file_id")

    # if not record:
    #     raise HTTPException(status_code=404, detail="File record not found")

    # redacted_path = record.get("redacted_path")

    redacted_dir = Path("C:/tmp/secureprompt_files")
    redacted_path = redacted_dir / f"redacted_{file_id}"

    if not os.path.exists(redacted_path):
        raise HTTPException(status_code=404, detail="File not available")

    return FileResponse(redacted_path, filename=os.path.basename(redacted_path))


@app.post("/api/v1/descrub")
def descrub(req: DescrubRequest, session=Depends(require_auth)):
    with AuditsDatabase() as audits_db:
        audits_db.log(session["corp_key"], "descrub", req.model_dump())

    return {"status": "OK"}
