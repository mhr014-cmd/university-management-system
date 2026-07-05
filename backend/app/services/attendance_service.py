"""
Business logic service: attendance (see docs/Requirement_Analysis.md
FR-026-FR-032, BR-007, BR-008, VR-005, and the Milestone 5 mandatory
Attendance Domain Rules).

Calls AttendanceRepository/ScheduleRepository/UserRepository/reference-data
repositories, never the ORM session directly, per CLAUDE.md §6. Every
RBAC/ownership/business-rule check happens here, before any database
write — routers only shape the request/response and enforce role-only
RBAC via dependencies; this service enforces everything else.
"""

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.notifications import dispatcher
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.reference_data_repository import CourseRepository, DepartmentRepository, SemesterRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.attendance import (
    LOW_ATTENDANCE_THRESHOLD,
    AttendanceMarkRequest,
    AttendanceMeQuery,
    AttendanceMeResponse,
    AttendanceRecordRead,
    AttendanceReportEntry,
    AttendanceReportScope,
    AttendanceReportsResponse,
    AttendanceUpdateRequest,
    ClassAttendanceEntry,
    ClassAttendanceResponse,
    ClassSessionAttendanceSummary,
)

attendance_repo = AttendanceRepository()
schedule_repo = ScheduleRepository()
user_repo = UserRepository()
department_repo = DepartmentRepository()
semester_repo = SemesterRepository()
course_repo = CourseRepository()

# Statuses that count as "attended" for percentage purposes. "excused" is
# treated as neutral (excluded from both numerator and denominator) since
# an excused absence should not count against the student the way an
# unexcused one does. Neither Database_Design.md nor API_Contract.md
# defines this formula explicitly — this is a documented engineering
# assumption (same class of gap as BR-008's threshold), recorded in
# Requirement_Analysis.md Section 14 as a new resolved-with-assumption item.
_ATTENDED_STATUSES = {"present", "late"}
_EXCLUDED_FROM_DENOMINATOR = {"excused"}


def _percentage(records: list) -> float:
    countable = [r for r in records if r.status not in _EXCLUDED_FROM_DENOMINATOR]
    if not countable:
        return 100.0
    attended = sum(1 for r in countable if r.status in _ATTENDED_STATUSES)
    return round((attended / len(countable)) * 100, 2)


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _invalid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


class AttendanceService:
    # --- POST /attendance (FR-027) ---------------------------------------

    def mark_attendance(
        self, session: Session, current_user: User, payload: AttendanceMarkRequest
    ) -> list[AttendanceRecordRead]:
        teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)

        # Rule 2: class session exists. (class_session has no is_active/
        # status column in Database_Design.md §6.9 — "active" is
        # interpreted as "exists"; there is no other schema-backed notion
        # of an inactive class session to check against.)
        class_session = schedule_repo.get_class_session(session, payload.class_session_id)
        if class_session is None:
            raise _not_found("class_session_id not found")

        # Rule 7: Teacher may only mark attendance for a class session they
        # are assigned to (System_Architecture.md Section 6 ownership check).
        if class_session.teacher_id != teacher.id:
            raise _forbidden("You are not the assigned Teacher for this class session.")

        # Rule 3: a schedule entry must exist for this class session — a
        # class session with no scheduled meeting time/room is not yet a
        # real, occurring class to take attendance for.
        if not schedule_repo.class_session_has_schedule_entry(session, payload.class_session_id):
            raise _invalid("This class session has no schedule entry — it is not yet scheduled to occur.")

        # VR-005: no future-dated attendance beyond today.
        if payload.attendance_date > date.today():
            raise _invalid("attendance_date cannot be in the future.")

        # Validate every record BEFORE any database write (Rule 10) — a
        # single invalid row must reject the whole batch, not partially
        # commit some students' attendance and reject others silently.
        student_users: dict[uuid.UUID, User] = {}
        for record_input in payload.records:
            # Rule 1: student exists and is active.
            student_row = user_repo.get_student_with_user(session, record_input.student_id)
            if student_row is None:
                raise _invalid(f"student_id {record_input.student_id} does not reference an existing student")
            _student, student_user = student_row
            if not student_user.is_active:
                raise _invalid(f"student_id {record_input.student_id} refers to a deactivated account")
            student_users[record_input.student_id] = student_user

            # Rule 4/Rule 6: student must be enrolled in this exact class
            # session — this is what prevents marking attendance for
            # unrelated students (Rule 6) as well as enforcing FR-027's
            # actual enrollment requirement.
            if schedule_repo.get_enrollment(session, record_input.student_id, payload.class_session_id) is None:
                raise _invalid(
                    f"student_id {record_input.student_id} is not enrolled in this class session"
                )

            # Rule 5/VR-005: no duplicate record for the same
            # student/class_session/date.
            if (
                attendance_repo.get_record(
                    session, record_input.student_id, payload.class_session_id, payload.attendance_date
                )
                is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Attendance already recorded for student_id {record_input.student_id} on this date.",
                )

        # Milestone 9 attendance_warning dispatch: capture each student's
        # per-class-session percentage BEFORE this batch is written, so it
        # can be compared against the percentage AFTER, to detect a genuine
        # threshold crossing (resolved during the M9 pre-implementation
        # review, confirmed with the user) rather than repeating the
        # notification on every marking while chronically below 80%.
        percentages_before: dict[uuid.UUID, float] = {}
        course_name: str | None = None
        for student_id in student_users:
            rows = attendance_repo.list_for_student(session, student_id, class_session_id=payload.class_session_id)
            percentages_before[student_id] = _percentage([r for r, _course in rows])
            if course_name is None and rows:
                course_name = rows[0][1].name

        created: list[AttendanceRecordRead] = []
        try:
            for record_input in payload.records:
                record = attendance_repo.create_record(
                    session,
                    student_id=record_input.student_id,
                    class_session_id=payload.class_session_id,
                    marked_by_teacher_id=teacher.id,
                    attendance_date=payload.attendance_date,
                    status=record_input.status,
                )
                created.append(record)
            session.commit()
        except IntegrityError:
            # Defense-in-depth backstop behind the pre-flight duplicate
            # check above (per CLAUDE.md Section 10 — "do not rely solely
            # on database constraints", but the DB UniqueConstraint still
            # catches a race the pre-flight check alone cannot).
            session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate attendance record.")

        for record in created:
            session.refresh(record)

        # Course name wasn't known pre-write if this is the student's very
        # first record for this class session — resolve it post-write if so.
        if course_name is None and created:
            class_session = schedule_repo.get_class_session(session, payload.class_session_id)
            if class_session is not None:
                course = course_repo.get(session, class_session.course_id)
                course_name = course.name if course is not None else None

        # Domain Rule 4: dispatch only after the batch commit above has
        # succeeded.
        if course_name is not None:
            for student_id in student_users:
                rows_after = attendance_repo.list_for_student(
                    session, student_id, class_session_id=payload.class_session_id
                )
                percentage_after = _percentage([r for r, _course in rows_after])
                if percentages_before[student_id] >= LOW_ATTENDANCE_THRESHOLD > percentage_after:
                    dispatcher.notify_attendance_warning(
                        session,
                        student_id=student_id,
                        student_user_id=student_users[student_id].id,
                        course_name=course_name,
                    )

        return [AttendanceRecordRead.model_validate(record) for record in created]

    # --- PUT /attendance/{id} (FR-029) -----------------------------------

    def update_attendance(
        self, session: Session, current_user: User, record_id: uuid.UUID, payload: AttendanceUpdateRequest
    ) -> AttendanceRecordRead:
        record = attendance_repo.get_by_id(session, record_id)
        if record is None:
            raise _not_found("Attendance record not found")

        # Rule 7 (Admin bypasses the ownership check; Teacher must be the
        # class session's assigned Teacher — same check as marking, since
        # under this data model the marking Teacher is always the class
        # session's assigned Teacher, per app/models/schedule_entry.py's
        # single-teacher-per-class-session design).
        if current_user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
            class_session = schedule_repo.get_class_session(session, record.class_session_id)
            if class_session is None or class_session.teacher_id != teacher.id:
                raise _forbidden("You are not the assigned Teacher for this class session.")

        attendance_repo.update_status(session, record, payload.status)
        session.commit()
        session.refresh(record)
        return AttendanceRecordRead.model_validate(record)

    # --- GET /attendance/me (FR-026, FR-031/BR-008; FR-032 for Parent) ----

    def get_me(self, session: Session, current_user: User, query: AttendanceMeQuery) -> AttendanceMeResponse:
        if current_user.role == "student":
            student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            target_student_id = student.id
        elif current_user.role == "parent":
            parent = user_repo.get_parent_profile_by_user_id(session, current_user.id)
            # Domain Rule 9/BR-007: a Parent may only view a linked child's
            # attendance, and must say which child — same convention as
            # fee_service.get_my_fees / result_service.get_my_results.
            if query.student_id is None or not user_repo.parent_has_linked_student(
                session, parent.id, query.student_id
            ):
                raise _forbidden("You may only view attendance for a linked student.")
            target_student_id = query.student_id
        else:
            raise _forbidden("Only Student or Parent callers may use this endpoint.")

        rows = attendance_repo.list_for_student(
            session,
            target_student_id,
            class_session_id=query.class_session_id,
            date_from=query.date_from,
            date_to=query.date_to,
        )

        by_class_session: dict[uuid.UUID, dict] = {}
        for record, course in rows:
            bucket = by_class_session.setdefault(
                record.class_session_id, {"course_name": course.name, "records": []}
            )
            bucket["records"].append(record)

        summaries = []
        for class_session_id, bucket in by_class_session.items():
            percentage = _percentage(bucket["records"])
            summaries.append(
                ClassSessionAttendanceSummary(
                    class_session_id=class_session_id,
                    course_name=bucket["course_name"],
                    percentage=percentage,
                    low_attendance_warning=percentage < LOW_ATTENDANCE_THRESHOLD,
                    records=[{"date": r.attendance_date, "status": r.status} for r in bucket["records"]],
                )
            )

        all_records = [record for record, _course in rows]
        overall_percentage = _percentage(all_records)
        return AttendanceMeResponse(
            overall_percentage=overall_percentage,
            low_attendance_warning=overall_percentage < LOW_ATTENDANCE_THRESHOLD,
            by_class_session=summaries,
        )

    # --- GET /attendance/{classId} (FR-028, FR-032/BR-007 for Parent) ----

    def get_class_attendance(
        self,
        session: Session,
        current_user: User,
        class_session_id: uuid.UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        student_id: uuid.UUID | None,
    ) -> ClassAttendanceResponse:
        class_session = schedule_repo.get_class_session(session, class_session_id)
        if class_session is None:
            raise _not_found("Class session not found")

        if current_user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
            if class_session.teacher_id != teacher.id:
                raise _forbidden("You are not the assigned Teacher for this class session.")
        elif current_user.role == "parent":
            # Rule 9: Parent access is exactly what API_Contract.md §4.3
            # documents — scoped to their own linked child via
            # parent_student_link, and only through this endpoint. No
            # implicit broader access is granted.
            if student_id is None:
                raise _forbidden("Parent access requires a student_id scoped to a linked child.")
            parent = user_repo.get_parent_profile_by_user_id(session, current_user.id)
            if not user_repo.parent_has_linked_student(session, parent.id, student_id):
                raise _forbidden("You are not linked to this student.")
        # Admin: no additional ownership check.

        records = attendance_repo.list_for_class_session(
            session, class_session_id, date_from=date_from, date_to=date_to, student_id=student_id
        )
        return ClassAttendanceResponse(
            class_session_id=class_session_id,
            records=[
                ClassAttendanceEntry(id=r.id, student_id=r.student_id, date=r.attendance_date, status=r.status)
                for r in records
            ],
        )

    # --- GET /attendance/reports (FR-030) --------------------------------

    def get_reports(
        self,
        session: Session,
        department_id: uuid.UUID | None,
        semester_id: uuid.UUID | None,
    ) -> AttendanceReportsResponse:
        if department_id is not None and department_repo.get(session, department_id) is None:
            raise _invalid("department_id does not reference an existing department")
        if semester_id is not None and semester_repo.get(session, semester_id) is None:
            raise _invalid("semester_id does not reference an existing semester")

        records = attendance_repo.list_for_report(session, department_id=department_id, semester_id=semester_id)

        by_student: dict[uuid.UUID, list] = {}
        for record in records:
            by_student.setdefault(record.student_id, []).append(record)

        # Single batch lookup for every student's display name — not one
        # query per student — so this report never becomes an N+1 query.
        students = user_repo.list_students_by_ids(session, list(by_student.keys()))
        name_by_student_id = {s.id: f"{s.first_name} {s.last_name}" for s in students}

        summary = [
            AttendanceReportEntry(
                student_id=student_id,
                student_name=name_by_student_id.get(student_id, "Unknown Student"),
                percentage=_percentage(student_records),
            )
            for student_id, student_records in by_student.items()
        ]
        return AttendanceReportsResponse(
            scope=AttendanceReportScope(department_id=department_id, semester_id=semester_id), summary=summary
        )
