"""
Unit tests: app.services.user_service.UserService.

UserRepository and DepartmentRepository are stubbed (per CLAUDE.md §10)
so these tests exercise business rules only: VR-009 (role/is_active/
department_id cannot be smuggled through PUT /users/me), BR-006
(deactivation is a soft flag, never a row deletion, and is idempotent),
department-existence validation on create/update (422), and email-
uniqueness handling (409) for Admin-driven account creation.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.admin import Admin
from app.models.department import Department
from app.models.parent import Parent
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.student import StudentCreate, StudentUpdate
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.schemas.user import MeUpdate
from app.services import user_service as user_service_module
from app.services.user_service import UserService


def make_user(**overrides) -> User:
    defaults = dict(
        id=uuid.uuid4(),
        email="user@example.com",
        role="student",
        is_active=True,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return User(**defaults)


def make_student(**overrides) -> Student:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        department_id=uuid.uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        enrollment_date=date(2026, 1, 1),
    )
    defaults.update(overrides)
    return Student(**defaults)


@pytest.fixture
def stub_repos(monkeypatch):
    user_repo = MagicMock()
    department_repo = MagicMock()
    monkeypatch.setattr(user_service_module, "user_repo", user_repo)
    monkeypatch.setattr(user_service_module, "department_repo", department_repo)
    return user_repo, department_repo


@pytest.fixture
def service():
    return UserService()


@pytest.fixture
def session():
    return MagicMock()


class TestMeUpdateSchema:
    def test_role_is_active_department_id_are_not_accepted_fields(self):
        # VR-009: these fields don't exist on the schema at all, so a
        # client-supplied value is silently dropped by Pydantic's default
        # "ignore extra fields" behavior — there is nothing for the
        # service layer to smuggle through, by construction.
        payload = MeUpdate.model_validate(
            {"first_name": "New", "role": "admin", "is_active": False, "department_id": str(uuid.uuid4())}
        )
        assert payload.first_name == "New"
        assert not hasattr(payload, "role")
        assert not hasattr(payload, "is_active")
        assert not hasattr(payload, "department_id")


class TestGetMe:
    def test_student_profile_maps_department_id(self, service, stub_repos, session):
        user_repo, _ = stub_repos
        user = make_user(role="student")
        student = make_student(department_id=uuid.uuid4())
        user_repo.get_student_profile_by_user_id.return_value = student

        result = service.get_me(session, user)

        assert result.profile.first_name == student.first_name
        assert result.profile.department_id == student.department_id

    def test_parent_profile_has_no_department_id(self, service, stub_repos, session):
        user_repo, _ = stub_repos
        user = make_user(role="parent")
        parent = Parent(id=uuid.uuid4(), user_id=user.id, first_name="Pat", last_name="Guardian")
        user_repo.get_parent_profile_by_user_id.return_value = parent

        result = service.get_me(session, user)

        assert result.profile.department_id is None
        assert result.profile.profile_photo_url is None


class TestUpdateMe:
    def test_profile_photo_url_ignored_for_admin_role(self, service, stub_repos, session):
        # Database_Design.md §6.5: admin has no profile_photo_url column.
        user_repo, _ = stub_repos
        user = make_user(role="admin")
        admin = Admin(id=uuid.uuid4(), user_id=user.id, first_name="A", last_name="Dmin")
        user_repo.get_admin_profile_by_user_id.return_value = admin

        service.update_me(session, user, MeUpdate(profile_photo_url="http://example.com/x.png"))

        assert not hasattr(admin, "profile_photo_url")


class TestCreateStudent:
    def test_invalid_department_raises_422_before_any_write(self, service, stub_repos, session):
        user_repo, department_repo = stub_repos
        department_repo.get.return_value = None

        payload = StudentCreate(
            email="s@example.com",
            password="password123",
            first_name="A",
            last_name="B",
            department_id=uuid.uuid4(),
            enrollment_date=date(2026, 1, 1),
        )
        with pytest.raises(HTTPException) as exc:
            service.create_student(session, payload)

        assert exc.value.status_code == 422
        user_repo.create_user.assert_not_called()

    def test_duplicate_email_raises_409_and_rolls_back(self, service, stub_repos, session):
        user_repo, department_repo = stub_repos
        department_repo.get.return_value = Department(id=uuid.uuid4(), name="CS", code="CS")
        user_repo.create_user.side_effect = IntegrityError("stmt", {}, Exception("dup"))

        payload = StudentCreate(
            email="s@example.com",
            password="password123",
            first_name="A",
            last_name="B",
            department_id=uuid.uuid4(),
            enrollment_date=date(2026, 1, 1),
        )
        with pytest.raises(HTTPException) as exc:
            service.create_student(session, payload)

        assert exc.value.status_code == 409
        session.rollback.assert_called_once()

    def test_success_creates_user_and_student_in_one_transaction(self, service, stub_repos, session):
        user_repo, department_repo = stub_repos
        department_repo.get.return_value = Department(id=uuid.uuid4(), name="CS", code="CS")
        user = make_user(email="s@example.com")
        student = make_student(user_id=user.id)
        user_repo.create_user.return_value = user
        user_repo.create_student.return_value = student

        payload = StudentCreate(
            email="s@example.com",
            password="password123",
            first_name=student.first_name,
            last_name=student.last_name,
            department_id=student.department_id,
            enrollment_date=student.enrollment_date,
        )
        result = service.create_student(session, payload)

        session.commit.assert_called_once()
        assert result.email == "s@example.com"
        assert result.is_active is True


class TestDeactivateStudent:
    def test_sets_user_inactive_without_deleting_student_row(self, service, stub_repos, session):
        user_repo, _ = stub_repos
        student = make_student()
        user = make_user(id=student.user_id, is_active=True)
        user_repo.get_student_with_user.return_value = (student, user)

        result = service.deactivate_student(session, student.id)

        assert user.is_active is False
        assert result.is_active is False
        assert result.id == student.id  # student row untouched, not deleted

    def test_not_found_raises_404(self, service, stub_repos, session):
        user_repo, _ = stub_repos
        user_repo.get_student_with_user.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.deactivate_student(session, uuid.uuid4())
        assert exc.value.status_code == 404

    def test_idempotent_on_already_deactivated_student(self, service, stub_repos, session):
        user_repo, _ = stub_repos
        student = make_student()
        user = make_user(id=student.user_id, is_active=False)
        user_repo.get_student_with_user.return_value = (student, user)

        result = service.deactivate_student(session, student.id)

        assert result.is_active is False


class TestUpdateStudent:
    def test_reactivates_via_is_active_true(self, service, stub_repos, session):
        user_repo, department_repo = stub_repos
        student = make_student()
        user = make_user(id=student.user_id, is_active=False)
        user_repo.get_student_with_user.return_value = (student, user)

        result = service.update_student(session, student.id, StudentUpdate(is_active=True))

        assert user.is_active is True
        assert result.is_active is True

    def test_invalid_department_on_update_raises_422(self, service, stub_repos, session):
        user_repo, department_repo = stub_repos
        student = make_student()
        user = make_user(id=student.user_id)
        user_repo.get_student_with_user.return_value = (student, user)
        department_repo.get.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.update_student(session, student.id, StudentUpdate(department_id=uuid.uuid4()))
        assert exc.value.status_code == 422


class TestTeacherManagement:
    def test_create_teacher_duplicate_email_raises_409(self, service, stub_repos, session):
        user_repo, department_repo = stub_repos
        department_repo.get.return_value = Department(id=uuid.uuid4(), name="CS", code="CS")
        user_repo.create_user.side_effect = IntegrityError("stmt", {}, Exception("dup"))

        payload = TeacherCreate(
            email="t@example.com", password="password123", first_name="A", last_name="B", department_id=uuid.uuid4()
        )
        with pytest.raises(HTTPException) as exc:
            service.create_teacher(session, payload)
        assert exc.value.status_code == 409

    def test_update_teacher_not_found_raises_404(self, service, stub_repos, session):
        user_repo, _ = stub_repos
        user_repo.get_teacher_with_user.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.update_teacher(session, uuid.uuid4(), TeacherUpdate(first_name="X"))
        assert exc.value.status_code == 404
