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


# --- Version 2.3 (Academic Setup) — update/delete RBAC + basic success/
# conflict paths. Department is exercised in full detail; Course/Room/
# Semester share the exact same _require_admin wiring and service-layer
# 409-on-conflict pattern, so each gets one representative RBAC test plus
# one success-path test rather than fully duplicating Department's depth
# (matches this file's own stated "representative rather than exhaustive"
# convention above).


class TestUpdateDeleteRBAC:
    def test_update_department_rejected_for_non_admin(self, client, make_user, make_department):
        make_user("student@example.com", "correct-password", "student")
        token = _login(client, "student@example.com", "correct-password")
        department = make_department()

        response = client.put(
            f"/api/v1/departments/{department.id}",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_delete_department_rejected_for_non_admin(self, client, make_user, make_department):
        make_user("student@example.com", "correct-password", "student")
        token = _login(client, "student@example.com", "correct-password")
        department = make_department()

        response = client.delete(
            f"/api/v1/departments/{department.id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_update_course_rejected_for_non_admin(self, client, make_user, make_course):
        make_user("student@example.com", "correct-password", "student")
        token = _login(client, "student@example.com", "correct-password")
        course = make_course()

        response = client.put(
            f"/api/v1/courses/{course.id}", json={"name": "New"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_delete_course_rejected_for_non_admin(self, client, make_user, make_course):
        make_user("student@example.com", "correct-password", "student")
        token = _login(client, "student@example.com", "correct-password")
        course = make_course()

        response = client.delete(f"/api/v1/courses/{course.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_update_room_rejected_for_non_admin(self, client, make_user, make_room):
        make_user("student@example.com", "correct-password", "student")
        token = _login(client, "student@example.com", "correct-password")
        room = make_room()

        response = client.put(
            f"/api/v1/rooms/{room.id}", json={"name": "New"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_delete_room_rejected_for_non_admin(self, client, make_user, make_room):
        make_user("student@example.com", "correct-password", "student")
        token = _login(client, "student@example.com", "correct-password")
        room = make_room()

        response = client.delete(f"/api/v1/rooms/{room.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_update_semester_rejected_for_non_admin(self, client, make_user, make_semester):
        make_user("student@example.com", "correct-password", "student")
        token = _login(client, "student@example.com", "correct-password")
        semester = make_semester()

        response = client.put(
            f"/api/v1/semesters/{semester.id}", json={"name": "New"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_delete_semester_rejected_for_non_admin(self, client, make_user, make_semester):
        make_user("student@example.com", "correct-password", "student")
        token = _login(client, "student@example.com", "correct-password")
        semester = make_semester()

        response = client.delete(f"/api/v1/semesters/{semester.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403


class TestUpdateDeleteSuccessAndConflict:
    def test_admin_updates_department(self, client, make_user, make_department):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        department = make_department()

        response = client.put(
            f"/api/v1/departments/{department.id}",
            json={"name": "Renamed Department"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Department"

    def test_admin_deletes_unreferenced_department(self, client, make_user, make_department):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        department = make_department()

        response = client.delete(
            f"/api/v1/departments/{department.id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 204

        get_response = client.get(
            f"/api/v1/departments/{department.id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 404

    def test_admin_deletes_referenced_department_returns_409(self, client, make_user, make_department, make_course):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        department = make_department()
        make_course(department=department)

        response = client.delete(
            f"/api/v1/departments/{department.id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 409

    def test_admin_updates_course(self, client, make_user, make_course):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        course = make_course()

        response = client.put(
            f"/api/v1/courses/{course.id}",
            json={"credit_hours": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["credit_hours"] == 5

    def test_admin_deletes_unreferenced_course(self, client, make_user, make_course):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        course = make_course()

        response = client.delete(f"/api/v1/courses/{course.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 204

    def test_admin_updates_room(self, client, make_user, make_room):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        room = make_room()

        response = client.put(
            f"/api/v1/rooms/{room.id}", json={"capacity": 99}, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["capacity"] == 99

    def test_admin_deletes_unreferenced_room(self, client, make_user, make_room):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        room = make_room()

        response = client.delete(f"/api/v1/rooms/{room.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 204

    def test_admin_updates_semester(self, client, make_user, make_semester):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        semester = make_semester()

        response = client.put(
            f"/api/v1/semesters/{semester.id}",
            json={"name": "Renamed Semester"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Semester"

    def test_admin_deletes_unreferenced_semester(self, client, make_user, make_semester):
        make_user("admin@example.com", "correct-password", "admin")
        token = _login(client, "admin@example.com", "correct-password")
        semester = make_semester()

        response = client.delete(f"/api/v1/semesters/{semester.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 204
