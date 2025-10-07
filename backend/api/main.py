import os
import threading
import jwt
from pathlib import Path
from datetime import datetime, timezone
from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.logger import logger
from fastapi.responses import FileResponse
from pymongo import MongoClient
from core.config import settings
from api.models import LoginRequest, LoginResponse, ScrubRequest, DescrubRequest
from scrubbers.text_scrubber import TextScrubber
from scrubbers.file_scrubber import FileScrubber
from database.user_manager import UserManager
from database.audit_manager import AuditManager
from fastapi import Depends


# In-memory demo session store (see notes below)
SESSIONS = set()
SESSIONS_LOCK = threading.Lock()


# Lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create one MongoClient and store it on app.state for connection pooling and efficient resource usage
    app.state.mongo_client = MongoClient(settings.MONGO_URI)

    try:
        # Yield control back to FastAPI to start serving requests
        yield
    finally:
        # Cleanup at shutdown
        try:
            app.state.mongo_client.close()
        except Exception:
            logger.error("Error closing MongoDB client", exc_info=True)


# Create app with lifespan
app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)


# Deppendencies
def get_mongo_client_dep() -> MongoClient:
    return app.state.mongo_client

def get_user_manager_dep(
    client: MongoClient = Depends(get_mongo_client_dep),
) -> UserManager:
    return UserManager(client)

def get_audit_manager_dep(
    client: MongoClient = Depends(get_mongo_client_dep),
) -> AuditManager:
    return AuditManager(client)

def get_text_scrubber_dep() -> TextScrubber:
    return TextScrubber()

def get_file_scrubber_dep() -> FileScrubber:
    return FileScrubber()


# Helper to enforce authentication
def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
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
        "role": payload.get("role"),
    }


@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {"status": "healthy"}


@app.post(f"{settings.API_V1_STR}/auth/login")
def login(
    req: LoginRequest,
    user_manager: UserManager = Depends(get_user_manager_dep),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
):
    logger.info("Login attempt with email: %s", req.email)

    user = user_manager.check_user_credentials(req.email, req.password)

    if not user:
        logger.warning("Invalid login attempt with email: %s", req.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT token
    payload = {
        "corp_key": user["corp_key"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc).timestamp()
        + settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Store session in-memory (demo only - not for production use)
    with SESSIONS_LOCK:
        SESSIONS.add(token)

    audit_manager.log(
        user["corp_key"], 
        "login", 
        {
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": user["role"]
        }
    )

    return LoginResponse(status="success", token=token)


@app.post(f"{settings.API_V1_STR}/auth/logout")
def logout(
    session=Depends(require_auth),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
):
    logger.info(f"Logout attempt with email: {session['email']}")

    with SESSIONS_LOCK:
        SESSIONS.discard(session["token"])

    audit_manager.log(
        session["corp_key"], 
        "logout", 
        {
            "email": session["email"],
            "first_name": session["first_name"],
            "last_name": session["last_name"],
            "role": session["role"]
        }
    )

    return {"status": "success"}


@app.post(f"{settings.API_V1_STR}/scrub")
def scrub(
    req: ScrubRequest,
    session=Depends(require_auth),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
    text_scrubber: TextScrubber = Depends(get_text_scrubber_dep)
):
    lang = req.language if req.language else "en"
    target_risk = req.target_risk if req.target_risk else "C4"
    scrub_result = text_scrubber.anonymize_text(req.prompt, target_risk, lang)

    audits_details = {
        "language": lang,
        "target_risk": target_risk,
        "original_text": req.prompt,
    }
    audits_details.update(scrub_result)

    audit_manager.log(session["corp_key"], "scrub", audits_details)

    return scrub_result


## Added endpoint for text anonymization
@app.post(f"{settings.API_V1_STR}/text/anonymize")
def anonymize_text(
    req: ScrubRequest,
    session=Depends(require_auth),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
    text_scrubber: TextScrubber = Depends(get_text_scrubber_dep)
):
    lang = req.language if req.language else "en"
    anon_result = text_scrubber.anonymize_text(req.prompt, req.target_risk, lang)

    audit_manager.log(
        session["corp_key"],
        "anonymize_text",
        {"target_risk": req.target_risk, "anonymized_text": anon_result},
    )  # Include original text ?
    return anon_result


@app.post(f"{settings.API_V1_STR}/file/scrub")
async def scrub_file(
    file: UploadFile = File(...),
    session=Depends(require_auth),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
    file_scrubber: FileScrubber = Depends(get_file_scrubber_dep)
):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")

    result = file_scrubber.scrub_file(file.filename, await file.read())

    audit_manager.log(session["corp_key"], "file_scrub", {"filename": file.filename})

    return result


@app.get(f"{settings.API_V1_STR}/file/download/{{file_id}}")
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


@app.post(f"{settings.API_V1_STR}/descrub")
def descrub(
    req: DescrubRequest,
    session=Depends(require_auth),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
):
    audit_manager.log(session["corp_key"], "descrub", req.model_dump())

    return {"status": "OK"}
