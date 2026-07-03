"""
Role-based access control dependency.

Enforces NFR-001 (role-based access control at the API layer, not only
the UI) via dependency injection on protected routes, per
System_Architecture.md §6. Role-only checks are insufficient for
`/me`-scoped and parent-linked endpoints — those need an additional
ownership check in the service layer (not this module), per CLAUDE.md §6.
"""

from fastapi import Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.models.user import User


def require_roles(*allowed_roles: str):
    def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return _check_role
