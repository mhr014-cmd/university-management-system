"""
Integration tests: /exams/*, including the Milestone 6 mandatory
Examination Domain Rules, BR-001, BR-003, VR-004, VR-006, and the Derived
POST /exams/{id}/start and GET /exams/{id}/submissions/{submission_id}
endpoints, end-to-end.

Full request -> DB -> response cycle against a disposable test database
(see tests/conftest.py). Requires TEST_DATABASE_URL — skipped otherwise.
"""

from datetime import datetime, timedelta, timezone

from tests.conftest import requires_test_database

pytestmark = requires_test_database


def _login(client, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _mcq_exam_payload(class_session_id: str, time_limit_minutes: int = 30) -> dict:
    return {
        "class_session_id": class_session_id,
        "title": "Midterm",
        "exam_type": "mcq",
        "time_limit_minutes": time_limit_minutes,
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
            },
            {
                "question_text": "Explain recursion.",
                "question_type": "short_answer",
                "marks": 10,
                "order_index": 1,
                "options": [],
            },
        ],
    }


def _setup_enrolled_student(make_teacher_user, make_student_user, make_class_session, make_enrollment):
    _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
    _student_user, student = make_student_user("student@example.com", "student-password")
    class_session = make_class_session(teacher=teacher)
    make_enrollment(student, class_session)
    return teacher, student, class_session


class TestCreateExam:
    def test_requires_teacher_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.post("/api/v1/exams", json={}, headers=_headers(token))
        assert response.status_code == 403

    def test_rule6_teacher_must_be_assigned_to_class_session(
        self, client, make_teacher_user, make_class_session
    ):
        _owner_user, owner = make_teacher_user("owner@example.com", "owner-password")
        _other_user, _other = make_teacher_user("other@example.com", "other-password")
        class_session = make_class_session(teacher=owner)
        token = _login(client, "other@example.com", "other-password")

        response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(token)
        )
        assert response.status_code == 403

    def test_mcq_question_without_correct_option_returns_422(
        self, client, make_teacher_user, make_class_session
    ):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        token = _login(client, "teacher@example.com", "teacher-password")

        payload = _mcq_exam_payload(str(class_session.id))
        payload["questions"][0]["options"] = [{"option_text": "3", "is_correct": False}]
        response = client.post("/api/v1/exams", json=payload, headers=_headers(token))
        assert response.status_code == 422

    def test_success_creates_draft_exam(self, client, make_teacher_user, make_class_session):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        token = _login(client, "teacher@example.com", "teacher-password")

        response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(token)
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "draft"
        assert len(body["questions"]) == 2


class TestListAndGetExam:
    def test_draft_exam_hidden_from_student_list_and_get(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam_id = create_response.json()["id"]

        student_token = _login(client, "student@example.com", "student-password")
        list_response = client.get("/api/v1/exams", headers=_headers(student_token))
        assert exam_id not in [e["id"] for e in list_response.json()["items"]]

        get_response = client.get(f"/api/v1/exams/{exam_id}", headers=_headers(student_token))
        assert get_response.status_code == 404

        # Final-polish fix: GET /exams must return a course_name, not just
        # the raw class_session_id, so the frontend Exam List page never
        # falls back to rendering a UUID.
        teacher_list = client.get("/api/v1/exams", headers=_headers(teacher_token)).json()
        listed_exam = next(e for e in teacher_list["items"] if e["id"] == exam_id)
        assert listed_exam["course_name"] == "Intro to CS"

    def test_unenrolled_student_cannot_view_open_exam(
        self, client, make_teacher_user, make_student_user, make_class_session
    ):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        _student_user, _student = make_student_user("student@example.com", "student-password")
        class_session = make_class_session(teacher=teacher)
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam_id = create_response.json()["id"]
        client.put(f"/api/v1/exams/{exam_id}", json={"status": "open"}, headers=_headers(teacher_token))

        student_token = _login(client, "student@example.com", "student-password")
        get_response = client.get(f"/api/v1/exams/{exam_id}", headers=_headers(student_token))
        assert get_response.status_code == 404

    def test_br001_is_correct_hidden_pre_publish_revealed_post_publish(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam_id = create_response.json()["id"]
        client.put(f"/api/v1/exams/{exam_id}", json={"status": "open"}, headers=_headers(teacher_token))

        student_token = _login(client, "student@example.com", "student-password")
        pre_publish = client.get(f"/api/v1/exams/{exam_id}", headers=_headers(student_token))
        assert pre_publish.status_code == 200
        mcq_question = next(q for q in pre_publish.json()["questions"] if q["question_type"] == "mcq")
        assert all(o["is_correct"] is None for o in mcq_question["options"])

        # Teacher always sees is_correct, even pre-publish.
        teacher_view = client.get(f"/api/v1/exams/{exam_id}", headers=_headers(teacher_token))
        mcq_question_teacher = next(q for q in teacher_view.json()["questions"] if q["question_type"] == "mcq")
        assert any(o["is_correct"] is True for o in mcq_question_teacher["options"])

        client.put(f"/api/v1/exams/{exam_id}", json={"status": "closed"}, headers=_headers(teacher_token))
        client.put(f"/api/v1/exams/{exam_id}", json={"status": "published"}, headers=_headers(teacher_token))

        post_publish = client.get(f"/api/v1/exams/{exam_id}", headers=_headers(student_token))
        mcq_question_post = next(q for q in post_publish.json()["questions"] if q["question_type"] == "mcq")
        assert any(o["is_correct"] is True for o in mcq_question_post["options"])


class TestUpdateExam:
    def test_br003_status_cannot_move_backward(self, client, make_teacher_user, make_class_session):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(token)
        )
        exam_id = create_response.json()["id"]
        client.put(f"/api/v1/exams/{exam_id}", json={"status": "open"}, headers=_headers(token))

        response = client.put(f"/api/v1/exams/{exam_id}", json={"status": "draft"}, headers=_headers(token))
        assert response.status_code == 422

    def test_br003_published_exam_cannot_be_edited(self, client, make_teacher_user, make_class_session):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(token)
        )
        exam_id = create_response.json()["id"]
        for status in ("open", "closed", "published"):
            client.put(f"/api/v1/exams/{exam_id}", json={"status": status}, headers=_headers(token))

        response = client.put(f"/api/v1/exams/{exam_id}", json={"title": "New title"}, headers=_headers(token))
        assert response.status_code == 409

    def test_non_creator_teacher_forbidden(self, client, make_teacher_user, make_class_session):
        _owner_user, owner = make_teacher_user("owner@example.com", "owner-password")
        _other_user, _other = make_teacher_user("other@example.com", "other-password")
        class_session = make_class_session(teacher=owner)
        owner_token = _login(client, "owner@example.com", "owner-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(owner_token)
        )
        exam_id = create_response.json()["id"]

        other_token = _login(client, "other@example.com", "other-password")
        response = client.put(f"/api/v1/exams/{exam_id}", json={"title": "New"}, headers=_headers(other_token))
        assert response.status_code == 403


class TestDeleteExam:
    def test_br003_published_exam_cannot_be_deleted(self, client, make_teacher_user, make_class_session):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(token)
        )
        exam_id = create_response.json()["id"]
        for status in ("open", "closed", "published"):
            client.put(f"/api/v1/exams/{exam_id}", json={"status": status}, headers=_headers(token))

        response = client.delete(f"/api/v1/exams/{exam_id}", headers=_headers(token))
        assert response.status_code == 409

    def test_admin_can_delete_unpublished_exam(self, client, make_admin_user, make_teacher_user, make_class_session):
        make_admin_user("admin@example.com", "correct-password")
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        class_session = make_class_session(teacher=teacher)
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam_id = create_response.json()["id"]

        admin_token = _login(client, "admin@example.com", "correct-password")
        response = client.delete(f"/api/v1/exams/{exam_id}", headers=_headers(admin_token))
        assert response.status_code == 204


class TestStartExam:
    def test_requires_student_role(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.post(
            "/api/v1/exams/00000000-0000-0000-0000-000000000000/start", headers=_headers(token)
        )
        assert response.status_code == 403

    def test_rule5_unenrolled_student_forbidden(
        self, client, make_teacher_user, make_student_user, make_class_session
    ):
        _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
        _student_user, _student = make_student_user("student@example.com", "student-password")
        class_session = make_class_session(teacher=teacher)
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam_id = create_response.json()["id"]
        client.put(f"/api/v1/exams/{exam_id}", json={"status": "open"}, headers=_headers(teacher_token))

        student_token = _login(client, "student@example.com", "student-password")
        response = client.post(f"/api/v1/exams/{exam_id}/start", headers=_headers(student_token))
        assert response.status_code == 403

    def test_exam_not_open_rejected(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam_id = create_response.json()["id"]  # still draft

        student_token = _login(client, "student@example.com", "student-password")
        response = client.post(f"/api/v1/exams/{exam_id}/start", headers=_headers(student_token))
        assert response.status_code == 409

    def test_idempotent_start_returns_200_second_time(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam_id = create_response.json()["id"]
        client.put(f"/api/v1/exams/{exam_id}", json={"status": "open"}, headers=_headers(teacher_token))

        student_token = _login(client, "student@example.com", "student-password")
        first = client.post(f"/api/v1/exams/{exam_id}/start", headers=_headers(student_token))
        assert first.status_code == 201
        second = client.post(f"/api/v1/exams/{exam_id}/start", headers=_headers(student_token))
        assert second.status_code == 200
        assert first.json()["submission_id"] == second.json()["submission_id"]
        assert first.json()["started_at"] == second.json()["started_at"]


class TestSubmitExam:
    def _create_open_exam(self, client, teacher_token, class_session_id, time_limit_minutes=30):
        create_response = client.post(
            "/api/v1/exams",
            json=_mcq_exam_payload(class_session_id, time_limit_minutes=time_limit_minutes),
            headers=_headers(teacher_token),
        )
        exam = create_response.json()
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "open"}, headers=_headers(teacher_token))
        return exam

    def test_submit_without_start_returns_409(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))

        student_token = _login(client, "student@example.com", "student-password")
        response = client.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": []}, headers=_headers(student_token))
        assert response.status_code == 409

    def test_success_submits_answers(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        mcq_question = next(q for q in exam["questions"] if q["question_type"] == "mcq")
        correct_option = next(o for o in mcq_question["options"] if o["is_correct"])

        student_token = _login(client, "student@example.com", "student-password")
        client.post(f"/api/v1/exams/{exam['id']}/start", headers=_headers(student_token))

        response = client.post(
            f"/api/v1/exams/{exam['id']}/submit",
            json={"answers": [{"question_id": mcq_question["id"], "selected_option_id": correct_option["id"]}]},
            headers=_headers(student_token),
        )
        assert response.status_code == 201
        assert response.json()["status"] == "submitted"

    def test_duplicate_submission_rejected(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))

        student_token = _login(client, "student@example.com", "student-password")
        client.post(f"/api/v1/exams/{exam['id']}/start", headers=_headers(student_token))
        client.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": []}, headers=_headers(student_token))

        second = client.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": []}, headers=_headers(student_token))
        assert second.status_code == 409

        # A student who has already submitted cannot start a second attempt.
        restart = client.post(f"/api/v1/exams/{exam['id']}/start", headers=_headers(student_token))
        assert restart.status_code == 409

    def test_vr004_time_limit_exceeded_returns_409(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment, db_session
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id), time_limit_minutes=10)

        student_token = _login(client, "student@example.com", "student-password")
        start_response = client.post(f"/api/v1/exams/{exam['id']}/start", headers=_headers(student_token))
        submission_id = start_response.json()["submission_id"]

        # Backdate started_at directly in the DB to simulate the time
        # limit having elapsed — the only way to exercise VR-004 without
        # an actual multi-minute sleep in the test suite.
        from app.models.exam_submission import ExamSubmission

        submission = db_session.get(ExamSubmission, submission_id)
        submission.started_at = datetime.now(timezone.utc) - timedelta(minutes=20)
        db_session.commit()

        response = client.post(
            f"/api/v1/exams/{exam['id']}/submit", json={"answers": []}, headers=_headers(student_token)
        )
        assert response.status_code == 409
        assert "time limit" in response.json()["error"]["message"].lower()


class TestGradingWorkflow:
    def _create_open_exam(self, client, teacher_token, class_session_id):
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(class_session_id), headers=_headers(teacher_token)
        )
        exam = create_response.json()
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "open"}, headers=_headers(teacher_token))
        return exam

    def _submit_full_answers(self, client, exam, student_token):
        mcq_question = next(q for q in exam["questions"] if q["question_type"] == "mcq")
        correct_option = next(o for o in mcq_question["options"] if o["is_correct"])
        short_answer_question = next(q for q in exam["questions"] if q["question_type"] == "short_answer")

        client.post(f"/api/v1/exams/{exam['id']}/start", headers=_headers(student_token))
        return client.post(
            f"/api/v1/exams/{exam['id']}/submit",
            json={
                "answers": [
                    {"question_id": mcq_question["id"], "selected_option_id": correct_option["id"]},
                    {"question_id": short_answer_question["id"], "answer_text": "Recursion is when a function calls itself."},
                ]
            },
            headers=_headers(student_token),
        )

    def test_requires_teacher_role_for_grading(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        student_token = _login(client, "student@example.com", "student-password")
        self._submit_full_answers(client, exam, student_token)

        response = client.post(
            f"/api/v1/exams/{exam['id']}/grade",
            json={"submission_id": "00000000-0000-0000-0000-000000000000", "grades": []},
            headers=_headers(student_token),
        )
        assert response.status_code == 403

    def test_vr006_awarded_marks_exceeding_max_returns_422(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        student_token = _login(client, "student@example.com", "student-password")
        self._submit_full_answers(client, exam, student_token)

        results = client.get(f"/api/v1/exams/{exam['id']}/results", headers=_headers(teacher_token))
        # Final-polish fix: GET /exams/{id}/results must return a
        # student_name, not just the raw student_id, so the Teacher Grading
        # Interface never falls back to rendering a truncated UUID.
        assert results.json()["submissions"][0]["student_name"] == "Test Student"
        submission_id = results.json()["submissions"][0]["submission_id"]
        detail = client.get(
            f"/api/v1/exams/{exam['id']}/submissions/{submission_id}", headers=_headers(teacher_token)
        )
        mcq_answer = next(q for q in detail.json()["questions"] if q["question_type"] == "mcq")

        response = client.post(
            f"/api/v1/exams/{exam['id']}/grade",
            json={"submission_id": submission_id, "grades": [{"answer_id": mcq_answer["answer_id"], "awarded_marks": 999}]},
            headers=_headers(teacher_token),
        )
        assert response.status_code == 422

    def test_full_grading_workflow_marks_submission_graded_and_allows_regrade(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        student_token = _login(client, "student@example.com", "student-password")
        self._submit_full_answers(client, exam, student_token)

        results = client.get(f"/api/v1/exams/{exam['id']}/results", headers=_headers(teacher_token))
        submission_id = results.json()["submissions"][0]["submission_id"]
        detail_response = client.get(
            f"/api/v1/exams/{exam['id']}/submissions/{submission_id}", headers=_headers(teacher_token)
        )
        assert detail_response.status_code == 200
        questions = detail_response.json()["questions"]
        assert all(q["answer_id"] is not None for q in questions)

        grade_payload = {
            "submission_id": submission_id,
            "grades": [{"answer_id": q["answer_id"], "awarded_marks": q["marks"]} for q in questions],
        }
        grade_response = client.post(
            f"/api/v1/exams/{exam['id']}/grade", json=grade_payload, headers=_headers(teacher_token)
        )
        assert grade_response.status_code == 200
        assert grade_response.json()["status"] == "graded"
        assert grade_response.json()["total_awarded_marks"] == 15.0

        # Re-save with a lower mark (regrade / "Save Grades" is re-saveable).
        regrade_payload = {
            "submission_id": submission_id,
            "grades": [{"answer_id": questions[0]["answer_id"], "awarded_marks": 0}],
        }
        regrade_response = client.post(
            f"/api/v1/exams/{exam['id']}/grade", json=regrade_payload, headers=_headers(teacher_token)
        )
        assert regrade_response.status_code == 200
        assert regrade_response.json()["total_awarded_marks"] == 10.0

    def test_non_creator_teacher_cannot_view_submission_detail(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        _other_user, _other = make_teacher_user("other@example.com", "other-password")
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        student_token = _login(client, "student@example.com", "student-password")
        self._submit_full_answers(client, exam, student_token)

        results = client.get(f"/api/v1/exams/{exam['id']}/results", headers=_headers(teacher_token))
        submission_id = results.json()["submissions"][0]["submission_id"]

        other_token = _login(client, "other@example.com", "other-password")
        response = client.get(
            f"/api/v1/exams/{exam['id']}/submissions/{submission_id}", headers=_headers(other_token)
        )
        assert response.status_code == 403

    def test_admin_can_view_submission_detail(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        student_token = _login(client, "student@example.com", "student-password")
        self._submit_full_answers(client, exam, student_token)

        results = client.get(f"/api/v1/exams/{exam['id']}/results", headers=_headers(teacher_token))
        submission_id = results.json()["submissions"][0]["submission_id"]

        admin_token = _login(client, "admin@example.com", "correct-password")
        response = client.get(
            f"/api/v1/exams/{exam['id']}/submissions/{submission_id}", headers=_headers(admin_token)
        )
        assert response.status_code == 200

    def test_submission_detail_requires_teacher_or_admin(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        student_token = _login(client, "student@example.com", "student-password")
        self._submit_full_answers(client, exam, student_token)

        results = client.get(f"/api/v1/exams/{exam['id']}/results", headers=_headers(teacher_token))
        submission_id = results.json()["submissions"][0]["submission_id"]

        response = client.get(
            f"/api/v1/exams/{exam['id']}/submissions/{submission_id}", headers=_headers(student_token)
        )
        assert response.status_code == 403


class TestGetResults:
    def test_requires_teacher_or_admin(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.get(
            "/api/v1/exams/00000000-0000-0000-0000-000000000000/results", headers=_headers(token)
        )
        assert response.status_code == 403


class TestGetMySubmissionDetail:
    """Feature 2 (final-verification-pass addition): Student Feedback View
    — GET /exams/{examId}/my-submission. Read-only, no grading changes.
    A Student sees only their own submission; a linked Parent may view a
    child's, per the existing ownership convention; feedback/awarded_marks
    stay hidden until the exam is published (same BR-001 gate as
    GET /exams/{id})."""

    def _create_open_exam(self, client, teacher_token, class_session_id):
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(class_session_id), headers=_headers(teacher_token)
        )
        exam = create_response.json()
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "open"}, headers=_headers(teacher_token))
        return exam

    def _submit_and_grade(self, client, exam, teacher_token, student_token, *, feedback="Well done"):
        mcq_question = next(q for q in exam["questions"] if q["question_type"] == "mcq")
        correct_option = next(o for o in mcq_question["options"] if o["is_correct"])
        client.post(f"/api/v1/exams/{exam['id']}/start", headers=_headers(student_token))
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
        # _mcq_exam_payload has 2 questions (mcq + short_answer) but this
        # helper only answers the mcq one — skip the unanswered question
        # (answer_id None) rather than sending an invalid grade for it.
        grades = [
            {"answer_id": q["answer_id"], "awarded_marks": q["marks"], "feedback": feedback}
            for q in detail["questions"]
            if q["answer_id"] is not None
        ]
        client.post(
            f"/api/v1/exams/{exam['id']}/grade",
            json={"submission_id": submission_id, "grades": grades},
            headers=_headers(teacher_token),
        )

    def test_requires_student_or_parent_role(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))

        response = client.get(f"/api/v1/exams/{exam['id']}/my-submission", headers=_headers(teacher_token))
        assert response.status_code == 403

    def test_student_sees_own_submission(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        self._submit_and_grade(client, exam, teacher_token, student_token)

        response = client.get(f"/api/v1/exams/{exam['id']}/my-submission", headers=_headers(student_token))
        assert response.status_code == 200
        assert response.json()["student_id"] == str(student.id)

    def test_feedback_hidden_before_exam_published(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        self._submit_and_grade(client, exam, teacher_token, student_token, feedback="Great job")
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "closed"}, headers=_headers(teacher_token))

        response = client.get(f"/api/v1/exams/{exam['id']}/my-submission", headers=_headers(student_token))
        assert response.status_code == 200
        body = response.json()
        assert all(q["feedback"] is None for q in body["questions"])
        assert all(q["awarded_marks"] is None for q in body["questions"])

    def test_feedback_visible_after_exam_published(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        self._submit_and_grade(client, exam, teacher_token, student_token, feedback="Great job")
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "closed"}, headers=_headers(teacher_token))
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "published"}, headers=_headers(teacher_token))

        response = client.get(f"/api/v1/exams/{exam['id']}/my-submission", headers=_headers(student_token))
        assert response.status_code == 200
        body = response.json()
        assert body["questions"][0]["feedback"] == "Great job"
        assert body["questions"][0]["awarded_marks"] == 5.0

    def test_student_cannot_view_another_students_submission(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        self._submit_and_grade(client, exam, teacher_token, student_token)
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "closed"}, headers=_headers(teacher_token))
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "published"}, headers=_headers(teacher_token))

        _other_user, other_student = make_student_user("other-student@example.com", "other-password")
        other_token = _login(client, "other-student@example.com", "other-password")

        # The other student never submitted this exam at all — their own
        # (nonexistent) submission is what's resolved, not the first
        # student's, so this 404s rather than leaking someone else's data.
        response = client.get(f"/api/v1/exams/{exam['id']}/my-submission", headers=_headers(other_token))
        assert response.status_code == 404

    def test_parent_without_student_id_rejected(
        self, client, make_teacher_user, make_student_user, make_parent_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        make_parent_user("parent@example.com", "parent-password")
        parent_token = _login(client, "parent@example.com", "parent-password")
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))

        response = client.get(f"/api/v1/exams/{exam['id']}/my-submission", headers=_headers(parent_token))
        assert response.status_code == 403

    def test_parent_without_link_rejected(
        self, client, make_teacher_user, make_student_user, make_parent_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        make_parent_user("parent@example.com", "parent-password")  # not linked
        parent_token = _login(client, "parent@example.com", "parent-password")
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))

        response = client.get(
            f"/api/v1/exams/{exam['id']}/my-submission?student_id={student.id}", headers=_headers(parent_token)
        )
        assert response.status_code == 403

    def test_linked_parent_sees_childs_submission_and_feedback(
        self,
        client,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        link_parent_student,
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        _parent_user, parent = make_parent_user("parent@example.com", "parent-password")
        link_parent_student(parent, student)

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = self._create_open_exam(client, teacher_token, str(class_session.id))
        self._submit_and_grade(client, exam, teacher_token, student_token, feedback="Nicely explained")
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "closed"}, headers=_headers(teacher_token))
        client.put(f"/api/v1/exams/{exam['id']}", json={"status": "published"}, headers=_headers(teacher_token))

        parent_token = _login(client, "parent@example.com", "parent-password")
        response = client.get(
            f"/api/v1/exams/{exam['id']}/my-submission?student_id={student.id}", headers=_headers(parent_token)
        )
        assert response.status_code == 200
        body = response.json()
        assert body["student_id"] == str(student.id)
        assert body["questions"][0]["feedback"] == "Nicely explained"


class TestListExamsParentAccess:
    """Gap closure: proposal §5 promises Parents "upcoming exam dates" for
    their linked child — GET /exams scoped by an ownership-checked
    student_id, same convention as GET /attendance/me, /results/me,
    /fees/me, /schedule/me."""

    def test_parent_without_student_id_rejected(self, client, make_parent_user):
        make_parent_user("parent@example.com", "parent-password")
        token = _login(client, "parent@example.com", "parent-password")
        response = client.get("/api/v1/exams", headers=_headers(token))
        assert response.status_code == 403

    def test_parent_without_link_rejected(
        self, client, make_teacher_user, make_student_user, make_parent_user, make_class_session, make_enrollment
    ):
        _teacher, student, _class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        make_parent_user("parent@example.com", "parent-password")  # not linked
        token = _login(client, "parent@example.com", "parent-password")

        response = client.get(f"/api/v1/exams?student_id={student.id}", headers=_headers(token))
        assert response.status_code == 403

    def test_linked_parent_sees_open_exam_but_not_draft(
        self,
        client,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        link_parent_student,
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        _parent_user, parent = make_parent_user("parent@example.com", "parent-password")
        link_parent_student(parent, student)

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam_id = create_response.json()["id"]

        parent_token = _login(client, "parent@example.com", "parent-password")
        # Still a draft — hidden from the Parent, same as from the Student.
        draft_list = client.get(f"/api/v1/exams?student_id={student.id}", headers=_headers(parent_token))
        assert draft_list.status_code == 200
        assert exam_id not in [e["id"] for e in draft_list.json()["items"]]

        client.put(f"/api/v1/exams/{exam_id}", json={"status": "open"}, headers=_headers(teacher_token))

        open_list = client.get(f"/api/v1/exams?student_id={student.id}", headers=_headers(parent_token))
        assert open_list.status_code == 200
        listed_exam = next(e for e in open_list.json()["items"] if e["id"] == exam_id)
        assert listed_exam["course_name"] == "Intro to CS"

    def test_parent_never_sees_unrelated_students_exams(
        self,
        client,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        make_course,
        make_semester,
        link_parent_student,
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        _other_user, other_student = make_student_user("other-student@example.com", "other-password")
        # Distinct course/code and semester — make_class_session's own
        # make_course()/make_semester() defaults ("CS101"/"Fall 2026")
        # would otherwise collide with the ones already created above for
        # `class_session`.
        other_course = make_course(name="Other Course", code="CS102")
        other_semester = make_semester(name="Other Semester")
        other_class_session = make_class_session(teacher=teacher, course=other_course, semester=other_semester)
        make_enrollment(other_student, other_class_session)
        _parent_user, parent = make_parent_user("parent@example.com", "parent-password")
        link_parent_student(parent, student)

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        other_exam = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(other_class_session.id)), headers=_headers(teacher_token)
        ).json()
        client.put(f"/api/v1/exams/{other_exam['id']}", json={"status": "open"}, headers=_headers(teacher_token))

        parent_token = _login(client, "parent@example.com", "parent-password")
        response = client.get(f"/api/v1/exams?student_id={student.id}", headers=_headers(parent_token))
        assert response.status_code == 200
        assert other_exam["id"] not in [e["id"] for e in response.json()["items"]]
