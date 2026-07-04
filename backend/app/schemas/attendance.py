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

    @model_validator(mode="after")
    def check_date_range(self) -> "AttendanceMeQuery":
        if self.date_from is not None and self.date_to is not None and self.date_from > self.date_to:
            raise ValueError("date_from must be before or equal to date_to")
        return self


class ClassAttendanceEntry(BaseModel):
    student_id: uuid.UUID
    date: date
    status: AttendanceStatus


class ClassAttendanceResponse(BaseModel):
    class_session_id: uuid.UUID
    records: list[ClassAttendanceEntry]


class AttendanceReportScope(BaseModel):
    department_id: uuid.UUID | None
    semester_id: uuid.UUID | None


class AttendanceReportEntry(BaseModel):
    student_id: uuid.UUID
    percentage: float


class AttendanceReportsResponse(BaseModel):
    scope: AttendanceReportScope
    summary: list[AttendanceReportEntry]
