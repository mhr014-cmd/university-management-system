"""
Pydantic request/response schemas: attendance (see docs/API_Contract.md
Section 4).
"""

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AttendanceStatus = Literal["present", "absent", "late", "excused"]

# BR-008/FR-031: threshold resolved to 80% during the Milestone 5
# pre-implementation review — see Requirement_Analysis.md Section 14 item 4.
LOW_ATTENDANCE_THRESHOLD = 80.0


class AttendanceRecordInput(BaseModel):
    student_id: uuid.UUID
    status: AttendanceStatus


class AttendanceMarkRequest(BaseModel):
    class_session_id: uuid.UUID
    attendance_date: date
    records: list[AttendanceRecordInput] = Field(min_length=1)


class AttendanceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    class_session_id: uuid.UUID
    marked_by_teacher_id: uuid.UUID
    attendance_date: date
    status: AttendanceStatus


class AttendanceUpdateRequest(BaseModel):
    status: AttendanceStatus


class AttendanceDateRecord(BaseModel):
    date: date
    status: AttendanceStatus


class ClassSessionAttendanceSummary(BaseModel):
    class_session_id: uuid.UUID
    course_name: str
    percentage: float
    low_attendance_warning: bool
    records: list[AttendanceDateRecord]


class AttendanceMeResponse(BaseModel):
    overall_percentage: float
    low_attendance_warning: bool
    by_class_session: list[ClassSessionAttendanceSummary]


class AttendanceMeQuery(BaseModel):
    class_session_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    # Parent scoping (FR-032/BR-007 — see attendance_service.get_me):
    # required when the caller is a Parent, ignored when the caller is a
    # Student (a Student always sees their own record regardless of this
    # field). Mirrors the same student_id convention already used by
    # GET /fees/me and GET /results/me.
    student_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def check_date_range(self) -> "AttendanceMeQuery":
        if self.date_from is not None and self.date_to is not None and self.date_from > self.date_to:
            raise ValueError("date_from must be before or equal to date_to")
        return self


class ClassAttendanceEntry(BaseModel):
    # id included beyond API_Contract.md's originally-documented shape —
    # PUT /attendance/{id} (the correction workflow, FR-029) needs the
    # record's own id, which student_id/date/status alone can't resolve.
    # Found while implementing the Teacher: Attendance Marker page's
    # correction mode; fixed in the same change per CLAUDE.md Section 9.
    id: uuid.UUID
    student_id: uuid.UUID
    date: date
    status: AttendanceStatus


class ClassAttendanceResponse(BaseModel):
    class_session_id: uuid.UUID
    records: list[ClassAttendanceEntry]


class AttendanceReportScope(BaseModel):
    department_id: uuid.UUID | None
    semester_id: uuid.UUID | None
    student_id: uuid.UUID | None


class AttendanceReportEntry(BaseModel):
    student_id: uuid.UUID
    # Additive display field (final-polish pass): the frontend Reports page
    # previously rendered the raw student_id UUID — see student_name below.
    student_name: str
    percentage: float


class AttendanceReportsResponse(BaseModel):
    scope: AttendanceReportScope
    summary: list[AttendanceReportEntry]
