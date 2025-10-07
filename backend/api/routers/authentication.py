from dataclasses import dataclass
import threading
import jwt
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.logger import logger

from core.config import settings
from api.models import LoginRequest, LoginResponse
from api.dependencies import get_user_manager_dep, get_audit_manager_dep
from database.user_manager import UserManager
from database.audit_manager import AuditManager, AuditLog


# In-memory demo session store (see notes below)
SESSIONS = set()
SESSIONS_LOCK = threading.Lock()

router = APIRouter(prefix="/auth", tags=["authentication"])


@dataclass
class ClientInfo:
    device_info: str
    browser_info: str
    client_ip: str
    user_agent: str


def extract_client_info(request: Request) -> ClientInfo:
    """Extract client identification information from HTTP request"""
    headers = request.headers

    # Extract User-Agent for browser identification
    user_agent = headers.get("user-agent", "Unknown")

    # Parse browser information
    browser_info = "Unknown"
    if "Chrome" in user_agent:
        chrome_match = re.search(r"Chrome/(\d+\.\d+)", user_agent)
        browser_info = f"Chrome {chrome_match.group(1) if chrome_match else 'Unknown'}"
    elif "Firefox" in user_agent:
        firefox_match = re.search(r"Firefox/(\d+\.\d+)", user_agent)
        browser_info = (
            f"Firefox {firefox_match.group(1) if firefox_match else 'Unknown'}"
        )
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        safari_match = re.search(r"Version/(\d+\.\d+)", user_agent)
        browser_info = f"Safari {safari_match.group(1) if safari_match else 'Unknown'}"
    elif "Edge" in user_agent:
        edge_match = re.search(r"Edg/(\d+\.\d+)", user_agent)
        browser_info = f"Edge {edge_match.group(1) if edge_match else 'Unknown'}"

    # Extract device/OS information
    device_info = "Unknown"
    if "Windows" in user_agent:
        if "Windows NT 10" in user_agent:
            device_info = "Windows 10/11"
        elif "Windows NT 6" in user_agent:
            device_info = "Windows 7/8"
        else:
            device_info = "Windows"
    elif "Macintosh" in user_agent:
        mac_match = re.search(r"Mac OS X (\d+_\d+)", user_agent)
        device_info = (
            f"macOS {mac_match.group(1).replace('_', '.') if mac_match else 'Unknown'}"
        )
    elif "Linux" in user_agent:
        device_info = "Linux"
    elif "iPhone" in user_agent:
        ios_match = re.search(r"OS (\d+_\d+)", user_agent)
        device_info = f"iPhone iOS {ios_match.group(1).replace('_', '.') if ios_match else 'Unknown'}"
    elif "Android" in user_agent:
        android_match = re.search(r"Android (\d+\.\d+)", user_agent)
        device_info = (
            f"Android {android_match.group(1) if android_match else 'Unknown'}"
        )

    # Get client IP (consider X-Forwarded-For for proxy/load balancer scenarios)
    client_ip = (
        headers.get("x-forwarded-for", "").split(",")[0].strip()
        or headers.get("x-real-ip", "")
        or str(request.client.host if request.client else "Unknown")
    )

    return ClientInfo(device_info, browser_info, client_ip, user_agent)


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
    request: Request,
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

    # Extract client identification information
    client_info = extract_client_info(request)

    audit_manager.log(
        AuditLog(
            corp_key=user["corp_key"],
            category="security",
            action="login",
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
            details={
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"],
            },
        )
    )

    return LoginResponse(status="success", token=token)


@router.post("/logout")
def logout(
    request: Request,
    session=Depends(require_auth),
    audit_manager: AuditManager = Depends(get_audit_manager_dep),
):
    """User logout endpoint"""
    logger.info(f"Logout attempt with email: {session['email']}")

    with SESSIONS_LOCK:
        SESSIONS.discard(session["token"])

    client_info = extract_client_info(request)

    audit_manager.log(
        AuditLog(
            corp_key=session["corp_key"],
            category="security",
            action="logout",
            device_info=client_info.device_info,
            browser_info=client_info.browser_info,
            client_ip=client_info.client_ip,
            user_agent=client_info.user_agent,
            details={
                "email": session["email"],
                "first_name": session["first_name"],
                "last_name": session["last_name"],
                "role": session["role"],
            },
        )
    )

    return {"status": "success"}
