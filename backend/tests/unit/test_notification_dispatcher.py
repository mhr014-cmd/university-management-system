"""
Unit tests: app.notifications.dispatcher.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise the
Milestone 9 mandatory Notification Domain Rules directly, without a
database:
  4. Dispatch is a discrete action, always paired with its own commit
  14. A failure inside dispatch is caught and never propagates — the
      originating transaction (already committed by the caller) is
      unaffected
  15. Batch dispatch (schedule-change to a roster, fee-due to a student
      + parents) writes one notification per resolved recipient
  17. Every message is a fixed, server-side template
"""

import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.notifications import dispatcher


@pytest.fixture
def stub_repos(monkeypatch):
    notification_repo = MagicMock()
    user_repo = MagicMock()
    monkeypatch.setattr(dispatcher, "notification_repo", notification_repo)
    monkeypatch.setattr(dispatcher, "user_repo", user_repo)
    return notification_repo, user_repo


@pytest.fixture
def session():
    return MagicMock()


class TestNotifyResultPublished:
    def test_creates_notification_with_template_message(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        user_repo.list_parent_user_ids_for_student.return_value = []
        student_user_id = uuid.uuid4()

        dispatcher.notify_result_published(
            session,
            student_id=uuid.uuid4(),
            student_user_id=student_user_id,
            course_name="DB Systems",
            semester_name="Spring 2026",
        )

        notification_repo.create.assert_called_once_with(
            session,
            user_id=student_user_id,
            type="result_published",
            message="Result published: DB Systems Spring 2026",
        )
        session.commit.assert_called_once()

    def test_rule15_notifies_student_and_all_linked_parents(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        student_user_id = uuid.uuid4()
        parent_user_ids = [uuid.uuid4(), uuid.uuid4()]
        user_repo.list_parent_user_ids_for_student.return_value = parent_user_ids

        dispatcher.notify_result_published(
            session,
            student_id=uuid.uuid4(),
            student_user_id=student_user_id,
            course_name="DB Systems",
            semester_name="Spring 2026",
        )

        assert notification_repo.create.call_count == 3
        recipients = {call.kwargs["user_id"] for call in notification_repo.create.call_args_list}
        assert recipients == {student_user_id, *parent_user_ids}
        for call in notification_repo.create.call_args_list:
            assert call.kwargs["type"] == "result_published"

    def test_rule14_exception_does_not_propagate(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        user_repo.list_parent_user_ids_for_student.return_value = []
        notification_repo.create.side_effect = RuntimeError("boom")

        # Must not raise.
        dispatcher.notify_result_published(
            session, student_id=uuid.uuid4(), student_user_id=uuid.uuid4(), course_name="X", semester_name="Y"
        )
        session.rollback.assert_called_once()
        session.commit.assert_not_called()


class TestNotifySchedulteChange:
    def test_rule15_notifies_every_student_and_the_teacher(self, stub_repos, session):
        notification_repo, _user_repo = stub_repos
        student_ids = [uuid.uuid4(), uuid.uuid4()]
        teacher_id = uuid.uuid4()

        dispatcher.notify_schedule_change(
            session,
            student_user_ids=student_ids,
            teacher_user_id=teacher_id,
            course_name="DB Systems",
            room_name="Room 305",
        )

        assert notification_repo.create.call_count == 3
        recipients = {call.kwargs["user_id"] for call in notification_repo.create.call_args_list}
        assert recipients == {*student_ids, teacher_id}
        for call in notification_repo.create.call_args_list:
            assert call.kwargs["message"] == "Schedule change: DB Systems moved to Room 305"
            assert call.kwargs["type"] == "schedule_change"

    def test_cancelled_uses_cancellation_template(self, stub_repos, session):
        notification_repo, _user_repo = stub_repos
        dispatcher.notify_schedule_change(
            session,
            student_user_ids=[uuid.uuid4()],
            teacher_user_id=uuid.uuid4(),
            course_name="Networks",
            cancelled=True,
        )
        for call in notification_repo.create.call_args_list:
            assert call.kwargs["message"] == "Schedule change: Networks class cancelled"

    def test_rule14_exception_does_not_propagate(self, stub_repos, session):
        notification_repo, _user_repo = stub_repos
        notification_repo.create.side_effect = RuntimeError("boom")
        dispatcher.notify_schedule_change(
            session, student_user_ids=[uuid.uuid4()], teacher_user_id=uuid.uuid4(), course_name="X"
        )
        session.rollback.assert_called_once()

    def test_also_notifies_linked_parents_when_student_ids_given(self, stub_repos, session):
        # Gap closure (production-readiness audit): student_ids is optional
        # and additive — every pre-existing caller that never passes it
        # (see the three tests above) keeps working unchanged.
        notification_repo, user_repo = stub_repos
        student_user_id = uuid.uuid4()
        student_id = uuid.uuid4()
        teacher_user_id = uuid.uuid4()
        parent_user_ids = [uuid.uuid4()]
        user_repo.list_parent_user_ids_for_student.return_value = parent_user_ids

        dispatcher.notify_schedule_change(
            session,
            student_user_ids=[student_user_id],
            teacher_user_id=teacher_user_id,
            course_name="DB Systems",
            room_name="Room 305",
            student_ids=[student_id],
        )

        recipients = {call.kwargs["user_id"] for call in notification_repo.create.call_args_list}
        assert recipients == {student_user_id, teacher_user_id, *parent_user_ids}


class TestNotifyScheduleChangeRequestResolved:
    def test_approved_message(self, stub_repos, session):
        notification_repo, _user_repo = stub_repos
        teacher_user_id = uuid.uuid4()

        dispatcher.notify_schedule_change_request_resolved(
            session, teacher_user_id=teacher_user_id, course_name="DB Systems", decision="approved"
        )

        notification_repo.create.assert_called_once_with(
            session,
            user_id=teacher_user_id,
            type="schedule_change",
            message="Your schedule change request for DB Systems was approved.",
        )
        session.commit.assert_called_once()

    def test_rejected_message(self, stub_repos, session):
        notification_repo, _user_repo = stub_repos
        teacher_user_id = uuid.uuid4()

        dispatcher.notify_schedule_change_request_resolved(
            session, teacher_user_id=teacher_user_id, course_name="DB Systems", decision="rejected"
        )

        assert notification_repo.create.call_args.kwargs["message"] == "Your schedule change request for DB Systems was rejected."

    def test_rule14_exception_does_not_propagate(self, stub_repos, session):
        notification_repo, _user_repo = stub_repos
        notification_repo.create.side_effect = RuntimeError("boom")
        dispatcher.notify_schedule_change_request_resolved(
            session, teacher_user_id=uuid.uuid4(), course_name="X", decision="approved"
        )
        session.rollback.assert_called_once()


class TestNotifyAttendanceWarning:
    def test_creates_notification_with_template_message(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        user_repo.list_parent_user_ids_for_student.return_value = []
        student_user_id = uuid.uuid4()
        dispatcher.notify_attendance_warning(
            session, student_id=uuid.uuid4(), student_user_id=student_user_id, course_name="Networks"
        )
        notification_repo.create.assert_called_once_with(
            session, user_id=student_user_id, type="attendance_warning", message="Attendance warning: Networks below 80%"
        )

    def test_rule15_notifies_student_and_all_linked_parents(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        student_id = uuid.uuid4()
        student_user_id = uuid.uuid4()
        parent_user_ids = [uuid.uuid4(), uuid.uuid4()]
        user_repo.list_parent_user_ids_for_student.return_value = parent_user_ids

        dispatcher.notify_attendance_warning(
            session, student_id=student_id, student_user_id=student_user_id, course_name="Networks"
        )

        assert notification_repo.create.call_count == 3
        recipients = {call.kwargs["user_id"] for call in notification_repo.create.call_args_list}
        assert recipients == {student_user_id, *parent_user_ids}
        for call in notification_repo.create.call_args_list:
            assert call.kwargs["type"] == "attendance_warning"

    def test_rule14_exception_does_not_propagate(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        user_repo.list_parent_user_ids_for_student.return_value = []
        notification_repo.create.side_effect = RuntimeError("boom")
        dispatcher.notify_attendance_warning(
            session, student_id=uuid.uuid4(), student_user_id=uuid.uuid4(), course_name="X"
        )
        session.rollback.assert_called_once()
        session.commit.assert_not_called()


class TestNotifyFeeDue:
    def test_rule15_notifies_student_and_all_linked_parents(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        student_id = uuid.uuid4()
        student_user_id = uuid.uuid4()
        parent_user_ids = [uuid.uuid4(), uuid.uuid4()]
        user_repo.list_parent_user_ids_for_student.return_value = parent_user_ids

        dispatcher.notify_fee_due(
            session, student_id=student_id, student_user_id=student_user_id, amount=5000.0, due_date=date(2026, 7, 15)
        )

        assert notification_repo.create.call_count == 3
        recipients = {call.kwargs["user_id"] for call in notification_repo.create.call_args_list}
        assert recipients == {student_user_id, *parent_user_ids}
        for call in notification_repo.create.call_args_list:
            assert call.kwargs["message"] == "Fee due: 5000.00 due 2026-07-15"
            assert call.kwargs["type"] == "fee_due"

    def test_no_linked_parents_notifies_student_only(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        user_repo.list_parent_user_ids_for_student.return_value = []
        dispatcher.notify_fee_due(
            session, student_id=uuid.uuid4(), student_user_id=uuid.uuid4(), amount=100.0, due_date=date(2026, 1, 1)
        )
        assert notification_repo.create.call_count == 1

    def test_rule14_exception_does_not_propagate(self, stub_repos, session):
        notification_repo, user_repo = stub_repos
        user_repo.list_parent_user_ids_for_student.return_value = []
        notification_repo.create.side_effect = RuntimeError("boom")
        dispatcher.notify_fee_due(
            session, student_id=uuid.uuid4(), student_user_id=uuid.uuid4(), amount=1.0, due_date=date(2026, 1, 1)
        )
        session.rollback.assert_called_once()
