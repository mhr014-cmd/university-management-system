"""
Business logic service: report (see docs/Requirement_Analysis.md FR-054,
FR-055, and the Milestone 10 Reporting Requirements).

Reuses ResultRepository/FeeRepository/reference-data repositories, never
the ORM session directly, per CLAUDE.md §6. Reuses the GPA formula
(`result_service.compute_credit_weighted_gpa`) and the derived-overdue-
status logic (`fee_service._derived_status`) rather than re-implementing
either, per CLAUDE.md's "no duplicated business logic" rule.
`GET /attendance/reports` is NOT hosted here — it already lives in
`attendance_service.py`/`routers/attendance.py` per Milestone 5; this
module only adds the two Milestone 10 report types.

Pass/Fail threshold (Milestone 10, resolved as a documented engineering
assumption — `Proposal_vs_Engineering_Additions.md` already flags this
endpoint's response shape as an "engineering interpretation" of the
proposal's undefined "result report" content): a result with
`grade_point > 0` counts as a pass; `grade_point == 0` (the conventional
"F" on a 4.0 scale) counts as a fail. `grade_letter` is free text
(Teacher-supplied, per `API_Contract.md` §5.2), so `grade_point` is used
for this determination instead of pattern-matching the letter string.

Outstanding vs. overdue (Milestone 10): `total_outstanding` is the sum of
remaining balance across every invoice not yet fully paid; `total_overdue`
is the portion of that same total whose `due_date` has passed — overdue
is a subset of outstanding, not a separate pool, matching the Admin: Fee
Dashboard's existing (Milestone 8) semantics for the same two terms.
"""

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.exam_repository import ExamRepository
from app.repositories.fee_repository import FeeRepository
from app.repositories.reference_data_repository import CourseRepository, DepartmentRepository, SemesterRepository
from app.repositories.result_repository import ResultRepository
from app.repositories.user_repository import UserRepository
from app.schemas.report import (
    FeeDetailEntry,
    FeesReportResponse,
    GradeDistributionEntry,
    ReportScope,
    ResultDetailEntry,
    ResultsReportResponse,
)
from app.services.fee_service import _derived_status
from app.services.result_service import compute_credit_weighted_gpa

result_repo = ResultRepository()
fee_repo = FeeRepository()
department_repo = DepartmentRepository()
semester_repo = SemesterRepository()
user_repo = UserRepository()
course_repo = CourseRepository()
exam_repo = ExamRepository()


def _invalid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


class ReportService:
    # --- GET /results/reports (FR-054) --------------------------------------

    def get_results_report(
        self,
        session: Session,
        *,
        department_id: uuid.UUID | None,
        semester_id: uuid.UUID | None,
        student_id: uuid.UUID | None,
    ) -> ResultsReportResponse:
        if department_id is not None and department_repo.get(session, department_id) is None:
            raise _invalid("department_id does not reference an existing department")
        if semester_id is not None and semester_repo.get(session, semester_id) is None:
            raise _invalid("semester_id does not reference an existing semester")
        if student_id is not None and user_repo.get_student_with_user(session, student_id) is None:
            raise _invalid("student_id does not reference an existing student")

        # Business Rule (API_Contract.md §9.1): only published results
        # contribute to report aggregates.
        results = result_repo.list_published_for_report(
            session, department_id=department_id, semester_id=semester_id, student_id=student_id
        )

        # Single batch lookup for every result's student display name —
        # not one query per result — matching the batch student_name
        # lookup convention already used by grading_service.get_results()
        # and exam_service.get_results_for_exam().
        students = user_repo.list_students_by_ids(session, [r.student_id for r in results])
        name_by_student_id = {s.id: f"{s.first_name} {s.last_name}" for s in students}

        distribution: dict[str, int] = {}
        pass_count = 0
        fail_count = 0
        details: list[ResultDetailEntry] = []
        for r in results:
            letter = r.grade_letter or "N/A"
            distribution[letter] = distribution.get(letter, 0) + 1
            if r.grade_point is not None and float(r.grade_point) > 0:
                pass_count += 1
            else:
                fail_count += 1

            # Detail row (consistency-audit gap closure): shows which
            # academic record produced each summary/distribution entry —
            # reuses the same `results` rows already fetched above, plus
            # per-row course/exam lookups matching the exact pattern
            # result_service.py's own _build_semester_entries already uses.
            course = course_repo.get(session, r.course_id)
            exam = exam_repo.get_exam(session, r.exam_id) if r.exam_id is not None else None
            details.append(
                ResultDetailEntry(
                    student_id=r.student_id,
                    student_name=name_by_student_id.get(r.student_id, "Unknown Student"),
                    course_name=course.name if course is not None else "",
                    exam_title=exam.title if exam is not None else None,
                    grade_letter=letter,
                    grade_point=float(r.grade_point) if r.grade_point is not None else 0.0,
                )
            )

        # Reused, not duplicated — see module docstring.
        average_gpa = compute_credit_weighted_gpa(session, results)

        return ResultsReportResponse(
            scope=ReportScope(department_id=department_id, semester_id=semester_id, student_id=student_id),
            grade_distribution=[
                GradeDistributionEntry(grade_letter=letter, count=count) for letter, count in distribution.items()
            ],
            pass_count=pass_count,
            fail_count=fail_count,
            average_gpa=average_gpa,
            details=details,
        )

    # --- GET /fees/reports (FR-055) ------------------------------------------

    def get_fees_report(
        self,
        session: Session,
        *,
        department_id: uuid.UUID | None,
        semester_id: uuid.UUID | None,
        student_id: uuid.UUID | None,
    ) -> FeesReportResponse:
        if department_id is not None and department_repo.get(session, department_id) is None:
            raise _invalid("department_id does not reference an existing department")
        if semester_id is not None and semester_repo.get(session, semester_id) is None:
            raise _invalid("semester_id does not reference an existing semester")
        if student_id is not None and user_repo.get_student_with_user(session, student_id) is None:
            raise _invalid("student_id does not reference an existing student")

        invoices = fee_repo.list_invoices_for_report(
            session, department_id=department_id, semester_id=semester_id, student_id=student_id
        )
        # Single batch lookup for every invoice's student display name —
        # not one query per invoice — same batch-lookup convention used
        # above in get_results_report.
        students = user_repo.list_students_by_ids(session, [invoice.student_id for invoice, _fs in invoices])
        name_by_student_id = {s.id: f"{s.first_name} {s.last_name}" for s in students}

        today = date.today()
        total_collected = 0.0
        total_outstanding = 0.0
        total_overdue = 0.0
        details: list[FeeDetailEntry] = []
        for invoice, fee_structure in invoices:
            paid = fee_repo.sum_payments(session, invoice.student_id, fee_structure.id)
            total_collected += paid
            remaining = max(0.0, float(fee_structure.amount) - paid)
            total_outstanding += remaining
            # Reused, not duplicated — see module docstring.
            derived_status = _derived_status(invoice, fee_structure, today)
            if derived_status == "overdue":
                total_overdue += remaining

            # Detail row (consistency-audit gap closure): shows which fee
            # structure/invoice produced each summary total — reuses the
            # same `invoices` rows and `paid`/`remaining`/derived_status
            # already computed above, no new query source.
            details.append(
                FeeDetailEntry(
                    student_id=invoice.student_id,
                    student_name=name_by_student_id.get(invoice.student_id, "Unknown Student"),
                    fee_name=fee_structure.name,
                    amount=round(float(fee_structure.amount), 2),
                    paid=round(paid, 2),
                    outstanding=round(remaining, 2),
                    due_date=fee_structure.due_date,
                    status=derived_status,
                )
            )

        return FeesReportResponse(
            scope=ReportScope(department_id=department_id, semester_id=semester_id, student_id=student_id),
            total_collected=round(total_collected, 2),
            total_outstanding=round(total_outstanding, 2),
            total_overdue=round(total_overdue, 2),
            details=details,
        )
