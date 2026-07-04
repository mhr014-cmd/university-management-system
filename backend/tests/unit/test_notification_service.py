"""
Unit tests: app.services.notification_service.NotificationService.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise the
Milestone 9 mandatory Notification Domain Rules directly, without a
database: ownership scoping (Rules 6-9), idempotent mark-as-read
(Rule 11).
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.notification import Notification
from app.models.user import User
from app.services import notification_service as notification_service_module
from app.services.notification_service import NotificationService


def make_notification(**overrides) -> Notification:
    defaults = dict(
        id=uuid.uuid4(), user_id=uuid.uuid4(), type="fee_due", message="Fee due: 100.00 due 2026-01-01",
        is_read=False, created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Notification(**defaults)


@pytest.fixture
def stub_repos(monkeypatch):
    notification_repo = MagicMock()
    monkeypatch.setattr(notification_service_module, "notification_repo", notification_repo)
    return notification_repo


@pytest.fixture
def service():
    return NotificationService()


@pytest.fixture
def session():
    return MagicMock()


def _user(user_id=None):
    return User(id=user_id or uuid.uuid4(), email="u@example.com", role="student")


class TestListNotifications:
    def test_scoped_to_callers_own_user_id(self, service, stub_repos, session):
        notification_repo = stub_repos
        user = _user()
        notification_repo.list_for_user.return_value = ([], 0)
        notification_repo.count_unread.return_value = 0

        service.list_notifications(session, user, is_read=None, page=1, page_size=20)

        notification_repo.list_for_user.assert_called_once_with(
            session, user.id, is_read=None, page=1, page_size=20
        )
        notification_repo.count_unread.assert_called_once_with(session, user.id)

    def test_returns_unread_count_and_total(self, service, stub_repos, session):
        notification_repo = stub_repos
        user = _user()
        notification_repo.list_for_user.return_value = ([make_notification(user_id=user.id)], 5)
        notification_repo.count_unread.return_value = 3

        result = service.list_notifications(session, user, is_read=None, page=1, page_size=20)
        assert result.total == 5
        assert result.unread_count == 3
        assert len(result.items) == 1


class TestMarkAsRead:
    def test_not_found_raises_404(self, service, stub_repos, session):
        notification_repo = stub_repos
        notification_repo.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.mark_as_read(session, _user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_rule6_other_users_notification_hidden_as_404(self, service, stub_repos, session):
        notification_repo = stub_repos
        notification = make_notification(user_id=uuid.uuid4())
        notification_repo.get.return_value = notification
        with pytest.raises(HTTPException) as exc:
            service.mark_as_read(session, _user(), notification.id)
        assert exc.value.status_code == 404
        notification_repo.mark_read.assert_not_called()

    def test_marks_unread_notification_as_read(self, service, stub_repos, session):
        notification_repo = stub_repos
        user = _user()
        notification = make_notification(user_id=user.id, is_read=False)
        notification_repo.get.return_value = notification

        def mark_read_side_effect(_session, n):
            n.is_read = True

        notification_repo.mark_read.side_effect = mark_read_side_effect

        result = service.mark_as_read(session, user, notification.id)
        assert result.is_read is True
        notification_repo.mark_read.assert_called_once()
        session.commit.assert_called_once()

    def test_rule11_already_read_is_idempotent_no_op(self, service, stub_repos, session):
        notification_repo = stub_repos
        user = _user()
        notification = make_notification(user_id=user.id, is_read=True)
        notification_repo.get.return_value = notification

        result = service.mark_as_read(session, user, notification.id)
        assert result.is_read is True
        notification_repo.mark_read.assert_not_called()
        session.commit.assert_not_called()
