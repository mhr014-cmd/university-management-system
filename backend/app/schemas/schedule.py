"""
Pydantic request/response schemas: schedule (see docs/API_Contract.md
Section 7), plus the Derived class_session/enrollment creation schemas
(Section 7.8-7.9).
"""

import uuid
from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DayOfWeek = Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# --- class_session (Derived, API_Contract.md Section 7.8) -----------------


class ClassSessionCreate(BaseModel):
    course_id: uuid.UUID
    teacher_id: uuid.UUID
    semester_id: uuid.UUID
    section_label: str = Field(min_length=1)


class ClassSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    teacher_id: uuid.UUID
    semester_id: uuid.UUID
    section_label: str
    created_at: datetime
    updated_at: datetime


# --- enrollment (Derived, API_Contract.md Section 7.9) --------------------


class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID
    class_session_id: uuid.UUID


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    class_session_id: uuid.UUID
    enrolled_at: datetime


# --- schedule_entry (API_Contract.md Section 7.1-7.5) ----------------------


class ScheduleEntryCreate(BaseModel):
    class_session_id: uuid.UUID
    room_id: uuid.UUID
    teacher_id: uuid.UUID
    day_of_week: DayOfWeek
    start_time: time
    end_time: time


class ScheduleEntryUpdate(BaseModel):
    class_session_id: uuid.UUID | None = None
    room_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    day_of_week: DayOfWeek | None = None
    start_time: time | None = None
    end_time: time | None = None


class ScheduleEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_session_id: uuid.UUID
    room_id: uuid.UUID
    teacher_id: uuid.UUID
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    created_at: datetime
    updated_at: datetime


class ScheduleMeEntry(BaseModel):
    schedule_entry_id: uuid.UUID
    class_session_id: uuid.UUID
    course_name: str
    room_name: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time


class ScheduleMeResponse(BaseModel):
    entries: list[ScheduleMeEntry]


class ScheduleConflict(BaseModel):
    type: Literal["room", "teacher"]
    conflicting_entry_ids: list[uuid.UUID]
    day_of_week: DayOfWeek
    overlap_start: time
    overlap_end: time


class ScheduleConflictsResponse(BaseModel):
    conflicts: list[ScheduleConflict]


# --- schedule_change_request (gap-fill, API_Contract.md Section 7.6-7.7) --


class RequestedChange(BaseModel):
    day_of_week: DayOfWeek | None = None
    start_time: time | None = None
    end_time: time | None = None
    room_id: uuid.UUID | None = None


class ScheduleChangeRequestCreate(BaseModel):
    schedule_entry_id: uuid.UUID
    requested_change: RequestedChange


class ScheduleChangeRequestCreateResponse(BaseModel):
    id: uuid.UUID
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime


class ScheduleChangeRequestResolve(BaseModel):
    decision: Literal["approve", "reject"]
    comment: str | None = None


class ScheduleChangeRequestResolveResponse(BaseModel):
    id: uuid.UUID
    status: Literal["approved", "rejected"]
    resolved_at: datetime


# --- class_session roster (Derived, API_Contract.md Section 7.10) ---------


class RosterEntry(BaseModel):
    student_id: uuid.UUID
    first_name: str
    last_name: str


class ClassSessionRosterResponse(BaseModel):
    class_session_id: uuid.UUID
    students: list[RosterEntry]
