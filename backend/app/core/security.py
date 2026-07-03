"""
Password hashing and JWT encode/decode utilities.

Pure utility layer — no database access, no HTTP-level error handling.
Callers (app/services/auth_service.py, app/middleware/auth.py) translate
failures into the appropriate HTTP responses.
"""

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    # bcrypt directly, not passlib's CryptContext: passlib 1.7.4 (its final
    # release — the project is unmaintained) probes the bcrypt backend via a
    # `bcrypt.__about__.__version__` attribute that modern bcrypt (4.1+)
    # removed, crashing on the very first hash call. bcrypt is what
    # System_Architecture.md §11 actually names as the required algorithm;
    # passlib was only ever our own wrapper choice, not a stack requirement.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str, datetime]:
    """Returns (encoded_token, jti, expires_at) — the caller persists jti/expires_at
    to user.current_refresh_token_jti/refresh_token_expires_at (Database_Design.md
    §6.1 Milestone 2 design note) so rotation/logout can be enforced server-side."""
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": REFRESH_TOKEN_TYPE,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_token(token: str) -> dict:
    """Raises jose.JWTError if the token is malformed, has an invalid signature,
    or is expired. Does not check token type or DB-side revocation — callers
    that need a specific type (access vs. refresh) or revocation check do so
    themselves against the decoded payload."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = [
    "JWTError",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "ACCESS_TOKEN_TYPE",
    "REFRESH_TOKEN_TYPE",
]
