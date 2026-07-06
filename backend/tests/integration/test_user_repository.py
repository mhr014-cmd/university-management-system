"""
Integration tests: app.repositories.user_repository.UserRepository —
transaction boundaries only (requires a real, disposable database — see
tests/conftest.py).

V1.1 stabilization fix: `set_refresh_token`, `clear_refresh_token`, and
`update_password_hash` previously called `session.commit()` directly,
contradicting this repository's own docstring (transaction ownership
belongs to the service layer, per CLAUDE.md §6). These tests run against
a real (disposable, SAVEPOINT-isolated) database session and assert the
repository now only `flush()`es — never commits — leaving the caller free
to roll back the whole operation.
"""

from unittest.mock import MagicMock

from tests.conftest import requires_test_database

from app.repositories.user_repository import UserRepository

pytestmark = requires_test_database

repo = UserRepository()


def _spy_on_commit(session):
    """Wraps the real session.commit so calls are counted without losing
    the underlying behavior, in case anything downstream still needs it."""
    spy = MagicMock(wraps=session.commit)
    session.commit = spy
    return spy


class TestSetRefreshToken:
    def test_flushes_but_does_not_commit(self, db_session, make_user):
        user = make_user("student@example.com", "correct-password", "student")
        commit_spy = _spy_on_commit(db_session)

        repo.set_refresh_token(db_session, user, "some-jti", user.created_at)

        commit_spy.assert_not_called()
        # flush() alone must be enough for the caller to see the write
        # within the same transaction.
        assert user.current_refresh_token_jti == "some-jti"


class TestClearRefreshToken:
    def test_flushes_but_does_not_commit(self, db_session, make_user):
        user = make_user("student2@example.com", "correct-password", "student")
        repo.set_refresh_token(db_session, user, "some-jti", user.created_at)
        commit_spy = _spy_on_commit(db_session)

        repo.clear_refresh_token(db_session, user)

        commit_spy.assert_not_called()
        assert user.current_refresh_token_jti is None


class TestUpdatePasswordHash:
    def test_flushes_but_does_not_commit(self, db_session, make_user):
        user = make_user("student3@example.com", "correct-password", "student")
        commit_spy = _spy_on_commit(db_session)

        repo.update_password_hash(db_session, user, "a-new-hash")

        commit_spy.assert_not_called()
        assert user.password_hash == "a-new-hash"
