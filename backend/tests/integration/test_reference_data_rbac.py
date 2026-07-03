"""
Integration tests: RBAC retrofit on the reference-data endpoints
(Milestone 2 closed a Milestone 1 known issue here — see
docs/Proposal_vs_Engineering_Additions.md). Only /departments is exercised
directly; /courses, /rooms, /semesters share the exact same
_require_authenticated / _require_admin dependency wiring, so this is
representative rather than exhaustive per-resource coverage.

Full request -> DB -> response cycle against a disposable test database
(see tests/conftest.py). Requires TEST_DATABASE_URL — skipped otherwise.
"""

from tests.conftest import requires_test_database

pytestmark = requires_test_database


def _login(client, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_list_departments_requires_authentication(client):
    response = client.get("/api/v1/departments")
    assert response.status_code == 401


def test_list_departments_succeeds_for_any_authenticated_role(client, make_user):
    make_user("student@example.com", "correct-password", "student")
    token = _login(client, "student@example.com", "correct-password")

    response = client.get("/api/v1/departments", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_create_department_requires_authentication(client):
    response = client.post("/api/v1/departments", json={"name": "Computer Science", "code": "CS"})
    assert response.status_code == 401


def test_create_department_rejected_for_non_admin_role(client, make_user):
    make_user("student@example.com", "correct-password", "student")
    token = _login(client, "student@example.com", "correct-password")

    response = client.post(
        "/api/v1/departments",
        json={"name": "Computer Science", "code": "CS"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_create_department_succeeds_for_admin_role(client, make_user):
    make_user("admin@example.com", "correct-password", "admin")
    token = _login(client, "admin@example.com", "correct-password")

    response = client.post(
        "/api/v1/departments",
        json={"name": "Computer Science", "code": "CS"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["code"] == "CS"


def test_deactivated_user_rejected_even_with_valid_access_token(client, make_user, db_session):
    user = make_user("student@example.com", "correct-password", "student")
    token = _login(client, "student@example.com", "correct-password")

    # Deactivate after the token was issued — CLAUDE.md §12: a deactivated
    # user must fail authorization immediately even with a still-valid token.
    user.is_active = False
    db_session.add(user)
    db_session.commit()

    response = client.get("/api/v1/departments", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
