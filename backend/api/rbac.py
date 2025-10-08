from typing import List, Union
from functools import wraps
from fastapi import HTTPException, Depends

from api.routers.authentication import require_auth


def require_roles(allowed_roles: Union[str, List[str]]):
    """
    Dependency factory that creates a role-based access control dependency.

    Args:
        allowed_roles: Single role string or list of allowed roles

    Returns:
        FastAPI dependency function that validates user roles

    Usage:
        @router.get("/admin-only")
        def admin_endpoint(session=Depends(require_roles("admin"))):
            return {"message": "Admin access granted"}

        @router.get("/multi-role")
        def multi_role_endpoint(session=Depends(require_roles(["admin", "descrubber"]))):
            return {"message": "Access granted"}
    """
    # Normalize to list
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def role_checker(session=Depends(require_auth)):
        user_role = session.get("role")

        if not user_role:
            raise HTTPException(
                status_code=403, detail="Access denied: No role assigned to user"
            )

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: Required roles: {allowed_roles}, your role: {user_role}",
            )

        return session

    return role_checker


def require_admin(session=Depends(require_auth)):
    """Dependency that requires admin role"""
    return require_roles("admin")(session)


def require_descrubber_or_admin(session=Depends(require_auth)):
    """Dependency that requires descrubber or admin role"""
    return require_roles(["descrubber", "admin"])(session)


def require_auditor_or_admin(session=Depends(require_auth)):
    """Dependency that requires auditor or admin role"""
    return require_roles(["auditor", "admin"])(session)


# Common role combinations
ADMIN_ONLY = require_roles("admin")
DESCRUBBER_OR_ADMIN = require_roles(["descrubber", "admin"])
AUDITOR_OR_ADMIN = require_roles(["auditor", "admin"])
SCRUBBER_OR_ABOVE = require_roles(["scrubber", "descrubber", "auditor", "admin"])
ALL_AUTHENTICATED = require_auth  # Any authenticated user
