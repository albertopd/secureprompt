"""
Authentication Router Module

This module provides JWT-based authentication endpoints with comprehensive security features
including device identification, client tracking, and audit logging.

Features:
- JWT token-based authentication with configurable expiration
- Device and browser identification from HTTP headers
- Client IP tracking with proxy support (X-Forwarded-For, X-Real-IP)
- Comprehensive audit logging for all authentication events
- Session management with secure token storage
- Role-based access control integration

Endpoints:
- POST /auth/login - User authentication with device tracking
- POST /auth/logout - Secure session termination with audit logging
"""

from dataclasses import dataclass
import threading
import jwt
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.logger import logger

from core.config import settings
from api.models import LoginRequest, LoginResponse
from api.dependencies import get_user_manager_dep, get_log_manager_dep
from database.user_manager import UserManager
from database.log_record import LogRecord, LogRecordAction, LogRecordCategory
from database.log_manager import LogManager


# In-memory session store for demo purposes
# NOTE: In production, use Redis or database-backed session storage
SESSIONS = set()  # Set of valid JWT tokens for session management
SESSIONS_LOCK = threading.Lock()  # Thread-safe access to session store

router = APIRouter(prefix="/auth", tags=["authentication"])


@dataclass
class ClientInfo:
    """
    Data class for client identification information extracted from HTTP requests.

    This class encapsulates device, browser, and network information used for
    security monitoring and audit logging. The information helps detect suspicious
    login patterns and provides detailed forensic data for security analysis.

    Attributes:
        device_info (str): Operating system and device type (e.g., "Windows 10/11", "iPhone iOS 15.0")
        browser_info (str): Browser name and version (e.g., "Chrome 118.0", "Firefox 119.0")
        client_ip (str): Real client IP address (handles proxy headers)
        user_agent (str): Complete User-Agent string for detailed analysis
    """

    device_info: str
    browser_info: str
    client_ip: str
    user_agent: str


def extract_client_info(request: Request) -> ClientInfo:
    """
    Extract comprehensive client identification information from HTTP request headers.

    Parses HTTP headers to identify client device, browser, IP address, and other
    forensic information useful for security monitoring and audit logging.

    Features:
    - Device/OS detection: Windows, macOS, Linux, iOS, Android with version info
    - Browser identification: Chrome, Firefox, Safari, Edge with version numbers
    - Real IP detection: Handles X-Forwarded-For and X-Real-IP proxy headers
    - Complete User-Agent preservation for detailed forensic analysis

    Args:
        request (Request): FastAPI Request object containing HTTP headers

    Returns:
        ClientInfo: Structured client information including device, browser, IP, and User-Agent

    Note:
        MAC address cannot be obtained from HTTP requests due to browser security restrictions.
        This function provides the maximum identification possible through web protocols.
    """
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
    """
    Enforce authentication via Authorization header for secure API endpoints.

    This dependency validates JWT tokens in the Authorization header and extracts
    user session data for authenticated endpoints. Used for endpoints that require
    strict header-based authentication without fallback options.

    Args:
        authorization (str, optional): Authorization header in format "Bearer <token>"

    Returns:
        dict: Validated session data containing user information and permissions

    Raises:
        HTTPException (401): When authorization header is missing, malformed, or contains invalid token

    Example:
        ```python
        @router.get("/protected")
        def protected_endpoint(session=Depends(require_auth)):
            return {"user": session["email"]}
        ```
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    return _validate_token(token)


def require_auth_flexible(authorization: str = Header(None), token: str | None = None):
    """
    Flexible authentication dependency supporting both header and query parameter tokens.

    This dependency provides authentication flexibility for endpoints that need to support
    both traditional Authorization headers and query parameter tokens (e.g., file downloads
    where headers may not be easily set). Prioritizes header authentication over query parameters.

    Args:
        authorization (str, optional): Authorization header in format "Bearer <token>"
        token (str, optional): JWT token as query parameter

    Returns:
        dict: Validated session data containing user information and permissions

    Raises:
        HTTPException (401): When no valid token is provided in either location

    Example:
        ```python
        # Both work:
        # GET /download/file.txt?token=<jwt_token>
        # GET /download/file.txt with Authorization: Bearer <jwt_token>

        @router.get("/download")
        def download_file(session=Depends(require_auth_flexible)):
            return FileResponse(f"files/{session['corp_key']}/file.txt")
        ```
    """
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
    """
    Internal function to validate JWT tokens and extract user session data.

    Decodes and validates JWT tokens using the configured secret key and algorithm.
    Extracts user information from token payload for session management.

    Args:
        token (str): JWT token string to validate

    Returns:
        dict: Session data with user information including:
            - token: Original JWT token
            - corp_key: Corporate identifier
            - email: User email address
            - first_name: User first name
            - last_name: User last name
            - role: User role for RBAC

    Raises:
        HTTPException (401): When token is expired, invalid, or malformed

    Note:
        This is an internal function used by authentication dependencies.
        Not intended for direct use in route handlers.
    """
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
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    """
    Authenticate user credentials and generate JWT session token.

    This endpoint validates user credentials against the MongoDB user database,
    generates JWT tokens for successful authentication, and logs security events
    with comprehensive client identification for audit purposes.

    Security Features:
    - Credential validation with secure password hashing
    - JWT token generation with configurable expiration
    - Comprehensive audit logging with device fingerprinting
    - IP address tracking with proxy header support
    - Session management for token validity control

    Args:
        req (LoginRequest): Login credentials containing email and password
        request (Request): FastAPI request object for client identification
        user_manager (UserManager): Database manager for user operations
        log_manager (LogManager): Audit log manager for security events

    Returns:
        LoginResponse: Success status and JWT bearer token

    Raises:
        HTTPException (401): When credentials are invalid or user not found

    Example Request:
        ```json
        {
            "email": "user@company.com",
            "password": "secure_password"
        }
        ```

    Example Response:
        ```json
        {
            "status": "success",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        ```
    """
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

    client_info = extract_client_info(request)

    log_manager.add_log(
        LogRecord(
            corp_key=user["corp_key"],
            category=LogRecordCategory.SECURITY,
            action=LogRecordAction.LOGIN,
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
    log_manager: LogManager = Depends(get_log_manager_dep),
):
    """
    Terminate user session and invalidate JWT token.

    This endpoint securely logs out authenticated users by invalidating their
    JWT tokens and logging the security event with complete client information.
    Tokens are removed from the active session store to prevent further use.

    Security Features:
    - Immediate token invalidation in session store
    - Comprehensive audit logging of logout events
    - Client identification for security monitoring

    Args:
        request (Request): FastAPI request object for client identification
        session (dict): Authenticated user session data from require_auth dependency
        log_manager (LogManager): Audit log manager for security events

    Returns:
        dict: Success status confirmation

    Requires:
        Authorization: Bearer <jwt_token> header

    Example Response:
        ```json
        {
            "status": "success"
        }
        ```

    Note:
        After logout, the JWT token becomes invalid and cannot be used for
        further API requests until a new login is performed.
    """
    logger.info(f"Logout attempt with email: {session['email']}")

    with SESSIONS_LOCK:
        SESSIONS.discard(session["token"])

    client_info = extract_client_info(request)

    log_manager.add_log(
        LogRecord(
            corp_key=session["corp_key"],
            category=LogRecordCategory.SECURITY,
            action=LogRecordAction.LOGOUT,
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
