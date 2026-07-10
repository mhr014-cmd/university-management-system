"""
Pydantic request/response schemas: reports (see docs/API_Contract.md
Section 9). Not enumerated in Implementation_Roadmap.md's Milestone 10
file list (only `report_service.py`/`reports.py` are) — added because
CLAUDE.md §6 requires every response model to be a Pydantic schema,
same precedent as Milestone 9's un-listed `notification_service.py`.
"""

import uuid
from datetime import date

from pydantic import BaseModel


class ReportScope(BaseModel):
    department_id: uuid.UUID | None
    semester_id: uuid.UUID | None
    student_id: uuid.UUID | None


class GradeDistributionEntry(BaseModel):
    grade_letter: str
    count: int


# Additive field (Reports-module detail enhancement — a summary-only
# Results/Fees report gave no way to see which records produced the
# totals, unlike Attendance's report which already lists per-student
# rows). One row per published `result`, reusing the same data
# `get_results_report` already fetches via
# ResultRepository.list_published_for_report — no new query source.
class ResultDetailEntry(BaseModel):
    student_id: uuid.UUID
    student_name: str
    course_name: str
    exam_title: str | None
    grade_letter: str
    grade_point: float


class ResultsReportResponse(BaseModel):
    scope: ReportScope
    grade_distribution: list[GradeDistributionEntry]
    pass_count: int
    fail_count: int
    average_gpa: float
    details: list[ResultDetailEntry]


# Additive field, same rationale as ResultDetailEntry above — one row per
# invoice, reusing the same (Invoice, FeeStructure) pairs
# `get_fees_report` already fetches via FeeRepository.list_invoices_for_report.
class FeeDetailEntry(BaseModel):
    student_id: uuid.UUID
    student_name: str
    fee_name: str
    amount: float
    paid: float
    outstanding: float
    due_date: date
    status: str


class FeesReportResponse(BaseModel):
    scope: ReportScope
    total_collected: float
    total_outstanding: float
    total_overdue: float
    details: list[FeeDetailEntry]
