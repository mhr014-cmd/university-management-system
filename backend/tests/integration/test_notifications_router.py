"""
Integration tests: /notifications/*, including the Milestone 9 mandatory
Notification Domain Rules and all four automatic dispatch triggers,
end-to-end.

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


def _setup_enrolled_student(make_teacher_user, make_student_user, make_class_session, make_enrollment):
    _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
    _student_user, student = make_student_user("student@example.com", "student-password")
    class_session = make_class_session(teacher=teacher)
    make_enrollment(student, class_session)
    return teacher, student, class_session


class TestGetNotifications:
    def test_requires_authentication(self, client):
        response = client.get("/api/v1/notifications")
        assert response.status_code == 401

    def test_empty_feed_for_new_user(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.get("/api/v1/notifications", headers=_headers(token))
        assert response.status_code == 200
        assert response.json() == {"items": [], "unread_count": 0, "total": 0}


class TestMarkAsRead:
    def test_not_found_returns_404(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.put(
            "/api/v1/notifications/00000000-0000-0000-0000-000000000000/read", headers=_headers(token)
        )
        assert response.status_code == 404


class TestScheduleChangeNotification:
    def test_update_notifies_students_and_teacher(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_room, make_schedule_entry
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        entry = make_schedule_entry(class_session, teacher)
        admin_token = _login(client, "admin@example.com", "correct-password")
        student_token = _login(client, "student@example.com", "student-password")
        teacher_token = _login(client, "teacher@example.com", "teacher-password")

        new_room = make_room(name="Room 305")
        response = client.put(
            f"/api/v1/schedule/{entry.id}", json={"room_id": str(new_room.id)}, headers=_headers(admin_token)
        )
        assert response.status_code == 200

        student_notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        teacher_notifs = client.get("/api/v1/notifications", headers=_headers(teacher_token)).json()
        assert any(n["type"] == "schedule_change" for n in student_notifs["items"])
        assert any(n["type"] == "schedule_change" for n in teacher_notifs["items"])
        assert "Room 305" in student_notifs["items"][0]["message"]

    def test_delete_notifies_with_cancellation_message(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        entry = make_schedule_entry(class_session, teacher)
        admin_token = _login(client, "admin@example.com", "correct-password")
        student_token = _login(client, "student@example.com", "student-password")

        response = client.delete(f"/api/v1/schedule/{entry.id}", headers=_headers(admin_token))
        assert response.status_code == 204

        student_notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        cancelled = [n for n in student_notifs["items"] if "cancelled" in n["message"]]
        assert len(cancelled) == 1


class TestAttendanceWarningNotification:
    def test_only_fires_on_threshold_crossing(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        make_schedule_entry(class_session, teacher)
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")

        dates_statuses = [
            ("2026-01-05", "present"),
            ("2026-01-06", "present"),
            ("2026-01-07", "present"),
            ("2026-01-08", "present"),
            ("2026-01-09", "absent"),  # 4/5 = 80% -> not below yet
        ]
        for attendance_date, status in dates_statuses:
            r = client.post(
                "/api/v1/attendance",
                json={
                    "class_session_id": str(class_session.id),
                    "attendance_date": attendance_date,
                    "records": [{"student_id": str(student.id), "status": status}],
                },
                headers=_headers(teacher_token),
            )
            assert r.status_code == 201

        notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        assert sum(1 for n in notifs["items"] if n["type"] == "attendance_warning") == 0

        # Crosses below 80% (4/6 = 66.7%).
        r = client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-10",
                "records": [{"student_id": str(student.id), "status": "absent"}],
            },
            headers=_headers(teacher_token),
        )
        assert r.status_code == 201
        notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        assert sum(1 for n in notifs["items"] if n["type"] == "attendance_warning") == 1

        # Stays below 80% — no repeat notification.
        r = client.post(
            "/api/v1/attendance",
            json={
                "class_session_id": str(class_session.id),
                "attendance_date": "2026-01-11",
                "records": [{"student_id": str(student.id), "status": "absent"}],
            },
            headers=_headers(teacher_token),
        )
        assert r.status_code == 201
        notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        assert sum(1 for n in notifs["items"] if n["type"] == "attendance_warning") == 1


class TestFeeDueNotification:
    def test_notifies_student_and_linked_parent(
        self,
        client,
        make_admin_user,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        link_parent_student,
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        _parent_user, parent = make_parent_user("parent@example.com", "parent-password")
        link_parent_student(parent, student)
        admin_token = _login(client, "admin@example.com", "correct-password")
        student_token = _login(client, "student@example.com", "student-password")
        parent_token = _login(client, "parent@example.com", "parent-password")

        response = client.post(
            "/api/v1/fees",
            json={
                "semester_id": str(class_session.semester_id),
                "name": "Tuition",
                "amount": 5000,
                "due_date": "2030-01-01",
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 201
        assert response.json()["invoices_created"] == 1

        student_notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        parent_notifs = client.get("/api/v1/notifications", headers=_headers(parent_token)).json()
        assert any(n["type"] == "fee_due" for n in student_notifs["items"])
        assert any(n["type"] == "fee_due" for n in parent_notifs["items"])
        assert "5000.00" in student_notifs["items"][0]["message"]


class TestResultPublishedNotification:
    def _build_published_exam(self, client, teacher_token, student_token, class_session_id):
        create_response = client.post(
            "/api/v1/exams",
            json={
                "class_session_id": class_session_id,
                "title": "Final",
                "exam_type": "mcq",
                "time_limit_minutes": 30,
                "questions": [
                    {
                        "question_text": "2 + 2 = ?",
                        "question_type": "mcq",
                        "marks": 5,
                        "order_index": 0,
                        "options": [
                            {"option_text": "3", "is_correct": False},
                            {"option_text": "4", "is_correct": True},
                        ],
                    }
                ],
            },
            headers=_headers(teacher_token),
        )
        exam = create_response.json()
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "open"}, headers=_headers(teacher_token))
        client.post(f"/api/v1/exams/{exam['id']}/start", headers=_headers(student_token))
        mcq_question = exam["questions"][0]
        correct_option = next(o for o in mcq_question["options"] if o["is_correct"])
        client.post(
            f"/api/v1/exams/{exam['id']}/submit",
            json={"answers": [{"question_id": mcq_question["id"], "selected_option_id": correct_option["id"]}]},
            headers=_headers(student_token),
        )
        results = client.get(f"/api/v1/exams/{exam['id']}/results", headers=_headers(teacher_token)).json()
        submission_id = results["submissions"][0]["submission_id"]
        detail = client.get(
            f"/api/v1/exams/{exam['id']}/submissions/{submission_id}", headers=_headers(teacher_token)
        ).json()
        grades = [{"answer_id": q["answer_id"], "awarded_marks": q["marks"]} for q in detail["questions"]]
        client.post(
            f"/api/v1/exams/{exam['id']}/grade",
            json={"submission_id": submission_id, "grades": grades},
            headers=_headers(teacher_token),
        )
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "closed"}, headers=_headers(teacher_token))
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "published"}, headers=_headers(teacher_token))
        return exam

    def test_approve_notifies_student_only(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        admin_token = _login(client, "admin@example.com", "correct-password")
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")

        exam = self._build_published_exam(client, teacher_token, student_token, str(class_session.id))
        client.post(
            f"/api/v1/results/{exam['id']}/submit",
            json={"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]},
            headers=_headers(teacher_token),
        )
        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]

        approve = client.post(
            f"/api/v1/results/{result_id}/approve", json={"decision": "approve"}, headers=_headers(admin_token)
        )
        assert approve.status_code == 200

        student_notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        teacher_notifs = client.get("/api/v1/notifications", headers=_headers(teacher_token)).json()
        assert any(n["type"] == "result_published" for n in student_notifs["items"])
        assert not any(n["type"] == "result_published" for n in teacher_notifs["items"])

    def test_reject_does_not_notify(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        admin_token = _login(client, "admin@example.com", "correct-password")
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")

        exam = self._build_published_exam(client, teacher_token, student_token, str(class_session.id))
        client.post(
            f"/api/v1/results/{exam['id']}/submit",
            json={"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]},
            headers=_headers(teacher_token),
        )
        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]

        reject = client.post(
            f"/api/v1/results/{result_id}/approve",
            json={"decision": "reject", "comment": "needs review"},
            headers=_headers(admin_token),
        )
        assert reject.status_code == 200

        student_notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        assert not any(n["type"] == "result_published" for n in student_notifs["items"])


class TestMarkAsReadWorkflow:
    def test_idempotent_and_ownership_enforced(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment, make_schedule_entry
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        entry = make_schedule_entry(class_session, teacher)
        admin_token = _login(client, "admin@example.com", "correct-password")
        student_token = _login(client, "student@example.com", "student-password")
        teacher_token = _login(client, "teacher@example.com", "teacher-password")

        client.delete(f"/api/v1/schedule/{entry.id}", headers=_headers(admin_token))

        student_notifs = client.get("/api/v1/notifications", headers=_headers(student_token)).json()
        teacher_notifs = client.get("/api/v1/notifications", headers=_headers(teacher_token)).json()
        student_notif_id = student_notifs["items"][0]["id"]
        teacher_notif_id = teacher_notifs["items"][0]["id"]

        first = client.put(f"/api/v1/notifications/{student_notif_id}/read", headers=_headers(student_token))
        second = client.put(f"/api/v1/notifications/{student_notif_id}/read", headers=_headers(student_token))
        assert first.status_code == 200 and first.json()["is_read"] is True
        assert second.status_code == 200 and second.json()["is_read"] is True

        cross_user = client.put(f"/api/v1/notifications/{teacher_notif_id}/read", headers=_headers(student_token))
        assert cross_user.status_code == 404
