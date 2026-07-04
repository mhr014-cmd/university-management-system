"""
Business logic service: result (see docs/Requirement_Analysis.md
FR-033-FR-037, BR-002, and the Milestone 7 mandatory Results & Academic
Records Domain Rules).

Calls ResultRepository/ExamRepository/ScheduleRepository/UserRepository/
reference-data repositories, never the ORM session directly, per
CLAUDE.md §6. Every RBAC/ownership/business-rule check happens here,
before any database write — routers only shape the request/response and
enforce role-only RBAC via dependencies.

Domain Rule 9/10 (never modify Examination/Submission/Answer/QuestionGrade
while generating Results; Results is a separate domain that only
*consumes* examination data): every read of `exam`/`exam_submission`/
`answer`/`question_grade` in this module is read-only — no method here
ever calls a mutating ExamRepository method.

GPA formula (resolves Requirement_Analysis.md §14 item 6, per that
document's own A-004 assumption): a credit-hour-weighted average of
`grade_point` across a semester's `published` results —
`sum(grade_point * course.credit_hours) / sum(course.credit_hours)`. This
is the one and only place that formula is implemented; `grade_letter`/
`grade_point` themselves are never computed from raw exam marks anywhere
in this codebase — per API_Contract.md §5.2, the submitting Teacher
supplies both directly.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.result import Result
from app.models.user import User
from app.repositories.exam_repository import ExamRepository
from app.repositories.reference_data_repository import CourseRepository, SemesterRepository
from app.repositories.result_repository import ResultRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.result import (
    PendingResultDetailEntry,
    PendingResultQueueEntry,
    PendingResultsResponse,
    ResultApprovalRequest,
    ResultApprovalResponse,
    ResultCourseEntry,
    ResultSemesterEntry,
    ResultSubmitRequest,
    ResultSubmitResponse,
    ResultsMeResponse,
)

result_repo = ResultRepository()
exam_repo = ExamRepository()
schedule_repo = ScheduleRepository()
user_repo = UserRepository()
course_repo = CourseRepository()
semester_repo = SemesterRepository()


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _invalid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _build_semester_entries(session: Session, results: list[Result]) -> list[ResultSemesterEntry]:
    by_semester: dict[uuid.UUID, list[Result]] = {}
    for r in results:
        by_semester.setdefault(r.semester_id, []).append(r)

    entries = []
    for semester_id, rows in by_semester.items():
        semester = semester_repo.get(session, semester_id)
        courses = []
        weighted_sum = 0.0
        credit_total = 0
        for row in rows:
            course = course_repo.get(session, row.course_id)
            if course is None or row.grade_point is None:
                continue
            courses.append(
                ResultCourseEntry(
                    course_id=course.id,
                    course_name=course.name,
                    grade_letter=row.grade_letter or "",
                    grade_point=float(row.grade_point),
                )
            )
            weighted_sum += float(row.grade_point) * course.credit_hours
            credit_total += course.credit_hours
        gpa = round(weighted_sum / credit_total, 2) if credit_total > 0 else 0.0
        entries.append(
            ResultSemesterEntry(
                semester_id=semester_id,
                semester_name=semester.name if semester else "",
                gpa=gpa,
                courses=courses,
            )
        )
    entries.sort(key=lambda e: e.semester_name, reverse=True)
    return entries


class ResultService:
    # --- GET /results/me (FR-033, FR-037) ----------------------------------

    def get_my_results(
        self,
        session: Session,
        current_user: User,
        *,
        semester_id: uuid.UUID | None,
        student_id: uuid.UUID | None,
    ) -> ResultsMeResponse:
        if semester_id is not None and semester_repo.get(session, semester_id) is None:
            raise _invalid("semester_id does not reference an existing semester")

        if current_user.role == "student":
            student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            target_student_id = student.id
        elif current_user.role == "parent":
            parent = user_repo.get_parent_profile_by_user_id(session, current_user.id)
            # Domain Rule 13: Parents may access only linked students' results.
            if student_id is None or not user_repo.parent_has_linked_student(session, parent.id, student_id):
                raise _forbidden("You may only view results for a linked student.")
            target_student_id = student_id
        else:
            raise _forbidden("Only Student or Parent callers may use this endpoint.")

        # Domain Rule 12 / BR-001-BR-002: only published results are visible.
        results = result_repo.list_for_student(
            session, target_student_id, semester_id=semester_id, status="published"
        )
        return ResultsMeResponse(semesters=_build_semester_entries(session, results))

    # --- POST /results/{examId}/submit (FR-034) ----------------------------

    def submit_results(
        self, session: Session, current_user: User, exam_id: uuid.UUID, payload: ResultSubmitRequest
    ) -> ResultSubmitResponse:
        teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)

        # Domain Rule 3: the referenced examination must exist.
        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")
        # Domain Rule 14: Teachers may only act on courses/classes they manage.
        if exam.created_by_teacher_id != teacher.id:
            raise _forbidden("You are not the creator of this exam.")
        # Domain Rule 4: the exam must be completed and published before it
        # can contribute to Results.
        if exam.status != "published":
            raise _conflict("This exam is not published yet.")

        class_session = schedule_repo.get_class_session(session, exam.class_session_id)
        course_id = class_session.course_id
        semester_id = class_session.semester_id

        # Domain Rule 5: grading must be complete for every submission of
        # this exam before any of its results can be submitted.
        submissions = exam_repo.list_submissions_for_exam(session, exam_id)
        if not submissions or any(s.status != "graded" for s in submissions):
            raise _conflict("This exam is not fully graded yet.")

        submissions_by_student = {s.student_id: s for s in submissions}

        # Pass 1 — validate the entire batch before writing anything
        # (Domain Rule 15 / "all validation before any write").
        existing_by_student: dict[uuid.UUID, Result | None] = {}
        for entry in payload.results:
            student_with_user = user_repo.get_student_with_user(session, entry.student_id)
            if student_with_user is None:
                raise _not_found(f"student_id {entry.student_id} does not exist")
            student, user = student_with_user
            # Domain Rule 1: student must exist and be active.
            if not user.is_active:
                raise _invalid(f"student_id {entry.student_id} is not active")
            # Domain Rule 2: student must be enrolled in this exam's class.
            if schedule_repo.get_enrollment(session, student.id, exam.class_session_id) is None:
                raise _invalid(f"student_id {entry.student_id} is not enrolled in this exam's class")
            # Domain Rule 6: the student's QuestionGrade data must belong
            # to this exact examination and student — i.e. they must have
            # an actually-graded submission for this exam, not a
            # hand-typed grade for a student never graded here.
            submission = submissions_by_student.get(student.id)
            if submission is None or submission.status != "graded":
                raise _invalid(f"student_id {entry.student_id} was never graded on this exam")

            existing = result_repo.get_by_student_course_semester(session, student.id, course_id, semester_id)
            # Domain Rule 7: duplicate prevention, with the documented
            # resubmission-after-reject exception (Database_Design.md
            # §6.21's Milestone 7 design note).
            if existing is not None and existing.status in ("submitted", "published"):
                raise _conflict(f"A result already exists for student_id {entry.student_id} in this course/semester")
            existing_by_student[entry.student_id] = existing

        # Pass 2 — all validation passed; write the whole batch.
        now = datetime.now(timezone.utc)
        for entry in payload.results:
            existing = existing_by_student[entry.student_id]
            if existing is not None:
                result_repo.update_for_resubmission(
                    session,
                    existing,
                    exam_id=exam_id,
                    submitted_by_teacher_id=teacher.id,
                    grade_letter=entry.grade_letter,
                    grade_point=entry.grade_point,
                    submitted_at=now,
                )
            else:
                result_repo.create(
                    session,
                    student_id=entry.student_id,
                    course_id=course_id,
                    semester_id=semester_id,
                    exam_id=exam_id,
                    submitted_by_teacher_id=teacher.id,
                    grade_letter=entry.grade_letter,
                    grade_point=entry.grade_point,
                    submitted_at=now,
                )
        session.commit()

        return ResultSubmitResponse(exam_id=exam_id, status="submitted", submitted_at=now)

    # --- GET /results/pending (Derived, API_Contract.md Section 5.3) ------

    def get_pending_results(self, session: Session, status_filter: str) -> PendingResultsResponse:
        results = result_repo.list_by_status(session, status_filter)

        groups: dict[tuple, list[Result]] = {}
        for r in results:
            key = (r.exam_id, r.course_id, r.submitted_by_teacher_id, r.submitted_at)
            groups.setdefault(key, []).append(r)

        items = []
        for (exam_id, course_id, teacher_id, submitted_at), rows in groups.items():
            exam = exam_repo.get_exam(session, exam_id) if exam_id is not None else None
            course = course_repo.get(session, course_id)
            teacher_with_user = user_repo.get_teacher_with_user(session, teacher_id)
            teacher_name = (
                f"{teacher_with_user[0].first_name} {teacher_with_user[0].last_name}" if teacher_with_user else ""
            )

            detail_entries = []
            for row in rows:
                student_with_user = user_repo.get_student_with_user(session, row.student_id)
                student_name = (
                    f"{student_with_user[0].first_name} {student_with_user[0].last_name}" if student_with_user else ""
                )
                detail_entries.append(
                    PendingResultDetailEntry(
                        result_id=row.id,
                        student_id=row.student_id,
                        student_name=student_name,
                        grade_letter=row.grade_letter,
                        grade_point=float(row.grade_point) if row.grade_point is not None else None,
                    )
                )

            items.append(
                PendingResultQueueEntry(
                    exam_id=exam_id,
                    exam_title=exam.title if exam else None,
                    course_id=course_id,
                    course_name=course.name if course else "",
                    submitted_by_teacher_id=teacher_id,
                    submitted_by_teacher_name=teacher_name,
                    submitted_at=submitted_at,
                    status=rows[0].status,
                    results=detail_entries,
                )
            )

        items.sort(key=lambda i: i.submitted_at, reverse=True)
        return PendingResultsResponse(items=items)

    # --- POST /results/{id}/approve (FR-035) --------------------------------

    def approve_or_reject(
        self, session: Session, current_user: User, result_id: uuid.UUID, payload: ResultApprovalRequest
    ) -> ResultApprovalResponse:
        admin = user_repo.get_admin_profile_by_user_id(session, current_user.id)

        result = result_repo.get(session, result_id)
        if result is None:
            raise _not_found("Result not found")
        if result.status != "submitted":
            raise _conflict("This result is not awaiting approval.")
        if payload.decision == "reject" and not payload.comment:
            raise _invalid("A comment is required when rejecting a result.")

        now = datetime.now(timezone.utc)
        if payload.decision == "approve":
            result_repo.mark_approved(session, result, admin_id=admin.id, approved_at=now)
        else:
            result_repo.mark_rejected(session, result, admin_id=admin.id, approved_at=now)
        session.commit()
        session.refresh(result)

        return ResultApprovalResponse(id=result.id, status=result.status, approved_at=result.approved_at)

    # --- GET /results/{studentId}/transcript (FR-036) -----------------------

    def get_transcript_data(
        self, session: Session, current_user: User, student_id: uuid.UUID
    ) -> tuple[str, list[ResultSemesterEntry]]:
        student_with_user = user_repo.get_student_with_user(session, student_id)
        if student_with_user is None:
            raise _not_found("Student not found")
        student, user = student_with_user
        if not user.is_active:
            raise _not_found("Student not found")

        if current_user.role == "student":
            own_student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            if own_student.id != student_id:
                raise _forbidden("You may only download your own transcript.")
        elif current_user.role != "admin":
            raise _forbidden("Only the Student themself or an Admin may download this transcript.")

        results = result_repo.list_for_student(session, student_id, status="published")
        semester_entries = _build_semester_entries(session, results)
        student_name = f"{student.first_name} {student.last_name}"
        return student_name, semester_entries
