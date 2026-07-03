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

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
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
    from app.models.department import Department

    def _make_department(name: str = "Computer Science", code: str = "CS") -> Department:
        department = Department(name=name, code=code)
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
