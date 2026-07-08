"""
Integration tests: /results/*, including the Milestone 7 mandatory
Results & Academic Records Domain Rules, BR-002, the GPA formula, and the
Derived GET /results/pending endpoint, end-to-end.

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


def _build_published_exam(client, teacher_token, student_token, class_session_id):
    """Create an exam, take/grade/publish it, returning the exam dict."""
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
    grades = [{"answer_id": q["answer_id"], "awarded_marks": q["marks"]} for q in detail["questions"]]
    client.post(
        f"/api/v1/exams/{exam['id']}/grade",
        json={"submission_id": submission_id, "grades": grades},
        headers=_headers(teacher_token),
    )

    client.put(f"/api/v1/exams/{exam['id']}", json={"status": "closed"}, headers=_headers(teacher_token))
    client.put(f"/api/v1/exams/{exam['id']}", json={"status": "published"}, headers=_headers(teacher_token))
    return exam


def _setup_enrolled_student(make_teacher_user, make_student_user, make_class_session, make_enrollment):
    _teacher_user, teacher = make_teacher_user("teacher@example.com", "teacher-password")
    _student_user, student = make_student_user("student@example.com", "student-password")
    class_session = make_class_session(teacher=teacher)
    make_enrollment(student, class_session)
    return teacher, student, class_session


class TestSubmitResults:
    def test_requires_teacher_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.post(
            "/api/v1/results/00000000-0000-0000-0000-000000000000/submit",
            json={"results": []},
            headers=_headers(token),
        )
        assert response.status_code == 403

    def test_rule4_exam_not_published_rejected(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam = create_response.json()  # still draft

        response = client.post(
            f"/api/v1/results/{exam['id']}/submit",
            json={"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]},
            headers=_headers(teacher_token),
        )
        assert response.status_code == 409

    def test_success_then_duplicate_submission_returns_409(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))

        payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        first = client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        assert first.status_code == 201
        assert first.json()["status"] == "submitted"

        second = client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        assert second.status_code == 409

    def test_rule6_student_never_graded_on_exam_returns_422(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))

        _other_user, other_student = make_student_user("other@example.com", "other-password")
        make_enrollment(other_student, class_session)

        payload = {"results": [{"student_id": str(other_student.id), "grade_letter": "A", "grade_point": 4.0}]}
        response = client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        assert response.status_code == 422

    def test_grade_point_above_max_rejected(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        """V1.1 stabilization fix: grade_point must not exceed the
        conventional 4.0 GPA scale (Requirement_Analysis.md A-004) — an
        out-of-range value would silently corrupt GPA computation and the
        printed transcript."""
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam = create_response.json()

        response = client.post(
            f"/api/v1/results/{exam['id']}/submit",
            json={"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.5}]},
            headers=_headers(teacher_token),
        )
        assert response.status_code == 422

    def test_grade_point_negative_rejected(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam = create_response.json()

        response = client.post(
            f"/api/v1/results/{exam['id']}/submit",
            json={"results": [{"student_id": str(student.id), "grade_letter": "F", "grade_point": -1.0}]},
            headers=_headers(teacher_token),
        )
        assert response.status_code == 422

    def test_grade_letter_too_long_rejected(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        """V1.1 stabilization fix: grade_letter stays free text (no fixed
        letter-grade enum — see report_service.py's documented rationale)
        but is bounded so an unreasonably long string can't be submitted."""
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        create_response = client.post(
            "/api/v1/exams", json=_mcq_exam_payload(str(class_session.id)), headers=_headers(teacher_token)
        )
        exam = create_response.json()

        response = client.post(
            f"/api/v1/results/{exam['id']}/submit",
            json={"results": [{"student_id": str(student.id), "grade_letter": "A" * 11, "grade_point": 4.0}]},
            headers=_headers(teacher_token),
        )
        assert response.status_code == 422

    def test_grade_point_at_max_boundary_accepted(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        """4.0 exactly (the top of the conventional scale) must still be accepted."""
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))

        response = client.post(
            f"/api/v1/results/{exam['id']}/submit",
            json={"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]},
            headers=_headers(teacher_token),
        )
        assert response.status_code == 201

    def test_rejected_result_can_be_resubmitted(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))

        payload = {"results": [{"student_id": str(student.id), "grade_letter": "C", "grade_point": 2.0}]}
        submit_response = client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]

        reject_response = client.post(
            f"/api/v1/results/{result_id}/approve",
            json={"decision": "reject", "comment": "Needs correction"},
            headers=_headers(admin_token),
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["status"] == "rejected"

        resubmit_payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        resubmit_response = client.post(
            f"/api/v1/results/{exam['id']}/submit", json=resubmit_payload, headers=_headers(teacher_token)
        )
        assert resubmit_response.status_code == 201


class TestApproveOrReject:
    def test_requires_admin_role(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.post(
            "/api/v1/results/00000000-0000-0000-0000-000000000000/approve",
            json={"decision": "approve"},
            headers=_headers(token),
        )
        assert response.status_code == 403

    def test_reject_requires_comment(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))

        payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]

        response = client.post(
            f"/api/v1/results/{result_id}/approve", json={"decision": "reject"}, headers=_headers(admin_token)
        )
        assert response.status_code == 422

    def test_approve_publishes_and_reveals_to_student(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))

        payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))

        before = client.get("/api/v1/results/me", headers=_headers(student_token))
        assert before.json()["semesters"] == []

        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]
        approve = client.post(
            f"/api/v1/results/{result_id}/approve", json={"decision": "approve"}, headers=_headers(admin_token)
        )
        assert approve.status_code == 200
        assert approve.json()["status"] == "published"

        after = client.get("/api/v1/results/me", headers=_headers(student_token))
        assert after.status_code == 200
        body = after.json()
        assert len(body["semesters"]) == 1
        assert body["semesters"][0]["gpa"] == 4.0
        assert body["semesters"][0]["courses"][0]["grade_letter"] == "A"


class TestGetMyResults:
    def test_requires_student_or_parent_role(self, client, make_admin_user):
        make_admin_user("admin@example.com", "correct-password")
        token = _login(client, "admin@example.com", "correct-password")
        response = client.get("/api/v1/results/me", headers=_headers(token))
        assert response.status_code == 403

    def test_rule13_parent_without_student_id_returns_403(self, client, make_parent_user):
        make_parent_user("parent@example.com", "parent-password")
        token = _login(client, "parent@example.com", "parent-password")
        response = client.get("/api/v1/results/me", headers=_headers(token))
        assert response.status_code == 403

    def test_rule13_parent_with_link_can_view(
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

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))
        payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]
        client.post(f"/api/v1/results/{result_id}/approve", json={"decision": "approve"}, headers=_headers(admin_token))

        parent_token = _login(client, "parent@example.com", "parent-password")
        response = client.get(
            "/api/v1/results/me", params={"student_id": str(student.id)}, headers=_headers(parent_token)
        )
        assert response.status_code == 200
        assert len(response.json()["semesters"]) == 1

    def test_rule13_parent_without_link_to_this_student_returns_403(
        self, client, make_teacher_user, make_student_user, make_parent_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        make_parent_user("parent@example.com", "parent-password")  # not linked

        parent_token = _login(client, "parent@example.com", "parent-password")
        response = client.get(
            "/api/v1/results/me", params={"student_id": str(student.id)}, headers=_headers(parent_token)
        )
        assert response.status_code == 403


class TestGetResultsForExam:
    """Feature 1 (final-verification-pass addition): Teacher Results View
    — GET /results/exam/{examId}. Read-only; a Teacher can check the
    approval status of results they've submitted for their own exams."""

    def test_requires_teacher_role(self, client, make_student_user):
        make_student_user("student@example.com", "correct-password")
        token = _login(client, "student@example.com", "correct-password")
        response = client.get(
            "/api/v1/results/exam/00000000-0000-0000-0000-000000000000", headers=_headers(token)
        )
        assert response.status_code == 403

    def test_non_creator_teacher_forbidden(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))

        make_teacher_user("other-teacher@example.com", "other-password")
        other_teacher_token = _login(client, "other-teacher@example.com", "other-password")

        response = client.get(f"/api/v1/results/exam/{exam['id']}", headers=_headers(other_teacher_token))
        assert response.status_code == 403

    def test_exam_not_found_returns_404(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "teacher-password")
        token = _login(client, "teacher@example.com", "teacher-password")
        response = client.get(
            "/api/v1/results/exam/00000000-0000-0000-0000-000000000000", headers=_headers(token)
        )
        assert response.status_code == 404

    def test_no_results_submitted_yet_returns_empty_list(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))

        response = client.get(f"/api/v1/results/exam/{exam['id']}", headers=_headers(teacher_token))
        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_teacher_sees_submitted_status_before_admin_approval(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))
        payload = {"results": [{"student_id": str(student.id), "grade_letter": "B", "grade_point": 3.0}]}
        client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))

        response = client.get(f"/api/v1/results/exam/{exam['id']}", headers=_headers(teacher_token))
        assert response.status_code == 200
        body = response.json()
        assert body["exam_title"] == "Final"
        assert len(body["results"]) == 1
        assert body["results"][0]["status"] == "submitted"
        assert body["results"][0]["grade_letter"] == "B"
        assert body["results"][0]["student_name"]

    def test_teacher_sees_published_status_after_admin_approval(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))
        payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]
        client.post(f"/api/v1/results/{result_id}/approve", json={"decision": "approve"}, headers=_headers(admin_token))

        response = client.get(f"/api/v1/results/exam/{exam['id']}", headers=_headers(teacher_token))
        assert response.status_code == 200
        assert response.json()["results"][0]["status"] == "published"


class TestGetPendingResults:
    def test_requires_admin_role(self, client, make_teacher_user):
        make_teacher_user("teacher@example.com", "correct-password")
        token = _login(client, "teacher@example.com", "correct-password")
        response = client.get("/api/v1/results/pending", headers=_headers(token))
        assert response.status_code == 403

    def test_groups_results_by_exam(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))
        payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))

        response = client.get("/api/v1/results/pending", headers=_headers(admin_token))
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["exam_title"] == "Final"
        assert items[0]["course_name"] is not None
        assert len(items[0]["results"]) == 1


class TestTranscript:
    def test_student_cannot_download_others_transcript(
        self, client, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        _teacher, _student, _cs = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        _other_user, other_student = make_student_user("other@example.com", "other-password")
        token = _login(client, "student@example.com", "student-password")

        response = client.get(f"/api/v1/results/{other_student.id}/transcript", headers=_headers(token))
        assert response.status_code == 403

    def test_own_transcript_downloads_as_pdf(
        self, client, make_admin_user, make_teacher_user, make_student_user, make_class_session, make_enrollment
    ):
        make_admin_user("admin@example.com", "correct-password")
        teacher, student, class_session = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))
        payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]
        client.post(f"/api/v1/results/{result_id}/approve", json={"decision": "approve"}, headers=_headers(admin_token))

        response = client.get(f"/api/v1/results/{student.id}/transcript", headers=_headers(student_token))
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")

    def test_empty_transcript_returns_200_not_409(self, client, make_student_user):
        _student_user, student = make_student_user("student@example.com", "student-password")
        token = _login(client, "student@example.com", "student-password")

        response = client.get(f"/api/v1/results/{student.id}/transcript", headers=_headers(token))
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF")

    def test_unlinked_parent_cannot_download_transcript(
        self, client, make_teacher_user, make_student_user, make_parent_user, make_class_session, make_enrollment
    ):
        # Gap closure (production-readiness audit): Parent transcript
        # download is scoped to a linked child, same as GET /results/me.
        _teacher, student, _cs = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        make_parent_user("parent@example.com", "parent-password")  # not linked
        parent_token = _login(client, "parent@example.com", "parent-password")

        response = client.get(f"/api/v1/results/{student.id}/transcript", headers=_headers(parent_token))
        assert response.status_code == 403

    def test_linked_parent_downloads_transcript(
        self,
        client,
        make_teacher_user,
        make_student_user,
        make_parent_user,
        make_class_session,
        make_enrollment,
        link_parent_student,
    ):
        _teacher, student, _cs = _setup_enrolled_student(
            make_teacher_user, make_student_user, make_class_session, make_enrollment
        )
        _parent_user, parent = make_parent_user("parent@example.com", "parent-password")
        link_parent_student(parent, student)
        parent_token = _login(client, "parent@example.com", "parent-password")

        response = client.get(f"/api/v1/results/{student.id}/transcript", headers=_headers(parent_token))
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF")


class TestResultPublishedParentNotification:
    """Gap closure (production-readiness audit): a linked Parent must be
    notified, same as the Student, when a result is approved/published."""

    def test_linked_parent_receives_result_published_notification(
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

        teacher_token = _login(client, "teacher@example.com", "teacher-password")
        student_token = _login(client, "student@example.com", "student-password")
        admin_token = _login(client, "admin@example.com", "correct-password")
        exam = _build_published_exam(client, teacher_token, student_token, str(class_session.id))
        payload = {"results": [{"student_id": str(student.id), "grade_letter": "A", "grade_point": 4.0}]}
        client.post(f"/api/v1/results/{exam['id']}/submit", json=payload, headers=_headers(teacher_token))
        pending = client.get("/api/v1/results/pending", headers=_headers(admin_token)).json()
        result_id = pending["items"][0]["results"][0]["result_id"]
        client.post(f"/api/v1/results/{result_id}/approve", json={"decision": "approve"}, headers=_headers(admin_token))

        parent_token = _login(client, "parent@example.com", "parent-password")
        notifications = client.get("/api/v1/notifications", headers=_headers(parent_token)).json()
        assert any(n["type"] == "result_published" for n in notifications["items"])
