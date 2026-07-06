"""
Unit tests: app.services.schedule_service.ScheduleService.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise
business rules only: VR-007 (start < end), BR-005 (overlap conflict
detection — including overlapping-but-different-start-time cases the DB
UniqueConstraint alone would miss), BR-004 (a Teacher may only request a
change to their own schedule entry), and the change-request resolve
workflow (idempotency, approve applying the change, reject not).
"""

import uuid
from datetime import datetime, time, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.schedule_change_request import ScheduleChangeRequest
from app.models.schedule_entry import ScheduleEntry
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.schedule import (
    ClassSessionCreate,
    RequestedChange,
    ScheduleChangeRequestCreate,
    ScheduleChangeRequestResolve,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
)
from app.services import schedule_service as schedule_service_module
from app.services.schedule_service import ScheduleService


def make_entry(**overrides) -> ScheduleEntry:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        class_session_id=uuid.uuid4(),
        room_id=uuid.uuid4(),
        teacher_id=uuid.uuid4(),
        day_of_week="Mon",
        start_time=time(9, 0),
        end_time=time(10, 0),
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return ScheduleEntry(**defaults)


@pytest.fixture
def stub_repos(monkeypatch):
    schedule_repo = MagicMock()
    user_repo = MagicMock()
    course_repo = MagicMock()
    room_repo = MagicMock()
    semester_repo = MagicMock()
    monkeypatch.setattr(schedule_service_module, "schedule_repo", schedule_repo)
    monkeypatch.setattr(schedule_service_module, "user_repo", user_repo)
    monkeypatch.setattr(schedule_service_module, "course_repo", course_repo)
    monkeypatch.setattr(schedule_service_module, "room_repo", room_repo)
    monkeypatch.setattr(schedule_service_module, "semester_repo", semester_repo)
    return schedule_repo, user_repo, course_repo, room_repo, semester_repo


@pytest.fixture
def service():
    return ScheduleService()


@pytest.fixture
def session():
    return MagicMock()


class TestCreateClassSession:
    def test_invalid_course_id_raises_422(self, service, stub_repos, session):
        _schedule_repo, _user_repo, course_repo, _room_repo, _semester_repo = stub_repos
        course_repo.get.return_value = None
        payload = ClassSessionCreate(
            course_id=uuid.uuid4(), teacher_id=uuid.uuid4(), semester_id=uuid.uuid4(), section_label="A"
        )
        with pytest.raises(HTTPException) as exc:
            service.create_class_session(session, payload)
        assert exc.value.status_code == 422


class TestCreateEntry:
    def test_start_after_end_raises_422(self, service, stub_repos, session):
        schedule_repo, user_repo, _course_repo, room_repo, _semester_repo = stub_repos
        payload = ScheduleEntryCreate(
            class_session_id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            day_of_week="Mon",
            start_time=time(10, 0),
            end_time=time(9, 0),
        )
        with pytest.raises(HTTPException) as exc:
            service.create_entry(session, payload)
        assert exc.value.status_code == 422
        schedule_repo.create_schedule_entry.assert_not_called()

    def test_conflict_raises_409(self, service, stub_repos, session):
        schedule_repo, user_repo, _course_repo, room_repo, _semester_repo = stub_repos
        schedule_repo.get_class_session.return_value = MagicMock()
        room_repo.get.return_value = MagicMock()
        user_repo.get_teacher_with_user.return_value = (MagicMock(), MagicMock())
        schedule_repo.find_overlapping_entries.return_value = [make_entry()]

        payload = ScheduleEntryCreate(
            class_session_id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            day_of_week="Mon",
            start_time=time(9, 30),
            end_time=time(10, 30),
        )
        with pytest.raises(HTTPException) as exc:
            service.create_entry(session, payload)
        assert exc.value.status_code == 409

    def test_success_creates_entry(self, service, stub_repos, session):
        schedule_repo, user_repo, _course_repo, room_repo, _semester_repo = stub_repos
        schedule_repo.get_class_session.return_value = MagicMock()
        room_repo.get.return_value = MagicMock()
        user_repo.get_teacher_with_user.return_value = (MagicMock(), MagicMock())
        schedule_repo.find_overlapping_entries.return_value = []
        schedule_repo.create_schedule_entry.return_value = make_entry()

        payload = ScheduleEntryCreate(
            class_session_id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            day_of_week="Mon",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        service.create_entry(session, payload)
        session.commit.assert_called_once()


class TestUpdateEntry:
    def test_not_found_raises_404(self, service, stub_repos, session):
        schedule_repo, *_ = stub_repos
        schedule_repo.get_schedule_entry.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.update_entry(session, uuid.uuid4(), ScheduleEntryUpdate())
        assert exc.value.status_code == 404

    def test_conflict_check_excludes_self(self, service, stub_repos, session):
        schedule_repo, *_ = stub_repos
        entry = make_entry()
        schedule_repo.get_schedule_entry.return_value = entry
        schedule_repo.find_overlapping_entries.return_value = []

        service.update_entry(session, entry.id, ScheduleEntryUpdate(start_time=time(11, 0), end_time=time(12, 0)))

        call_kwargs = schedule_repo.find_overlapping_entries.call_args.kwargs
        assert call_kwargs["exclude_id"] == entry.id

    def test_new_time_range_invalid_raises_422(self, service, stub_repos, session):
        schedule_repo, *_ = stub_repos
        entry = make_entry()
        schedule_repo.get_schedule_entry.return_value = entry
        with pytest.raises(HTTPException) as exc:
            service.update_entry(session, entry.id, ScheduleEntryUpdate(start_time=time(11, 0), end_time=time(10, 0)))
        assert exc.value.status_code == 422


class TestDeleteEntry:
    def test_not_found_raises_404(self, service, stub_repos, session):
        schedule_repo, *_ = stub_repos
        schedule_repo.get_schedule_entry.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.delete_entry(session, uuid.uuid4())
        assert exc.value.status_code == 404


class TestGetConflicts:
    def test_detects_room_overlap_with_different_start_times(self, service, stub_repos, session):
        # BR-005: the DB UniqueConstraint alone would miss this (different
        # start_time on each row) — this is exactly the case the service
        # layer's overlap math must catch.
        schedule_repo, *_ = stub_repos
        room_id = uuid.uuid4()
        entry_a = make_entry(room_id=room_id, start_time=time(9, 0), end_time=time(10, 0))
        entry_b = make_entry(room_id=room_id, start_time=time(9, 30), end_time=time(10, 30))
        schedule_repo.list_all_entries.return_value = [entry_a, entry_b]

        result = service.get_conflicts(session)

        assert len(result.conflicts) == 1
        assert result.conflicts[0].type == "room"

    def test_no_conflict_for_non_overlapping_entries(self, service, stub_repos, session):
        schedule_repo, *_ = stub_repos
        room_id = uuid.uuid4()
        entry_a = make_entry(room_id=room_id, start_time=time(9, 0), end_time=time(10, 0))
        entry_b = make_entry(room_id=room_id, start_time=time(10, 0), end_time=time(11, 0))
        schedule_repo.list_all_entries.return_value = [entry_a, entry_b]

        result = service.get_conflicts(session)

        assert len(result.conflicts) == 0

    def test_detects_teacher_overlap_different_rooms(self, service, stub_repos, session):
        schedule_repo, *_ = stub_repos
        teacher_id = uuid.uuid4()
        entry_a = make_entry(teacher_id=teacher_id, room_id=uuid.uuid4(), start_time=time(9, 0), end_time=time(10, 0))
        entry_b = make_entry(teacher_id=teacher_id, room_id=uuid.uuid4(), start_time=time(9, 30), end_time=time(10, 30))
        schedule_repo.list_all_entries.return_value = [entry_a, entry_b]

        result = service.get_conflicts(session)

        assert len(result.conflicts) == 1
        assert result.conflicts[0].type == "teacher"


class TestCreateChangeRequest:
    def test_teacher_cannot_request_change_for_another_teachers_entry(self, service, stub_repos, session):
        # BR-004 ownership check.
        schedule_repo, user_repo, *_ = stub_repos
        other_teacher_id = uuid.uuid4()
        entry = make_entry(teacher_id=other_teacher_id)
        schedule_repo.get_schedule_entry.return_value = entry
        user_repo.get_teacher_profile_by_user_id.return_value = Teacher(id=uuid.uuid4(), user_id=uuid.uuid4())

        current_user = User(id=uuid.uuid4(), email="t@example.com", role="teacher")
        payload = ScheduleChangeRequestCreate(
            schedule_entry_id=entry.id, requested_change=RequestedChange(start_time=time(11, 0), end_time=time(12, 0))
        )
        with pytest.raises(HTTPException) as exc:
            service.create_change_request(session, current_user, payload)
        assert exc.value.status_code == 403

    def test_owner_can_request_change(self, service, stub_repos, session):
        schedule_repo, user_repo, *_ = stub_repos
        teacher_id = uuid.uuid4()
        entry = make_entry(teacher_id=teacher_id)
        schedule_repo.get_schedule_entry.return_value = entry
        user_repo.get_teacher_profile_by_user_id.return_value = Teacher(id=teacher_id, user_id=uuid.uuid4())
        schedule_repo.create_change_request.return_value = ScheduleChangeRequest(
            id=uuid.uuid4(),
            schedule_entry_id=entry.id,
            requested_by_teacher_id=teacher_id,
            requested_change={},
            status="pending",
            created_at=datetime.now(timezone.utc),
        )

        current_user = User(id=uuid.uuid4(), email="t@example.com", role="teacher")
        payload = ScheduleChangeRequestCreate(
            schedule_entry_id=entry.id, requested_change=RequestedChange(start_time=time(11, 0), end_time=time(12, 0))
        )
        result = service.create_change_request(session, current_user, payload)
        assert result.status == "pending"


class TestResolveChangeRequest:
    def test_already_resolved_raises_409(self, service, stub_repos, session):
        schedule_repo, *_ = stub_repos
        schedule_repo.get_change_request.return_value = ScheduleChangeRequest(
            id=uuid.uuid4(), status="approved", requested_change={}
        )
        with pytest.raises(HTTPException) as exc:
            service.resolve_change_request(
                session, uuid.uuid4(), ScheduleChangeRequestResolve(decision="approve"), User(id=uuid.uuid4())
            )
        assert exc.value.status_code == 409

    def test_reject_does_not_touch_schedule_entry(self, service, stub_repos, session):
        schedule_repo, user_repo, *_ = stub_repos
        request = ScheduleChangeRequest(
            id=uuid.uuid4(), status="pending", schedule_entry_id=uuid.uuid4(), requested_change={}
        )
        schedule_repo.get_change_request.return_value = request
        user_repo.get_admin_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())

        result = service.resolve_change_request(
            session, request.id, ScheduleChangeRequestResolve(decision="reject"), User(id=uuid.uuid4())
        )

        assert result.status == "rejected"
        schedule_repo.get_schedule_entry.assert_not_called()

    def test_approve_applies_requested_time_and_checks_conflicts(self, service, stub_repos, session):
        schedule_repo, user_repo, *_ = stub_repos
        entry = make_entry()
        request = ScheduleChangeRequest(
            id=uuid.uuid4(),
            status="pending",
            schedule_entry_id=entry.id,
            requested_change={"start_time": "11:00:00", "end_time": "12:00:00"},
        )
        schedule_repo.get_change_request.return_value = request
        schedule_repo.get_schedule_entry.return_value = entry
        schedule_repo.find_overlapping_entries.return_value = []
        user_repo.get_admin_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())

        result = service.resolve_change_request(
            session, request.id, ScheduleChangeRequestResolve(decision="approve"), User(id=uuid.uuid4())
        )

        assert result.status == "approved"
        assert entry.start_time == time(11, 0)
        assert entry.end_time == time(12, 0)


class TestGetMe:
    """Gap closure: Parent access via GET /schedule/me + student_id,
    mirroring the same convention as attendance_service.get_me /
    fee_service.get_my_fees."""

    def _parent_user(self):
        return User(id=uuid.uuid4(), email="p@example.com", role="parent")

    def test_parent_without_student_id_rejected(self, service, stub_repos, session):
        _schedule_repo, user_repo, *_ = stub_repos
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())

        with pytest.raises(HTTPException) as exc:
            service.get_me(session, self._parent_user())
        assert exc.value.status_code == 403

    def test_parent_without_link_rejected(self, service, stub_repos, session):
        _schedule_repo, user_repo, *_ = stub_repos
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        user_repo.parent_has_linked_student.return_value = False

        with pytest.raises(HTTPException) as exc:
            service.get_me(session, self._parent_user(), student_id=uuid.uuid4())
        assert exc.value.status_code == 403

    def test_parent_with_link_returns_child_schedule(self, service, stub_repos, session):
        schedule_repo, user_repo, *_ = stub_repos
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        user_repo.parent_has_linked_student.return_value = True
        schedule_repo.list_class_session_ids_for_student.return_value = []
        schedule_repo.list_entries_for_class_sessions.return_value = []
        student_id = uuid.uuid4()

        result = service.get_me(session, self._parent_user(), student_id=student_id)

        assert result.entries == []
        schedule_repo.list_class_session_ids_for_student.assert_called_once_with(session, student_id)
