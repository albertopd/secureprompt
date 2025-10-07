import threading
import jwt
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.logger import logger

from core.config import settings
from api.models import LoginRequest, LoginResponse
from api.dependencies import get_user_manager_dep, get_audit_manager_dep
from database.user_manager import UserManager
from database.audit_manager import AuditManager


# In-memory demo session store (see notes below)
SESSIONS = set()
SESSIONS_LOCK = threading.Lock()

router = APIRouter(prefix="/auth", tags=["authentication"])


def require_auth(authorization: str = Header(None)):
    """Helper to enforce authentication via Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    return _validate_token(token)


def require_auth_flexible(authorization: str = Header(None), token: str | None = None):
    """Helper to enforce authentication via Authorization header OR query parameter"""
    # Try header first, then query parameter
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ", 1)[1]
    elif token:
        auth_token = token

    if not auth_token:
        raise HTTPException(status_code=401, detail="Unauthorized - token required")

    return _validate_token(auth_token)


def _validate_token(token: str):
    """Validate JWT token and return user session data"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
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


@router.post("/login", response_model=LoginResponse)
def login(
    req: LoginRequest,
    user_manager: UserManager = Depends(get_user_manager_dep),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
):
    """User login endpoint"""
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

    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

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
            "role": user["role"],
        },
    )

    return LoginResponse(status="success", token=token)


@router.post("/logout")
def logout(
    session=Depends(require_auth),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
):
    """User logout endpoint"""
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
            "role": session["role"],
        },
    )

    return {"status": "success"}
