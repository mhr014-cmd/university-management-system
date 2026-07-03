"""
Business logic service: auth.

Owns the login / token-refresh / logout / password-change workflows and
all auth-related business rules (VR-001, VR-002, BR-006 deactivation
check). Calls UserRepository, never the ORM session directly, per
CLAUDE.md §6.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    JWTError,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import PasswordChangeRequest

user_repo = UserRepository()

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
)
_ACCOUNT_DEACTIVATED = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
_INVALID_REFRESH_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid, expired, or revoked"
)


class AuthService:
    def login(self, session: Session, email: str, password: str) -> tuple[str, str, User]:
        user = user_repo.get_by_email(session, email)
        if user is None or not verify_password(password, user.password_hash):
            raise _INVALID_CREDENTIALS
        if not user.is_active:
            # BR-006: a deactivated account must fail login even with correct credentials.
            raise _ACCOUNT_DEACTIVATED

        access_token = create_access_token(user.id, user.role)
        refresh_token, jti, expires_at = create_refresh_token(user.id)
        user_repo.set_refresh_token(session, user, jti, expires_at)
        return access_token, refresh_token, user

    def refresh(self, session: Session, refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise _INVALID_REFRESH_TOKEN

        if payload.get("type") != REFRESH_TOKEN_TYPE:
            raise _INVALID_REFRESH_TOKEN

        try:
            # JWT claims are always strings — the "sub" claim must be
            # explicitly converted back to a UUID rather than relying on
            # implicit coercion at the ORM layer, which the UUID(as_uuid=True)
            # column type does not guarantee for a raw string primary key.
            subject_id = uuid.UUID(payload["sub"])
        except (KeyError, ValueError):
            raise _INVALID_REFRESH_TOKEN

        user = user_repo.get_by_id(session, subject_id)
        if user is None or not user.is_active:
            raise _INVALID_REFRESH_TOKEN

        if user.current_refresh_token_jti != payload.get("jti"):
            # Token was already rotated (reused) or the session was logged out.
            raise _INVALID_REFRESH_TOKEN

        if user.refresh_token_expires_at is None or user.refresh_token_expires_at < datetime.now(timezone.utc):
            raise _INVALID_REFRESH_TOKEN

        new_access_token = create_access_token(user.id, user.role)
        new_refresh_token, new_jti, new_expires_at = create_refresh_token(user.id)
        user_repo.set_refresh_token(session, user, new_jti, new_expires_at)
        return new_access_token, new_refresh_token

    def logout(self, session: Session, user: User) -> None:
        user_repo.clear_refresh_token(session, user)

    def change_password(self, session: Session, user: User, payload: PasswordChangeRequest) -> None:
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
        # payload's own model_validator already rejects new_password == current_password
        # (VR-002) at the schema layer, before this service method is ever called.
        user_repo.update_password_hash(session, user, hash_password(payload.new_password))
