"""
Pytest fixtures shared across backend tests.

Integration tests need a real database (per CLAUDE.md §10 — "integration
tests for routers... against a test database"), because app.models.user
uses PostgreSQL's native UUID/Enum types that SQLite cannot represent. The
target database is read from TEST_DATABASE_URL; if it isn't set, integration
tests are skipped rather than run against — or worse, silently created
against — an unfamiliar database. Never point this at a developer's real
local database; it is dropped and recreated (schema-level) between test runs.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

requires_test_database = pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL not set — integration tests need a disposable Postgres database",
)


@pytest.fixture(scope="session")
def test_engine():
    if TEST_DATABASE_URL is None:
        pytest.skip("TEST_DATABASE_URL not set")

    os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)
    os.environ.setdefault("JWT_SECRET_KEY", "test-suite-secret-key-not-for-production")

    from app.db.base import Base
    import app.models  # noqa: F401 — registers all models on Base.metadata

    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Session:
    # Service-layer code (AuthService/UserRepository) calls session.commit()
    # directly, so a plain outer transaction would be committed away by the
    # first commit, leaking test data into later tests. Nesting a SAVEPOINT
    # and restarting it after every commit keeps each test isolated and
    # rollback-able regardless of how many commits the code under test issues.
    connection = test_engine.connect()
    outer_transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session
    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture
def client(test_engine, db_session):
    from app.db.session import get_db
    from app.main import app
    from app.middleware.rate_limit import _attempts as login_rate_limit_attempts

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Milestone 11's login rate limiter is keyed by client IP; TestClient
    # sends every request from the same host ("testclient"), so its
    # in-memory bucket must be reset per test — otherwise tests that call
    # POST /auth/login several times (directly or via a shared `_login()`
    # helper) would eventually trip the real 429 limit across unrelated
    # test functions in the same run.
    login_rate_limit_attempts.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    from app.core.security import hash_password
    from app.models.user import User

    def _make_user(email: str, password: str, role: str, is_active: bool = True) -> User:
        user = User(email=email, password_hash=hash_password(password), role=role, is_active=is_active)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def auth_headers():
    def _auth_headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    return _auth_headers


@pytest.fixture
def make_department(db_session):
    import uuid

    from app.models.department import Department

    def _make_department(name: str | None = None, code: str | None = None) -> Department:
        # Unique-by-default so a test creating a department via multiple
        # independent fixture calls (e.g. make_course() and
        # make_teacher_user() each calling make_department() internally)
        # never collides on department.name/code's unique constraints —
        # this exact collision was found and fixed during Milestone 4.
        suffix = uuid.uuid4().hex[:8]
        department = Department(name=name or f"Department {suffix}", code=code or f"D{suffix}")
        db_session.add(department)
        db_session.commit()
        db_session.refresh(department)
        return department

    return _make_department


@pytest.fixture
def make_student_user(db_session, make_user, make_department):
    from datetime import date

    from app.models.student import Student

    def _make_student_user(email: str, password: str, department=None, is_active: bool = True) -> tuple:
        department = department or make_department()
        user = make_user(email, password, "student", is_active=is_active)
        student = Student(
            user_id=user.id,
            department_id=department.id,
            first_name="Test",
            last_name="Student",
            enrollment_date=date(2026, 1, 1),
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        return user, student

    return _make_student_user


@pytest.fixture
def make_teacher_user(db_session, make_user, make_department):
    from app.models.teacher import Teacher

    def _make_teacher_user(email: str, password: str, department=None, is_active: bool = True) -> tuple:
        department = department or make_department()
        user = make_user(email, password, "teacher", is_active=is_active)
        teacher = Teacher(
            user_id=user.id, department_id=department.id, first_name="Test", last_name="Teacher"
        )
        db_session.add(teacher)
        db_session.commit()
        db_session.refresh(teacher)
        return user, teacher

    return _make_teacher_user


@pytest.fixture
def make_admin_user(db_session, make_user):
    from app.models.admin import Admin

    def _make_admin_user(email: str, password: str) -> tuple:
        user = make_user(email, password, "admin")
        admin = Admin(user_id=user.id, first_name="Test", last_name="Admin")
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return user, admin

    return _make_admin_user


@pytest.fixture
def make_course(db_session, make_department):
    from app.models.course import Course

    def _make_course(department=None, name: str = "Intro to CS", code: str = "CS101", credit_hours: int = 3) -> Course:
        department = department or make_department()
        course = Course(department_id=department.id, name=name, code=code, credit_hours=credit_hours)
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)
        return course

    return _make_course


@pytest.fixture
def make_room(db_session):
    from app.models.room import Room

    def _make_room(name: str = "Room 101", building: str | None = "Main", capacity: int | None = 30) -> Room:
        room = Room(name=name, building=building, capacity=capacity)
        db_session.add(room)
        db_session.commit()
        db_session.refresh(room)
        return room

    return _make_room


@pytest.fixture
def make_semester(db_session):
    from datetime import date

    from app.models.semester import Semester

    def _make_semester(
        name: str = "Fall 2026", start_date: date = date(2026, 9, 1), end_date: date = date(2026, 12, 20)
    ) -> Semester:
        semester = Semester(name=name, start_date=start_date, end_date=end_date)
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        return semester

    return _make_semester


@pytest.fixture
def make_class_session(db_session, make_course, make_semester):
    from app.models.class_session import ClassSession

    def _make_class_session(course=None, teacher=None, semester=None, section_label: str = "Section A") -> ClassSession:
        course = course or make_course()
        semester = semester or make_semester()
        class_session = ClassSession(
            course_id=course.id, teacher_id=teacher.id, semester_id=semester.id, section_label=section_label
        )
        db_session.add(class_session)
        db_session.commit()
        db_session.refresh(class_session)
        return class_session

    return _make_class_session


@pytest.fixture
def make_parent_user(db_session, make_user):
    from app.models.parent import Parent

    def _make_parent_user(email: str, password: str) -> tuple:
        user = make_user(email, password, "parent")
        parent = Parent(user_id=user.id, first_name="Test", last_name="Parent")
        db_session.add(parent)
        db_session.commit()
        db_session.refresh(parent)
        return user, parent

    return _make_parent_user


@pytest.fixture
def link_parent_student(db_session):
    from app.models.parent_student_link import ParentStudentLink

    def _link_parent_student(parent, student) -> ParentStudentLink:
        link = ParentStudentLink(parent_id=parent.id, student_id=student.id)
        db_session.add(link)
        db_session.commit()
        db_session.refresh(link)
        return link

    return _link_parent_student


@pytest.fixture
def make_enrollment(db_session):
    from app.models.enrollment import Enrollment

    def _make_enrollment(student, class_session) -> Enrollment:
        enrollment = Enrollment(student_id=student.id, class_session_id=class_session.id)
        db_session.add(enrollment)
        db_session.commit()
        db_session.refresh(enrollment)
        return enrollment

    return _make_enrollment


@pytest.fixture
def make_schedule_entry(db_session, make_room):
    from datetime import time

    from app.models.schedule_entry import ScheduleEntry

    def _make_schedule_entry(
        class_session,
        teacher,
        room=None,
        day_of_week: str = "Mon",
        start_time: time = time(9, 0),
        end_time: time = time(10, 0),
    ) -> ScheduleEntry:
        room = room or make_room()
        entry = ScheduleEntry(
            class_session_id=class_session.id,
            room_id=room.id,
            teacher_id=teacher.id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        return entry

    return _make_schedule_entry
