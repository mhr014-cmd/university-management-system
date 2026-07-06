"""
Integration tests: /schedule/*, including the Derived
/schedule/class-sessions and /schedule/enrollments endpoints.

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


class TestCreateClassSession:
    def test_requires_admin(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.post("/api/v1/schedule/class-sessions", json={}, headers=_headers(token))
        assert response.status_code == 403

    def test_admin_creates_class_session(self, client, make_admin_user, make_course, make_teacher_user, make_semester):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        course = make_course()
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "some-password", department=None)
        semester = make_semester()

        response = client.post(
            "/api/v1/schedule/class-sessions",
            json={
                "course_id": str(course.id),
                "teacher_id": str(teacher.id),
                "semester_id": str(semester.id),
                "section_label": "Section A",
            },
            headers=_headers(token),
        )
        assert response.status_code == 201
        assert response.json()["section_label"] == "Section A"

    def test_invalid_teacher_id_returns_422(self, client, make_admin_user, make_course, make_semester):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        course = make_course()
        semester = make_semester()

        response = client.post(
            "/api/v1/schedule/class-sessions",
            json={
                "course_id": str(course.id),
                "teacher_id": "00000000-0000-0000-0000-000000000000",
                "semester_id": str(semester.id),
                "section_label": "Section A",
            },
            headers=_headers(token),
        )
        assert response.status_code == 422


class TestCreateEnrollment:
    def test_duplicate_enrollment_returns_409(self, client, make_admin_user, make_student_user, make_class_session, make_teacher_user):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        _student_user, student = make_student_user("student@example.com", "some-password")
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "some-password")
        class_session = make_class_session(teacher=teacher)

        payload = {"student_id": str(student.id), "class_session_id": str(class_session.id)}
        first = client.post("/api/v1/schedule/enrollments", json=payload, headers=_headers(token))
        assert first.status_code == 201

        second = client.post("/api/v1/schedule/enrollments", json=payload, headers=_headers(token))
        assert second.status_code == 409


class TestScheduleEntryLifecycle:
    def test_create_conflict_and_get_me(
        self,
        client,
        make_admin_user,
        make_student_user,
        make_teacher_user,
        make_class_session,
        make_room,
        make_parent_user,
        link_parent_student,
    ):
        make_admin_user("admin@example.com", "correct-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        _student_user, student = make_student_user("student@example.com", "student-password")
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        room = make_room()

        client.post(
            "/api/v1/schedule/enrollments",
            json={"student_id": str(student.id), "class_session_id": str(class_session.id)},
            headers=_headers(admin_token),
        )

        entry_payload = {
            "class_session_id": str(class_session.id),
            "room_id": str(room.id),
            "teacher_id": str(teacher.id),
            "day_of_week": "Mon",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        }
        create_response = client.post("/api/v1/schedule", json=entry_payload, headers=_headers(admin_token))
        assert create_response.status_code == 201

        # BR-005: overlapping-but-different-start-time conflict.
        conflict_payload = dict(entry_payload, start_time="09:30:00", end_time="10:30:00")
        conflict_response = client.post("/api/v1/schedule", json=conflict_payload, headers=_headers(admin_token))
        assert conflict_response.status_code == 409

        # VR-007.
        invalid_payload = dict(entry_payload, room_id=str(room.id), start_time="11:00:00", end_time="10:00:00")
        invalid_response = client.post("/api/v1/schedule", json=invalid_payload, headers=_headers(admin_token))
        assert invalid_response.status_code == 422

        student_token = _login(client, "student@example.com", "student-password")
        me_response = client.get("/api/v1/schedule/me", headers=_headers(student_token))
        assert me_response.status_code == 200
        assert len(me_response.json()["entries"]) == 1

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        teacher_me_response = client.get("/api/v1/schedule/me", headers=_headers(teacher_token))
        assert teacher_me_response.status_code == 200
        assert len(teacher_me_response.json()["entries"]) == 1

        # Gap closure: a linked Parent can see the same child's timetable
        # via GET /schedule/me + student_id; an unlinked Parent cannot.
        _parent_user, parent = make_parent_user("parent@example.com", "parent-password")
        link_parent_student(parent, student)
        parent_token = _login(client, "parent@example.com", "parent-password")
        parent_response = client.get(
            "/api/v1/schedule/me", params={"student_id": str(student.id)}, headers=_headers(parent_token)
        )
        assert parent_response.status_code == 200
        assert len(parent_response.json()["entries"]) == 1

        no_link_response = client.get("/api/v1/schedule/me", headers=_headers(parent_token))
        assert no_link_response.status_code == 403

    def test_student_forbidden_from_creating_entry(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.post("/api/v1/schedule", json={}, headers=_headers(token))
        assert response.status_code == 403

    def test_delete_entry_returns_204(self, client, make_admin_user, make_teacher_user, make_class_session, make_room):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "some-password")
        class_session = make_class_session(teacher=teacher)
        room = make_room()

        create_response = client.post(
            "/api/v1/schedule",
            json={
                "class_session_id": str(class_session.id),
                "room_id": str(room.id),
                "teacher_id": str(teacher.id),
                "day_of_week": "Tue",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
            },
            headers=_headers(token),
        )
        entry_id = create_response.json()["id"]

        delete_response = client.delete(f"/api/v1/schedule/{entry_id}", headers=_headers(token))
        assert delete_response.status_code == 204

        second_delete = client.delete(f"/api/v1/schedule/{entry_id}", headers=_headers(token))
        assert second_delete.status_code == 404


class TestScheduleConflictsEndpoint:
    def test_requires_admin(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.get("/api/v1/schedule/conflicts", headers=_headers(token))
        assert response.status_code == 403

    def test_returns_empty_when_no_conflicts(self, client, make_admin_user):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        response = client.get("/api/v1/schedule/conflicts", headers=_headers(token))
        assert response.status_code == 200
        assert response.json()["conflicts"] == []


class TestChangeRequestWorkflow:
    def test_full_submit_and_approve_workflow(
        self, client, make_admin_user, make_teacher_user, make_class_session, make_room
    ):
        make_admin_user("admin@example.com", "correct-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        room = make_room()

        entry_response = client.post(
            "/api/v1/schedule",
            json={
                "class_session_id": str(class_session.id),
                "room_id": str(room.id),
                "teacher_id": str(teacher.id),
                "day_of_week": "Wed",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
            },
            headers=_headers(admin_token),
        )
        entry_id = entry_response.json()["id"]

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        request_response = client.post(
            "/api/v1/schedule/change-requests",
            json={
                "schedule_entry_id": entry_id,
                "requested_change": {"start_time": "11:00:00", "end_time": "12:00:00"},
            },
            headers=_headers(teacher_token),
        )
        assert request_response.status_code == 201
        assert request_response.json()["status"] == "pending"
        request_id = request_response.json()["id"]

        resolve_response = client.post(
            f"/api/v1/schedule/change-requests/{request_id}/resolve",
            json={"decision": "approve"},
            headers=_headers(admin_token),
        )
        assert resolve_response.status_code == 200
        assert resolve_response.json()["status"] == "approved"

        # Re-resolving an already-resolved request is a conflict.
        second_resolve = client.post(
            f"/api/v1/schedule/change-requests/{request_id}/resolve",
            json={"decision": "approve"},
            headers=_headers(admin_token),
        )
        assert second_resolve.status_code == 409

        me_response = client.get("/api/v1/schedule/me", headers=_headers(teacher_token))
        entries = me_response.json()["entries"]
        assert entries[0]["start_time"] == "11:00:00"

    def test_other_teacher_cannot_request_change(
        self, client, make_admin_user, make_teacher_user, make_class_session, make_room
    ):
        make_admin_user("admin@example.com", "correct-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        _owner_user, owner = make_teacher_user("owner@example.com", "owner-password")
        _other_user, _other = make_teacher_user("other@example.com", "other-password")
        class_session = make_class_session(teacher=owner)
        room = make_room()

        entry_response = client.post(
            "/api/v1/schedule",
            json={
                "class_session_id": str(class_session.id),
                "room_id": str(room.id),
                "teacher_id": str(owner.id),
                "day_of_week": "Thu",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
            },
            headers=_headers(admin_token),
        )
        entry_id = entry_response.json()["id"]

        other_token = _login(client, "other@example.com", "other-password")
        response = client.post(
            "/api/v1/schedule/change-requests",
            json={
                "schedule_entry_id": entry_id,
                "requested_change": {"start_time": "11:00:00", "end_time": "12:00:00"},
            },
            headers=_headers(other_token),
        )
        assert response.status_code == 403

    def test_room_change_request_is_supported(
        self, client, make_admin_user, make_teacher_user, make_class_session, make_room
    ):
        # Gap closure (production-readiness audit): RequestedChange already
        # supported room_id server-side — this confirms the full path
        # (create with a room change, approve, timetable updates) works.
        make_admin_user("admin@example.com", "correct-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        old_room = make_room(name="Room A")
        new_room = make_room(name="Room B")

        entry_response = client.post(
            "/api/v1/schedule",
            json={
                "class_session_id": str(class_session.id),
                "room_id": str(old_room.id),
                "teacher_id": str(teacher.id),
                "day_of_week": "Wed",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
            },
            headers=_headers(admin_token),
        )
        entry_id = entry_response.json()["id"]

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        request_response = client.post(
            "/api/v1/schedule/change-requests",
            json={"schedule_entry_id": entry_id, "requested_change": {"room_id": str(new_room.id)}},
            headers=_headers(teacher_token),
        )
        request_id = request_response.json()["id"]

        resolve_response = client.post(
            f"/api/v1/schedule/change-requests/{request_id}/resolve",
            json={"decision": "approve"},
            headers=_headers(admin_token),
        )
        assert resolve_response.status_code == 200

        me_response = client.get("/api/v1/schedule/me", headers=_headers(teacher_token))
        assert me_response.json()["entries"][0]["room_name"] == "Room B"

    def test_teacher_notified_after_approval_and_after_rejection(
        self, client, make_admin_user, make_teacher_user, make_class_session, make_room
    ):
        # Gap closure (production-readiness audit): resolving a request
        # previously updated the timetable silently — the requesting
        # Teacher must now be notified of the outcome either way.
        make_admin_user("admin@example.com", "correct-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        room = make_room()

        entry_id = client.post(
            "/api/v1/schedule",
            json={
                "class_session_id": str(class_session.id),
                "room_id": str(room.id),
                "teacher_id": str(teacher.id),
                "day_of_week": "Wed",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
            },
            headers=_headers(admin_token),
        ).json()["id"]

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        approve_request_id = client.post(
            "/api/v1/schedule/change-requests",
            json={"schedule_entry_id": entry_id, "requested_change": {"start_time": "11:00:00", "end_time": "12:00:00"}},
            headers=_headers(teacher_token),
        ).json()["id"]
        client.post(
            f"/api/v1/schedule/change-requests/{approve_request_id}/resolve",
            json={"decision": "approve"},
            headers=_headers(admin_token),
        )

        reject_request_id = client.post(
            "/api/v1/schedule/change-requests",
            json={"schedule_entry_id": entry_id, "requested_change": {"start_time": "13:00:00", "end_time": "14:00:00"}},
            headers=_headers(teacher_token),
        ).json()["id"]
        client.post(
            f"/api/v1/schedule/change-requests/{reject_request_id}/resolve",
            json={"decision": "reject"},
            headers=_headers(admin_token),
        )

        notifications = client.get("/api/v1/notifications", headers=_headers(teacher_token)).json()["items"]
        messages = [n["message"] for n in notifications]
        assert any("approved" in m for m in messages)
        assert any("rejected" in m for m in messages)


class TestListChangeRequests:
    """Gap closure (production-readiness audit): Admin approval queue —
    GET /schedule/change-requests previously didn't exist at all."""

    def test_requires_admin_role(self, client, make_teacher_user):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        token = _login(client, "teacher@example.com", "teacher-password")
        response = client.get("/api/v1/schedule/change-requests", headers=_headers(token))
        assert response.status_code == 403

    def test_lists_only_pending_by_default_and_excludes_resolved(
        self, client, make_admin_user, make_teacher_user, make_class_session, make_room
    ):
        make_admin_user("admin@example.com", "correct-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        room = make_room()

        entry_id = client.post(
            "/api/v1/schedule",
            json={
                "class_session_id": str(class_session.id),
                "room_id": str(room.id),
                "teacher_id": str(teacher.id),
                "day_of_week": "Wed",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
            },
            headers=_headers(admin_token),
        ).json()["id"]

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        pending_request_id = client.post(
            "/api/v1/schedule/change-requests",
            json={"schedule_entry_id": entry_id, "requested_change": {"start_time": "11:00:00", "end_time": "12:00:00"}},
            headers=_headers(teacher_token),
        ).json()["id"]
        resolved_request_id = client.post(
            "/api/v1/schedule/change-requests",
            json={"schedule_entry_id": entry_id, "requested_change": {"start_time": "13:00:00", "end_time": "14:00:00"}},
            headers=_headers(teacher_token),
        ).json()["id"]
        client.post(
            f"/api/v1/schedule/change-requests/{resolved_request_id}/resolve",
            json={"decision": "reject"},
            headers=_headers(admin_token),
        )

        response = client.get("/api/v1/schedule/change-requests", headers=_headers(admin_token))
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == pending_request_id
        assert items[0]["requested_by_teacher_name"] == "Test Teacher"
        assert items[0]["current_room_name"] == room.name
