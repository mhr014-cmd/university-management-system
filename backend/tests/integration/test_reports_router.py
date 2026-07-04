"""
Integration tests: /results/reports, /fees/reports, /fees/overdue/notify
(Milestone 10 Reporting Requirements), end-to-end.

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


def _mcq_exam_payload(class_session_id: str) -> dict:
    return {
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
    }


def _build_published_result(client, teacher_token, student_token, admin_token, class_session_id, student_id, *, awarded_marks=5):
    """Create+take+grade+publish an exam, then submit+approve a Result for it. Returns the result dict."""
    create_response = client.post(
        "/api/v1/exams", json=_mcq_exam_payload(class_session_id), headers=_headers(teacher_token)
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
    grades = [{"answer_id": q["answer_id"], "awarded_marks": awarded_marks} for q in detail["questions"]]
    client.post(
        f"/api/v1/exams/{exam['id']}/grade",
        json={"submission_id": submission_id, "grades": grades},
        headers=_headers(teacher_token),
    )
    client.put(f"/api/v1/exams/{exam['id']}", json={"status": "closed"}, headers=_headers(teacher_token))
    client.put(f"/api/v1/exams/{exam['id']}", json={"status": "published"}, headers=_headers(teacher_token))

    grade_point = 4.0 if awarded_marks > 0 else 0.0
    grade_letter = "A" if awarded_marks > 0 else "F"
    client.post(
        f"/api/v1/results/{exam['id']}/submit",
        json={"results": [{"student_id": str(student_id), "grade_letter": grade_letter, "grade_point": grade_point}]},
        headers=_headers(teacher_token),
    )
    pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
    result_id = pending["items"][0]["results"][0]["result_id"]
    approve = client.post(
        f"/api/v1/results/{result_id}/approve", json={"decision": "approve"}, headers=_headers(admin_token)
    )
    assert approve.status_code == 200
    return approve.json()


def _setup_enrolled_student(make_teacher_user, make_student_user, make_class_session, make_enrollment, department=None):
    _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password", department=department)
    _student_user, student = make_student_user("student@example.com", "student-password", department=department)
    class_session = make_class_session(teacher=teacher)
    make_enrollment(student, class_session)
    return teacher, student, class_session


class TestGetResultsReport:
    def test_requires_admin_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.get("/api/v1/results/reports", headers=_headers(token))
        assert response.status_code == 403

    def test_invalid_department_rejected(self, client, make_admin_user):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        response = client.get(
            "/api/v1/results/reports",
            params={"department_id": "00000000-0000-0000-0000-000000000000"},
            headers=_headers(token),
        )
        assert response.status_code == 422

    def test_average_gpa_and_pass_fail_from_published_results_only(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        _admin_user, _admin = make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        admin_token = _login(client, "admin@example.com", "correct-password")
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")

        _build_published_result(client, teacher_token, student_token, admin_token, str(class_session.id), student.id)

        response = client.get("/api/v1/results/reports", headers=_headers(admin_token))
        assert response.status_code == 200
        body = response.json()
        assert body["pass_count"] == 1
        assert body["fail_count"] == 0
        assert body["average_gpa"] == 4.0
        assert {"grade_letter": "A", "count": 1} in body["grade_distribution"]


class TestGetFeesReport:
    def test_requires_admin_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.get("/api/v1/fees/reports", headers=_headers(token))
        assert response.status_code == 403

    def test_totals_reflect_payments_and_overdue_subset(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        admin_token = _login(client, "admin@example.com", "correct-password")

        fs = client.post(
            "/api/v1/fees",
            json={"semester_id": str(class_session.semester_id), "name": "Tuition", "amount": 10000, "due_date": "2020-01-01"},
            headers=_headers(admin_token),
        ).json()
        client.post(
            "/api/v1/fees/payments",
            json={"student_id": str(student.id), "fee_structure_id": fs["id"], "amount": 4000, "payment_date": "2026-06-01T00:00:00Z"},
            headers=_headers(admin_token),
        )

        response = client.get("/api/v1/fees/reports", headers=_headers(admin_token))
        assert response.status_code == 200
        body = response.json()
        assert body["total_collected"] == 4000.0
        assert body["total_outstanding"] == 6000.0
        assert body["total_overdue"] == 6000.0


class TestNotifyOverdueAccounts:
    def test_requires_admin_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.post(
            "/api/v1/fees/overdue/notify", json={"student_ids": [], "scope": "all_overdue"}, headers=_headers(token)
        )
        assert response.status_code == 403

    def test_scope_selected_rejects_student_without_overdue_invoice(self, client, make_admin_user, make_student_user):
        make_admin_user("admin@example.com", "correct-password")
        _student_user, student = make_student_user("student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")

        response = client.post(
            "/api/v1/fees/overdue/notify",
            json={"student_ids": [str(student.id)], "scope": "selected"},
            headers=_headers(admin_token),
        )
        assert response.status_code == 422

    def test_scope_all_overdue_notifies_and_dispatches_notification(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        admin_token = _login(client, "admin@example.com", "correct-password")
        student_token = _login(client, "student@example.com", "student-password")

        client.post(
            "/api/v1/fees",
            json={"semester_id": str(class_session.semester_id), "name": "Tuition", "amount": 2000, "due_date": "2020-01-01"},
            headers=_headers(admin_token),
        )

        response = client.post(
            "/api/v1/fees/overdue/notify", json={"student_ids": [], "scope": "all_overdue"}, headers=_headers(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["notified_count"] == 1

        # Reuses the existing Notification Dispatcher — the student now has
        # a fee_due notification, no second/parallel notification system.
        notifications = client.get("/api/v1/notifications", headers=_headers(student_token))
        assert notifications.status_code == 200
        assert any(n["type"] == "fee_due" for n in notifications.json()["items"])
