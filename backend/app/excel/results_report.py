"""
Excel generation for the Admin Results Report export
(GET /results/reports/excel) — consistency enhancement so Results supports
the same Print/PDF/Excel export actions as the Attendance Report reference
implementation.

Built entirely from app.excel.shared's reusable workbook helpers, matching
app.excel.attendance_report's shape exactly.
"""

from app.excel.shared import build_report_workbook
from app.schemas.report import ResultsReportResponse

_REPORT_TITLE = "Results Report"
_COLUMNS = ["Grade Letter", "Count"]


def _build_subtitle(scope_labels: dict[str, str], report: ResultsReportResponse) -> str:
    return (
        f"Department: {scope_labels['department']} | "
        f"Semester: {scope_labels['semester']} | "
        f"Student: {scope_labels['student']} | "
        f"Pass: {report.pass_count} | Fail: {report.fail_count} | "
        f"Average GPA: {report.average_gpa:.2f}"
    )


_DETAIL_COLUMNS = ["Student", "Course", "Exam", "Grade", "GPA"]


def generate_results_report_excel(scope_labels: dict[str, str], report: ResultsReportResponse) -> bytes:
    rows = [[entry.grade_letter, entry.count] for entry in report.grade_distribution]
    detail_rows = [
        [entry.student_name, entry.course_name, entry.exam_title or "—", entry.grade_letter, entry.grade_point]
        for entry in report.details
    ]
    return build_report_workbook(
        report_title=_REPORT_TITLE,
        subtitle=_build_subtitle(scope_labels, report),
        columns=_COLUMNS,
        rows=rows,
        extra_sheets=[("Details", _DETAIL_COLUMNS, detail_rows)],
    )
