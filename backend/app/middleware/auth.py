"""
JWT authentication dependency.

Resolves the current authenticated user from the Authorization: Bearer
header on every protected request (System_Architecture.md §6) — the
dependency every router in this project attaches to a protected route.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import ACCESS_TOKEN_TYPE, JWTError, decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=True)
_user_repo = UserRepository()

_INVALID_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)
_DEACTIVATED = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise _INVALID_TOKEN

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise _INVALID_TOKEN

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _INVALID_TOKEN

    user = _user_repo.get_by_id(db, user_id)
    if user is None:
        raise _INVALID_TOKEN

    # Re-checked on every request, not just at login (CLAUDE.md §12): a
    # deactivated account must fail immediately even with a still-valid,
    # unexpired token.
    if not user.is_active:
        raise _DEACTIVATED

    return user
