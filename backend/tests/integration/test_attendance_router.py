"""
Integration tests: GET/POST/PUT /attendance/*, GET /attendance/reports, and
the Milestone 5 mandatory Attendance Domain Rules end-to-end.

Full request -> DB -> response cycle against a disposable test database
(see tests/conftest.py). Requires TEST_DATABASE_URL — skipped otherwise.
"""

from tests.conftest import requires_test_database

pytestmark = requires_test_database


def _login(client, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_class_with_enrolled_student(
    make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
):
    _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
    _student_user, student = make_student_user("student@example.com", "student-password")
    class_session = make_class_session(teacher=teacher)
    make_enrollment(student, class_session)
    make_schedule_entry(class_session, teacher)
    return teacher, student, class_session


class TestMarkAttendance:
    def test_requires_teacher_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.post("/api/v1/attendance", json={}, headers=_headers(token))
        assert response.status_code == 403

    def test_success_marks_attendance(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        token = _login(client, "teacher@example.com", "teacher-password")

        response = client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-05",
                "records": [{"student_id": str(student.id), "status": "present"}],
            },
            headers=_headers(token),
        )
        assert response.status_code == 201
        assert response.json()[0]["status"] == "present"

    def test_duplicate_marking_returns_409(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        token = _login(client, "teacher@example.com", "teacher-password")
        payload = {
            "class_session_id": str(class_session.id),
            "attendance_date": "2026-01-05",
            "records": [{"student_id": str(student.id), "status": "present"}],
        }
        client.post("/api/v1/attendance", json=payload, headers=_headers(token))
        second = client.post("/api/v1/attendance", json=payload, headers=_headers(token))
        assert second.status_code == 409

    def test_unenrolled_student_returns_422(
        self, client, make_teacher_user, make_student_user, make_class_session, make_schedule_entry
    ):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        _student_user, student = make_student_user("student@example.com", "student-password")
        class_session = make_class_session(teacher=teacher)
        make_schedule_entry(class_session, teacher)
        # No enrollment created for this student.
        token = _login(client, "teacher@example.com", "teacher-password")

        response = client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-05",
                "records": [{"student_id": str(student.id), "status": "present"}],
            },
            headers=_headers(token),
        )
        assert response.status_code == 422

    def test_teacher_not_assigned_to_class_session_returns_403(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        _owner_user, owner = make_teacher_user("owner@example.com", "owner-password")
        _other_user, _other = make_teacher_user("other@example.com", "other-password")
        _student_user, student = make_student_user("student@example.com", "student-password")
        class_session = make_class_session(teacher=owner)
        make_enrollment(student, class_session)
        make_schedule_entry(class_session, owner)

        token = _login(client, "other@example.com", "other-password")
        response = client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-05",
                "records": [{"student_id": str(student.id), "status": "present"}],
            },
            headers=_headers(token),
        )
        assert response.status_code == 403

    def test_no_schedule_entry_returns_422(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        _student_user, student = make_student_user("student@example.com", "student-password")
        class_session = make_class_session(teacher=teacher)
        make_enrollment(student, class_session)
        # No schedule_entry created — Rule 3.
        token = _login(client, "teacher@example.com", "teacher-password")

        response = client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-05",
                "records": [{"student_id": str(student.id), "status": "present"}],
            },
            headers=_headers(token),
        )
        assert response.status_code == 422


class TestUpdateAttendance:
    def test_correction_updates_status(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-05",
                "records": [{"student_id": str(student.id), "status": "present"}],
            },
            headers=_headers(token),
        )
        record_id = create_response.json()[0]["id"]

        update_response = client.put(
            f"/api/v1/attendance/{record_id}", json={"status": "absent"}, headers=_headers(token)
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "absent"

    def test_requires_teacher_or_admin(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.put(
            "/api/v1/attendance/00000000-0000-0000-0000-000000000000",
            json={"status": "absent"},
            headers=_headers(token),
        )
        assert response.status_code == 403


class TestGetMyAttendance:
    def test_requires_student_role(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.get("/api/v1/attendance/me", headers=_headers(token))
        assert response.status_code == 403

    def test_returns_percentage_and_warning(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-05",
                "records": [{"student_id": str(student.id), "status": "absent"}],
            },
            headers=_headers(teacher_token),
        )

        student_token = _login(client, "student@example.com", "student-password")
        response = client.get("/api/v1/attendance/me", headers=_headers(student_token))
        assert response.status_code == 200
        body = response.json()
        assert body["overall_percentage"] == 0.0
        assert body["low_attendance_warning"] is True

    # --- Gap closure: Parent access via GET /attendance/me + student_id ---

    def test_parent_without_student_id_returns_403(
        self, client, make_teacher_user, make_student_user, make_parent_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        make_parent_user("parent@example.com", "parent-password")
        parent_token = _login(client, "parent@example.com", "parent-password")

        response = client.get("/api/v1/attendance/me", headers=_headers(parent_token))
        assert response.status_code == 403

    def test_parent_without_link_returns_403(
        self,
        client,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        make_schedule_entry,
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        make_parent_user("parent@example.com", "parent-password")  # not linked to `student`
        parent_token = _login(client, "parent@example.com", "parent-password")

        response = client.get(
            "/api/v1/attendance/me", params={"student_id": str(student.id)}, headers=_headers(parent_token)
        )
        assert response.status_code == 403

    def test_parent_with_link_sees_child_attendance(
        self,
        client,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        make_schedule_entry,
        link_parent_student,
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        _parent_user, parent = make_parent_user("parent@example.com", "parent-password")
        link_parent_student(parent, student)

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-05",
                "records": [{"student_id": str(student.id), "status": "absent"}],
            },
            headers=_headers(teacher_token),
        )

        parent_token = _login(client, "parent@example.com", "parent-password")
        response = client.get(
            "/api/v1/attendance/me", params={"student_id": str(student.id)}, headers=_headers(parent_token)
        )
        assert response.status_code == 200
        body = response.json()
        assert body["overall_percentage"] == 0.0
        assert body["low_attendance_warning"] is True


class TestGetClassAttendance:
    def test_parent_without_student_id_returns_403(
        self, client, make_teacher_user, make_student_user, make_parent_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        make_parent_user("parent@example.com", "parent-password")
        parent_token = _login(client, "parent@example.com", "parent-password")

        response = client.get(f"/api/v1/attendance/{class_session.id}", headers=_headers(parent_token))
        assert response.status_code == 403

    def test_parent_with_link_can_view(
        self,
        client,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        make_schedule_entry,
        link_parent_student,
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        _parent_user, parent = make_parent_user("parent@example.com", "parent-password")
        link_parent_student(parent, student)
        parent_token = _login(client, "parent@example.com", "parent-password")

        response = client.get(
            f"/api/v1/attendance/{class_session.id}",
            params={"student_id": str(student.id)},
            headers=_headers(parent_token),
        )
        assert response.status_code == 200

    def test_parent_without_link_to_this_student_returns_403(
        self,
        client,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        make_schedule_entry,
    ):
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        make_parent_user("parent@example.com", "parent-password")  # not linked to `student`
        parent_token = _login(client, "parent@example.com", "parent-password")

        response = client.get(
            f"/api/v1/attendance/{class_session.id}",
            params={"student_id": str(student.id)},
            headers=_headers(parent_token),
        )
        assert response.status_code == 403


class TestAttendanceReports:
    def test_requires_admin(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.get("/api/v1/attendance/reports", headers=_headers(token))
        assert response.status_code == 403

    def test_admin_gets_summary(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_class_with_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-05",
                "records": [{"student_id": str(student.id), "status": "present"}],
            },
            headers=_headers(teacher_token),
        )

        admin_token = _login(client, "admin@example.com", "correct-password")
        response = client.get("/api/v1/attendance/reports", headers=_headers(admin_token))
        assert response.status_code == 200
        assert response.json()["summary"][0]["percentage"] == 100.0
        # Final-polish fix: the report must show a display name, not just
        # the raw student_id, so the frontend Reports page never falls
        # back to rendering a UUID.
        assert response.json()["summary"][0]["student_name"] == "Test Student"


class TestClassSessionRoster:
    def test_teacher_sees_enrolled_students(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        _student_user, student = make_student_user("student@example.com", "student-password")
        class_session = make_class_session(teacher=teacher)
        make_enrollment(student, class_session)

        token = _login(client, "teacher@example.com", "teacher-password")
        response = client.get(
            f"/api/v1/schedule/class-sessions/{class_session.id}/roster", headers=_headers(token)
        )
        assert response.status_code == 200
        assert len(response.json()["students"]) == 1

    def test_unassigned_teacher_forbidden(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        _owner_user, owner = make_teacher_user("owner@example.com", "owner-password")
        _other_user, _other = make_teacher_user("other@example.com", "other-password")
        _student_user, student = make_student_user("student@example.com", "student-password")
        class_session = make_class_session(teacher=owner)
        make_enrollment(student, class_session)

        token = _login(client, "other@example.com", "other-password")
        response = client.get(
            f"/api/v1/schedule/class-sessions/{class_session.id}/roster", headers=_headers(token)
        )
        assert response.status_code == 403
