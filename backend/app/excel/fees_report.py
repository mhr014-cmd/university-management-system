"""
Excel generation for the Admin Fees Report export (GET /fees/reports/excel)
— consistency enhancement so Fees supports the same Print/PDF/Excel export
actions as the Attendance Report reference implementation.

Built entirely from app.excel.shared's reusable workbook helpers, matching
app.excel.attendance_report's shape exactly.
"""

from app.excel.shared import build_report_workbook
from app.schemas.report import FeesReportResponse

_REPORT_TITLE = "Fees Report"
_COLUMNS = ["Metric", "Amount"]


def _build_subtitle(scope_labels: dict[str, str]) -> str:
    return (
        f"Department: {scope_labels['department']} | "
        f"Semester: {scope_labels['semester']} | "
        f"Student: {scope_labels['student']}"
    )


_DETAIL_COLUMNS = ["Student", "Fee Name", "Amount", "Paid", "Outstanding", "Due Date"]


def generate_fees_report_excel(scope_labels: dict[str, str], report: FeesReportResponse) -> bytes:
    rows = [
        ["Collected", round(report.total_collected, 2)],
        ["Outstanding", round(report.total_outstanding, 2)],
        ["Overdue", round(report.total_overdue, 2)],
    ]
    detail_rows = [
        [entry.student_name, entry.fee_name, entry.amount, entry.paid, entry.outstanding, entry.due_date.isoformat()]
        for entry in report.details
    ]
    return build_report_workbook(
        report_title=_REPORT_TITLE,
        subtitle=_build_subtitle(scope_labels),
        columns=_COLUMNS,
        rows=rows,
        extra_sheets=[("Details", _DETAIL_COLUMNS, detail_rows)],
    )
