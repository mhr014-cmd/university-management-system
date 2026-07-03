"""
Business logic service: schedule (see docs/Requirement_Analysis.md
FR-045-FR-051, BR-004, BR-005, VR-007).

Calls ScheduleRepository/UserRepository/reference-data repositories, never
the ORM session directly, per CLAUDE.md §6.
"""

import uuid
from datetime import datetime, time, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.reference_data_repository import CourseRepository, RoomRepository, SemesterRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.schedule import (
    ClassSessionCreate,
    ClassSessionRead,
    EnrollmentCreate,
    EnrollmentRead,
    ScheduleChangeRequestCreate,
    ScheduleChangeRequestCreateResponse,
    ScheduleChangeRequestResolve,
    ScheduleChangeRequestResolveResponse,
    ScheduleConflict,
    ScheduleConflictsResponse,
    ScheduleEntryCreate,
    ScheduleEntryRead,
    ScheduleEntryUpdate,
    ScheduleMeEntry,
    ScheduleMeResponse,
)

schedule_repo = ScheduleRepository()
user_repo = UserRepository()
course_repo = CourseRepository()
room_repo = RoomRepository()
semester_repo = SemesterRepository()

_ENTRY_NOT_FOUND = "Schedule entry not found"


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _invalid_reference(field: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"{field} does not reference an existing row"
    )


class ScheduleService:
    # --- class_session (Derived, API_Contract.md Section 7.8) -------------

    def create_class_session(self, session: Session, payload: ClassSessionCreate) -> ClassSessionRead:
        if course_repo.get(session, payload.course_id) is None:
            raise _invalid_reference("course_id")
        if user_repo.get_teacher_with_user(session, payload.teacher_id) is None:
            raise _invalid_reference("teacher_id")
        if semester_repo.get(session, payload.semester_id) is None:
            raise _invalid_reference("semester_id")

        class_session = schedule_repo.create_class_session(
            session,
            course_id=payload.course_id,
            teacher_id=payload.teacher_id,
            semester_id=payload.semester_id,
            section_label=payload.section_label,
        )
        session.commit()
        session.refresh(class_session)
        return ClassSessionRead.model_validate(class_session)

    # --- enrollment (Derived, API_Contract.md Section 7.9) -----------------

    def create_enrollment(self, session: Session, payload: EnrollmentCreate) -> EnrollmentRead:
        if user_repo.get_student_with_user(session, payload.student_id) is None:
            raise _invalid_reference("student_id")
        if schedule_repo.get_class_session(session, payload.class_session_id) is None:
            raise _invalid_reference("class_session_id")

        try:
            enrollment = schedule_repo.create_enrollment(
                session, student_id=payload.student_id, class_session_id=payload.class_session_id
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already enrolled in this class session.")
        session.refresh(enrollment)
        return EnrollmentRead.model_validate(enrollment)

    # --- schedule_entry (API_Contract.md Section 7.1-7.5) -------------------

    def get_me(self, session: Session, current_user: User) -> ScheduleMeResponse:
        if current_user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
            rows = schedule_repo.list_entries_for_teacher(session, teacher.id)
        else:
            student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            class_session_ids = schedule_repo.list_class_session_ids_for_student(session, student.id)
            rows = schedule_repo.list_entries_for_class_sessions(session, class_session_ids)

        entries = [
            ScheduleMeEntry(
                schedule_entry_id=entry.id,
                class_session_id=entry.class_session_id,
                course_name=course.name,
                room_name=room.name,
                day_of_week=entry.day_of_week,
                start_time=entry.start_time,
                end_time=entry.end_time,
            )
            for entry, course, room in rows
        ]
        return ScheduleMeResponse(entries=entries)

    def create_entry(self, session: Session, payload: ScheduleEntryCreate) -> ScheduleEntryRead:
        self._validate_time_range(payload.start_time, payload.end_time)
        if schedule_repo.get_class_session(session, payload.class_session_id) is None:
            raise _not_found("class_session_id not found")
        if room_repo.get(session, payload.room_id) is None:
            raise _not_found("room_id not found")
        if user_repo.get_teacher_with_user(session, payload.teacher_id) is None:
            raise _not_found("teacher_id not found")

        self._check_conflicts(
            session,
            room_id=payload.room_id,
            teacher_id=payload.teacher_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )

        entry = schedule_repo.create_schedule_entry(
            session,
            class_session_id=payload.class_session_id,
            room_id=payload.room_id,
            teacher_id=payload.teacher_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
        session.commit()
        session.refresh(entry)
        return ScheduleEntryRead.model_validate(entry)

    def update_entry(
        self, session: Session, schedule_entry_id: uuid.UUID, payload: ScheduleEntryUpdate
    ) -> ScheduleEntryRead:
        entry = schedule_repo.get_schedule_entry(session, schedule_entry_id)
        if entry is None:
            raise _not_found(_ENTRY_NOT_FOUND)

        new_room_id = payload.room_id if payload.room_id is not None else entry.room_id
        new_teacher_id = payload.teacher_id if payload.teacher_id is not None else entry.teacher_id
        new_day = payload.day_of_week if payload.day_of_week is not None else entry.day_of_week
        new_start = payload.start_time if payload.start_time is not None else entry.start_time
        new_end = payload.end_time if payload.end_time is not None else entry.end_time

        self._validate_time_range(new_start, new_end)
        if payload.class_session_id is not None and schedule_repo.get_class_session(session, payload.class_session_id) is None:
            raise _not_found("class_session_id not found")
        if payload.room_id is not None and room_repo.get(session, payload.room_id) is None:
            raise _not_found("room_id not found")
        if payload.teacher_id is not None and user_repo.get_teacher_with_user(session, payload.teacher_id) is None:
            raise _not_found("teacher_id not found")

        self._check_conflicts(
            session,
            room_id=new_room_id,
            teacher_id=new_teacher_id,
            day_of_week=new_day,
            start_time=new_start,
            end_time=new_end,
            exclude_id=entry.id,
        )

        if payload.class_session_id is not None:
            entry.class_session_id = payload.class_session_id
        entry.room_id = new_room_id
        entry.teacher_id = new_teacher_id
        entry.day_of_week = new_day
        entry.start_time = new_start
        entry.end_time = new_end

        session.add(entry)
        session.commit()
        session.refresh(entry)
        return ScheduleEntryRead.model_validate(entry)

    def delete_entry(self, session: Session, schedule_entry_id: uuid.UUID) -> None:
        entry = schedule_repo.get_schedule_entry(session, schedule_entry_id)
        if entry is None:
            raise _not_found(_ENTRY_NOT_FOUND)
        schedule_repo.delete_schedule_entry(session, entry)
        session.commit()

    def get_conflicts(self, session: Session, semester_id: uuid.UUID | None = None) -> ScheduleConflictsResponse:
        if semester_id is not None and semester_repo.get(session, semester_id) is None:
            raise _invalid_reference("semester_id")

        entries = schedule_repo.list_all_entries(session, semester_id)
        conflicts: list[ScheduleConflict] = []
        for i, a in enumerate(entries):
            for b in entries[i + 1 :]:
                if a.day_of_week != b.day_of_week:
                    continue
                if not (a.start_time < b.end_time and b.start_time < a.end_time):
                    continue
                overlap_start = max(a.start_time, b.start_time)
                overlap_end = min(a.end_time, b.end_time)
                if a.room_id == b.room_id:
                    conflicts.append(
                        ScheduleConflict(
                            type="room",
                            conflicting_entry_ids=[a.id, b.id],
                            day_of_week=a.day_of_week,
                            overlap_start=overlap_start,
                            overlap_end=overlap_end,
                        )
                    )
                if a.teacher_id == b.teacher_id:
                    conflicts.append(
                        ScheduleConflict(
                            type="teacher",
                            conflicting_entry_ids=[a.id, b.id],
                            day_of_week=a.day_of_week,
                            overlap_start=overlap_start,
                            overlap_end=overlap_end,
                        )
                    )
        return ScheduleConflictsResponse(conflicts=conflicts)

    def _validate_time_range(self, start_time, end_time) -> None:
        # VR-007: start_time must precede end_time.
        if start_time >= end_time:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="start_time must be before end_time"
            )

    def _check_conflicts(
        self, session: Session, *, room_id, teacher_id, day_of_week, start_time, end_time, exclude_id=None
    ) -> None:
        # BR-005/NFR-015: no double-booking of the same room or teacher for
        # overlapping time slots.
        conflicts = schedule_repo.find_overlapping_entries(
            session,
            room_id=room_id,
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            exclude_id=exclude_id,
        )
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This time slot conflicts with an existing room or teacher booking.",
            )

    # --- schedule_change_request (gap-fill, API_Contract.md Section 7.6-7.7) --

    def create_change_request(
        self, session: Session, current_user: User, payload: ScheduleChangeRequestCreate
    ) -> ScheduleChangeRequestCreateResponse:
        entry = schedule_repo.get_schedule_entry(session, payload.schedule_entry_id)
        if entry is None:
            raise _not_found(_ENTRY_NOT_FOUND)

        # BR-004: a Teacher may only request a change to their own schedule
        # entry; ownership check per System_Architecture.md Section 6.
        teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
        if entry.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This schedule entry does not belong to you.",
            )

        change = payload.requested_change
        if change.start_time is not None and change.end_time is not None:
            self._validate_time_range(change.start_time, change.end_time)

        request = schedule_repo.create_change_request(
            session,
            schedule_entry_id=payload.schedule_entry_id,
            requested_by_teacher_id=teacher.id,
            requested_change=change.model_dump(mode="json", exclude_none=True),
        )
        session.commit()
        session.refresh(request)
        return ScheduleChangeRequestCreateResponse(id=request.id, status=request.status, created_at=request.created_at)

    def resolve_change_request(
        self, session: Session, request_id: uuid.UUID, payload: ScheduleChangeRequestResolve, current_admin: User
    ) -> ScheduleChangeRequestResolveResponse:
        request = schedule_repo.get_change_request(session, request_id)
        if request is None:
            raise _not_found("Schedule change request not found")
        if request.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="This request has already been resolved."
            )

        admin = user_repo.get_admin_profile_by_user_id(session, current_admin.id)

        if payload.decision == "approve":
            entry = schedule_repo.get_schedule_entry(session, request.schedule_entry_id)
            change = request.requested_change
            new_room_id = uuid.UUID(change["room_id"]) if change.get("room_id") else entry.room_id
            new_day = change.get("day_of_week", entry.day_of_week)
            new_start = _parse_time(change["start_time"]) if change.get("start_time") else entry.start_time
            new_end = _parse_time(change["end_time"]) if change.get("end_time") else entry.end_time

            self._validate_time_range(new_start, new_end)
            self._check_conflicts(
                session,
                room_id=new_room_id,
                teacher_id=entry.teacher_id,
                day_of_week=new_day,
                start_time=new_start,
                end_time=new_end,
                exclude_id=entry.id,
            )

            entry.room_id = new_room_id
            entry.day_of_week = new_day
            entry.start_time = new_start
            entry.end_time = new_end
            session.add(entry)
            request.status = "approved"
        else:
            request.status = "rejected"

        request.confirmed_by_admin_id = admin.id
        request.resolved_at = datetime.now(timezone.utc)
        session.add(request)
        session.commit()
        session.refresh(request)
        return ScheduleChangeRequestResolveResponse(
            id=request.id, status=request.status, resolved_at=request.resolved_at
        )


def _parse_time(value: str) -> time:
    hour, minute = value.split(":")[:2]
    return time(int(hour), int(minute))
