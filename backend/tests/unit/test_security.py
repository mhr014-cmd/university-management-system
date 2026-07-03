"""
Unit tests: app.core.security (password hashing, JWT encode/decode).

No database access — pure utility layer, per CLAUDE.md §10.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    ACCESS_TOKEN_TYPE,
    JWTError,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_verifiable_hash():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct-horse-battery-staple")
    assert not verify_password("wrong-password", hashed)


def test_hash_password_is_salted_and_nondeterministic():
    first = hash_password("same-password")
    second = hash_password("same-password")
    assert first != second


def test_create_access_token_has_expected_claims():
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "student")
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "student"
    assert payload["type"] == ACCESS_TOKEN_TYPE


def test_create_refresh_token_has_expected_claims_and_matches_returned_jti():
    user_id = uuid.uuid4()
    token, jti, expires_at = create_refresh_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["jti"] == jti
    assert payload["type"] == REFRESH_TOKEN_TYPE
    assert expires_at > datetime.now(timezone.utc)


def test_decode_token_raises_on_malformed_token():
    with pytest.raises(JWTError):
        decode_token("not-a-real-token")


def test_decode_token_raises_on_expired_token():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": str(uuid.uuid4()),
        "type": ACCESS_TOKEN_TYPE,
        "iat": now - timedelta(minutes=30),
        "exp": now - timedelta(minutes=15),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(JWTError):
        decode_token(expired_token)


def test_decode_token_raises_on_bad_signature():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    token = jwt.encode(payload, "a-different-secret-key", algorithm=settings.jwt_algorithm)
    with pytest.raises(JWTError):
        decode_token(token)
