"""
Excel generation for the Admin Attendance Report export
(GET /attendance/reports/excel) — the reporting-infrastructure vertical
slice's reference implementation.

Built entirely from app.excel.shared's reusable workbook helpers; only
report-specific content (the Student/Attendance % columns) lives here.
Future report workbooks (Results, Fees, Timetable, Users) should follow
this same shape.
"""

from app.excel.shared import build_report_workbook
from app.schemas.attendance import AttendanceReportEntry

_REPORT_TITLE = "Attendance Report"
_COLUMNS = ["Student", "Attendance %"]


def _build_subtitle(scope_labels: dict[str, str]) -> str:
    return (
        f"Department: {scope_labels['department']} | "
        f"Semester: {scope_labels['semester']} | "
        f"Student: {scope_labels['student']}"
    )


def generate_attendance_report_excel(scope_labels: dict[str, str], summary: list[AttendanceReportEntry]) -> bytes:
    rows = [[entry.student_name, round(entry.percentage, 1)] for entry in summary]
    return build_report_workbook(
        report_title=_REPORT_TITLE, subtitle=_build_subtitle(scope_labels), columns=_COLUMNS, rows=rows
    )
