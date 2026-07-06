"""
PDF generation for the Admin Attendance Report export
(GET /attendance/reports/pdf) — the reporting-infrastructure vertical
slice's reference implementation.

Built entirely from app.pdf.shared's reusable layout/table/header-footer
helpers; only report-specific content (the two-column Student/Attendance %
table and its empty-state message) lives here. Future report PDFs
(Results, Fees, Timetable, Users) should follow this same shape: a small
module that composes app.pdf.shared helpers, not a new generic API.
"""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

from app.pdf.shared import build_report_document, empty_state_style, styled_table
from app.schemas.attendance import AttendanceReportEntry

_REPORT_TITLE = "Attendance Report"


def _build_subtitle(scope_labels: dict[str, str]) -> str:
    return (
        f"Department: {scope_labels['department']}  |  "
        f"Semester: {scope_labels['semester']}  |  "
        f"Student: {scope_labels['student']}"
    )


def generate_attendance_report_pdf(scope_labels: dict[str, str], summary: list[AttendanceReportEntry]) -> bytes:
    subtitle = _build_subtitle(scope_labels)

    if not summary:
        body = [Paragraph("No attendance records in this scope.", empty_state_style())]
    else:
        table_data: list[list[str]] = [["Student", "Attendance %"]]
        table_data.extend([entry.student_name, f"{entry.percentage:.1f}%"] for entry in summary)
        body = [styled_table(table_data, col_widths=[4.0 * inch, 2.0 * inch])]

    return build_report_document(report_title=_REPORT_TITLE, subtitle=subtitle, story_body=body)
