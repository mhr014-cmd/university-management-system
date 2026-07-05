"""
Integration tests: GET/PUT /users/me, /users/students*, /users/teachers*.

Full request -> DB -> response cycle against a disposable test database
(see tests/conftest.py). Requires TEST_DATABASE_URL — skipped otherwise.
"""

from tests.conftest import requires_test_database

pytestmark = requires_test_database


def _login(client, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


class TestGetMe:
    def test_requires_authentication(self, client):
        assert client.get("/api/v1/users/me").status_code == 401

    def test_student_sees_own_profile_with_department(self, client, make_student_user):
        user, student = make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")

        response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "student@example.com"
        assert body["role"] == "student"
        assert body["profile"]["department_id"] == str(student.department_id)
        # Production-polish fix: the Profile page's read-only Department
        # field must show a name, not just the raw department_id UUID.
        assert body["profile"]["department_name"]

    def test_admin_profile_has_null_department_id(self, client, make_admin_user):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")

        response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json()["profile"]["department_id"] is None


class TestGetMyChildren:
    def test_requires_authentication(self, client):
        assert client.get("/api/v1/users/me/children").status_code == 401

    def test_forbidden_for_non_parent_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.get("/api/v1/users/me/children", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_parent_sees_linked_children_by_name(
        self, client, make_parent_user, make_student_user, link_parent_student
    ):
        _parent_user, parent = make_parent_user("parent@example.com", "correct-password")
        _student_user, student = make_student_user("child@example.com", "student-password")
        link_parent_student(parent, student)
        token = _login(client, "parent@example.com", "correct-password")

        response = client.get("/api/v1/users/me/children", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        body = response.json()
        assert len(body["children"]) == 1
        assert body["children"][0]["first_name"] == student.first_name
        assert body["children"][0]["id"] == str(student.id)

    def test_parent_with_no_linked_children_sees_empty_list(self, client, make_parent_user):
        make_parent_user("parent@example.com", "correct-password")
        token = _login(client, "parent@example.com", "correct-password")

        response = client.get("/api/v1/users/me/children", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json()["children"] == []


class TestUpdateMe:
    def test_updates_own_first_last_name(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")

        response = client.put(
            "/api/v1/users/me",
            json={"first_name": "Updated", "last_name": "Name"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["profile"]["first_name"] == "Updated"

    def test_role_and_is_active_in_body_are_silently_ignored(self, client, make_student_user):
        # VR-009: sending role/is_active must not change them — the schema
        # has no such field, so this is an inert extra key, not a rejected one.
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")

        response = client.put(
            "/api/v1/users/me",
            json={"first_name": "Still Student", "role": "admin", "is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["role"] == "student"

        # Confirm is_active truly wasn't touched: still able to log in.
        assert _login(client, "student@example.com", "correct-password")


class TestListStudents:
    def test_requires_authentication(self, client):
        assert client.get("/api/v1/users/students").status_code == 401

    def test_forbidden_for_student_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.get("/api/v1/users/students", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_allowed_for_teacher_role(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.get("/api/v1/users/students", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    def test_allowed_for_admin_role(self, client, make_admin_user, make_student_user):
        make_admin_user("admin@example.com", "correct-password")
        make_student_user("student@example.com", "student-password")
        token = _login(client, "admin@example.com", "correct-password")
        response = client.get("/api/v1/users/students", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestCreateStudent:
    def test_forbidden_for_non_admin(self, client, make_teacher_user, make_department):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        department = make_department(name="Business", code="BBA")
        response = client.post(
            "/api/v1/users/students",
            json={
                "email": "new-student@example.com",
                "password": "password123",
                "first_name": "New",
                "last_name": "Student",
                "department_id": str(department.id),
                "enrollment_date": "2026-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_admin_creates_student_successfully(self, client, make_admin_user, make_department):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        department = make_department()

        response = client.post(
            "/api/v1/users/students",
            json={
                "email": "new-student@example.com",
                "password": "password123",
                "first_name": "New",
                "last_name": "Student",
                "department_id": str(department.id),
                "enrollment_date": "2026-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "new-student@example.com"
        assert body["is_active"] is True
        # The newly created student can log in immediately.
        assert _login(client, "new-student@example.com", "password123")

    def test_invalid_department_id_returns_422(self, client, make_admin_user):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")

        response = client.post(
            "/api/v1/users/students",
            json={
                "email": "new-student@example.com",
                "password": "password123",
                "first_name": "New",
                "last_name": "Student",
                "department_id": "00000000-0000-0000-0000-000000000000",
                "enrollment_date": "2026-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_duplicate_email_returns_409(self, client, make_admin_user, make_student_user, make_department):
        make_admin_user("admin@example.com", "correct-password")
        make_student_user("existing@example.com", "some-password")
        token = _login(client, "admin@example.com", "correct-password")
        department = make_department(name="Business", code="BBA")

        response = client.post(
            "/api/v1/users/students",
            json={
                "email": "existing@example.com",
                "password": "password123",
                "first_name": "Dup",
                "last_name": "Licate",
                "department_id": str(department.id),
                "enrollment_date": "2026-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409


class TestStudentLifecycle:
    def test_get_nonexistent_student_returns_404(self, client, make_admin_user):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        response = client.get(
            "/api/v1/users/students/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_deactivate_then_reactivate_via_put(self, client, make_admin_user, make_student_user):
        make_admin_user("admin@example.com", "correct-password")
        _student_user, student = make_student_user("student@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        headers = {"Authorization": f"Bearer {token}"}

        deactivate_response = client.delete(f"/api/v1/users/students/{student.id}", headers=headers)
        assert deactivate_response.status_code == 200
        assert deactivate_response.json() == {"id": str(student.id), "is_active": False}

        # BR-006: soft deactivation is idempotent — calling it again is not an error.
        second_deactivate = client.delete(f"/api/v1/users/students/{student.id}", headers=headers)
        assert second_deactivate.status_code == 200

        # Deactivated student can no longer log in (BR-006 via M2's login check).
        blocked_login = client.post(
            "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
        )
        assert blocked_login.status_code == 403

        reactivate_response = client.put(
            f"/api/v1/users/students/{student.id}", json={"is_active": True}, headers=headers
        )
        assert reactivate_response.status_code == 200
        assert reactivate_response.json()["is_active"] is True
        assert _login(client, "student@example.com", "correct-password")


class TestTeacherManagement:
    def test_list_teachers_forbidden_for_teacher_role(self, client, make_teacher_user):
        # Unlike /users/students (Admin, Teacher), /users/teachers is Admin-only.
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.get("/api/v1/users/teachers", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_admin_creates_and_updates_teacher(self, client, make_admin_user, make_department):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        headers = {"Authorization": f"Bearer {token}"}
        department = make_department()

        create_response = client.post(
            "/api/v1/users/teachers",
            json={
                "email": "new-teacher@example.com",
                "password": "password123",
                "first_name": "New",
                "last_name": "Teacher",
                "department_id": str(department.id),
            },
            headers=headers,
        )
        assert create_response.status_code == 201
        teacher_id = create_response.json()["id"]

        update_response = client.put(
            f"/api/v1/users/teachers/{teacher_id}", json={"last_name": "Updated"}, headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["last_name"] == "Updated"
