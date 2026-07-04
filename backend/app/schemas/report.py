"""
Pydantic request/response schemas: reports (see docs/API_Contract.md
Section 9). Not enumerated in Implementation_Roadmap.md's Milestone 10
file list (only `report_service.py`/`reports.py` are) — added because
CLAUDE.md §6 requires every response model to be a Pydantic schema,
same precedent as Milestone 9's un-listed `notification_service.py`.
"""

import uuid

from pydantic import BaseModel


class ReportScope(BaseModel):
    department_id: uuid.UUID | None
    semester_id: uuid.UUID | None
    student_id: uuid.UUID | None


class GradeDistributionEntry(BaseModel):
    grade_letter: str
    count: int


class ResultsReportResponse(BaseModel):
    scope: ReportScope
    grade_distribution: list[GradeDistributionEntry]
    pass_count: int
    fail_count: int
    average_gpa: float


class FeesReportResponse(BaseModel):
    scope: ReportScope
    total_collected: float
    total_outstanding: float
    total_overdue: float
