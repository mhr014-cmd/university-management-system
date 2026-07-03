"""
Unit tests: app.services.auth_service.AuthService.

UserRepository is stubbed (per CLAUDE.md §10 — "repositories mocked/stubbed")
so these tests exercise business rules only: BR-006 (deactivated account
fails login and refresh), VR-002 (change-password current-password check),
and refresh-token rotation/reuse detection.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.security import create_refresh_token, hash_password
from app.models.user import User
from app.schemas.auth import PasswordChangeRequest
from app.services import auth_service as auth_service_module
from app.services.auth_service import AuthService


def make_user(**overrides) -> User:
    defaults = dict(
        id=uuid.uuid4(),
        email="student@example.com",
        password_hash=hash_password("correct-password"),
        role="student",
        is_active=True,
        current_refresh_token_jti=None,
        refresh_token_expires_at=None,
    )
    defaults.update(overrides)
    return User(**defaults)


@pytest.fixture
def stub_repo(monkeypatch):
    repo = MagicMock()
    monkeypatch.setattr(auth_service_module, "user_repo", repo)
    return repo


@pytest.fixture
def service():
    return AuthService()


@pytest.fixture
def session():
    return MagicMock()


class TestLogin:
    def test_success_issues_tokens_and_persists_refresh_jti(self, service, stub_repo, session):
        user = make_user()
        stub_repo.get_by_email.return_value = user

        access_token, refresh_token, returned_user = service.login(session, user.email, "correct-password")

        assert access_token
        assert refresh_token
        assert returned_user is user
        stub_repo.set_refresh_token.assert_called_once()
        called_user, jti, expires_at = stub_repo.set_refresh_token.call_args.args[1:]
        assert called_user is user
        assert isinstance(jti, str)
        assert expires_at > datetime.now(timezone.utc)

    def test_unknown_email_raises_401(self, service, stub_repo, session):
        stub_repo.get_by_email.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.login(session, "nobody@example.com", "whatever")
        assert exc.value.status_code == 401

    def test_wrong_password_raises_401(self, service, stub_repo, session):
        stub_repo.get_by_email.return_value = make_user()
        with pytest.raises(HTTPException) as exc:
            service.login(session, "student@example.com", "wrong-password")
        assert exc.value.status_code == 401

    def test_deactivated_account_raises_403_even_with_correct_password(self, service, stub_repo, session):
        # BR-006: a deactivated account must fail login even with correct credentials.
        stub_repo.get_by_email.return_value = make_user(is_active=False)
        with pytest.raises(HTTPException) as exc:
            service.login(session, "student@example.com", "correct-password")
        assert exc.value.status_code == 403
        stub_repo.set_refresh_token.assert_not_called()


class TestRefresh:
    def test_success_rotates_token_and_persists_new_jti(self, service, stub_repo, session):
        user = make_user()
        token, jti, expires_at = create_refresh_token(user.id)
        user.current_refresh_token_jti = jti
        user.refresh_token_expires_at = expires_at
        stub_repo.get_by_id.return_value = user

        new_access_token, new_refresh_token = service.refresh(session, token)

        assert new_access_token
        assert new_refresh_token != token
        stub_repo.set_refresh_token.assert_called_once()

    def test_access_token_rejected_as_refresh_token(self, service, stub_repo, session):
        from app.core.security import create_access_token

        access_token = create_access_token(uuid.uuid4(), "student")
        with pytest.raises(HTTPException) as exc:
            service.refresh(session, access_token)
        assert exc.value.status_code == 401
        stub_repo.get_by_id.assert_not_called()

    def test_malformed_token_raises_401(self, service, stub_repo, session):
        with pytest.raises(HTTPException) as exc:
            service.refresh(session, "not-a-real-token")
        assert exc.value.status_code == 401

    def test_unknown_user_raises_401(self, service, stub_repo, session):
        token, _jti, _expires_at = create_refresh_token(uuid.uuid4())
        stub_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.refresh(session, token)
        assert exc.value.status_code == 401

    def test_deactivated_user_raises_401(self, service, stub_repo, session):
        user = make_user(is_active=False)
        token, jti, expires_at = create_refresh_token(user.id)
        user.current_refresh_token_jti = jti
        user.refresh_token_expires_at = expires_at
        stub_repo.get_by_id.return_value = user
        with pytest.raises(HTTPException) as exc:
            service.refresh(session, token)
        assert exc.value.status_code == 401

    def test_jti_mismatch_raises_401(self, service, stub_repo, session):
        # Reuse-detection: token was already rotated (or session was logged
        # out), so the stored jti no longer matches the presented token's jti.
        user = make_user()
        token, _issued_jti, expires_at = create_refresh_token(user.id)
        user.current_refresh_token_jti = "a-different-jti-than-the-one-presented"
        user.refresh_token_expires_at = expires_at
        stub_repo.get_by_id.return_value = user
        with pytest.raises(HTTPException) as exc:
            service.refresh(session, token)
        assert exc.value.status_code == 401

    def test_expired_refresh_session_raises_401(self, service, stub_repo, session):
        user = make_user()
        token, jti, _expires_at = create_refresh_token(user.id)
        user.current_refresh_token_jti = jti
        user.refresh_token_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        stub_repo.get_by_id.return_value = user
        with pytest.raises(HTTPException) as exc:
            service.refresh(session, token)
        assert exc.value.status_code == 401


class TestLogout:
    def test_logout_clears_refresh_token(self, service, stub_repo, session):
        user = make_user()
        service.logout(session, user)
        stub_repo.clear_refresh_token.assert_called_once_with(session, user)


class TestChangePassword:
    def test_wrong_current_password_raises_401(self, service, stub_repo, session):
        user = make_user()
        payload = PasswordChangeRequest(current_password="wrong-password", new_password="new-password-123")
        with pytest.raises(HTTPException) as exc:
            service.change_password(session, user, payload)
        assert exc.value.status_code == 401
        stub_repo.update_password_hash.assert_not_called()

    def test_success_updates_password_hash(self, service, stub_repo, session):
        user = make_user()
        payload = PasswordChangeRequest(current_password="correct-password", new_password="new-password-123")
        service.change_password(session, user, payload)
        stub_repo.update_password_hash.assert_called_once()
        called_user, new_hash = stub_repo.update_password_hash.call_args.args[1:]
        assert called_user is user
        assert new_hash != "new-password-123"

    def test_new_password_equal_to_current_rejected_at_schema_layer(self):
        # VR-002: enforced by PasswordChangeRequest's own model_validator,
        # before the service method is ever reached.
        with pytest.raises(ValueError):
            PasswordChangeRequest(current_password="same-password", new_password="same-password")
