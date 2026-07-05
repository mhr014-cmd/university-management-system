"""
Notification generation/dispatch event hooks (see API_Contract.md §8.3 for
the full trigger/recipient/message-template table).

Domain Rule 4: every function here is called by the originating service
*after* that service's own `session.commit()` has already succeeded —
dispatch is a side effect of a successful business operation, never a
precondition for one.

Domain Rule 14: notification creation must never break the originating
transaction. Every public function below catches and logs any exception
internally rather than letting it propagate — by the time these are
called, the business transaction they're reporting on has already
committed and must not be affected by a failure here.

Domain Rule 17: every message is a fixed, server-side template
(interpolating only trusted, server-computed values — course/room names
resolved from the database, never a frontend-supplied string).

Domain Rule 15: batch dispatch (schedule-change to a class roster,
fee-due to a student + linked parents) only ever writes recipients
already resolved from FK-backed repository queries (Enrollment/
ParentStudentLink) — there is no per-recipient validation step that can
fail independently, so "validate all before writing" is satisfied
structurally by construction.
"""

import logging
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository

notification_repo = NotificationRepository()
user_repo = UserRepository()

logger = logging.getLogger("app.notifications")


def _safe_dispatch(session: Session, source: str, build) -> None:
    try:
        build()
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Notification dispatch failed in %s — originating transaction is unaffected.", source)


def notify_result_published(
    session: Session, *, student_user_id: uuid.UUID, course_name: str, semester_name: str
) -> None:
    def _build() -> None:
        notification_repo.create(
            session,
            user_id=student_user_id,
            type="result_published",
            message=f"Result published: {course_name} {semester_name}",
        )

    _safe_dispatch(session, "notify_result_published", _build)


def notify_schedule_change(
    session: Session,
    *,
    student_user_ids: list[uuid.UUID],
    teacher_user_id: uuid.UUID,
    course_name: str,
    room_name: str | None = None,
    cancelled: bool = False,
) -> None:
    message = (
        f"Schedule change: {course_name} class cancelled"
        if cancelled
        else f"Schedule change: {course_name} moved to {room_name}"
    )

    def _build() -> None:
        for user_id in [*student_user_ids, teacher_user_id]:
            notification_repo.create(session, user_id=user_id, type="schedule_change", message=message)

    _safe_dispatch(session, "notify_schedule_change", _build)


def notify_attendance_warning(
    session: Session, *, student_id: uuid.UUID, student_user_id: uuid.UUID, course_name: str
) -> None:
    # Gap closure (post-M11 audit): the proposal (Section 5, Parent —
    # "Attendance summary") explicitly promises Parents "automatic alerts
    # for absences" — this previously only notified the Student, matching
    # every linked Parent onto the same fan-out pattern already used by
    # notify_fee_due (Domain Rule 15: recipients resolved from
    # ParentStudentLink, no per-recipient validation step required).
    message = f"Attendance warning: {course_name} below 80%"

    def _build() -> None:
        notification_repo.create(session, user_id=student_user_id, type="attendance_warning", message=message)
        for parent_user_id in user_repo.list_parent_user_ids_for_student(session, student_id):
            notification_repo.create(session, user_id=parent_user_id, type="attendance_warning", message=message)

    _safe_dispatch(session, "notify_attendance_warning", _build)


def notify_fee_due(
    session: Session, *, student_id: uuid.UUID, student_user_id: uuid.UUID, amount: float, due_date: date
) -> None:
    message = f"Fee due: {amount:.2f} due {due_date.isoformat()}"

    def _build() -> None:
        notification_repo.create(session, user_id=student_user_id, type="fee_due", message=message)
        for parent_user_id in user_repo.list_parent_user_ids_for_student(session, student_id):
            notification_repo.create(session, user_id=parent_user_id, type="fee_due", message=message)

    _safe_dispatch(session, "notify_fee_due", _build)
