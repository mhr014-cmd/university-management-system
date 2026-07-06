"""
CSV generation for the Attendance Report export (GET /attendance/reports/csv).

Production-readiness audit gap closure: PDF and Excel exports already
existed (Version 1.2 reporting infrastructure); CSV was requested
separately for the Parent attendance page. Uses the stdlib `csv` module
only — no new dependency — and reuses the exact same
`AttendanceReportEntry` summary rows the PDF/Excel generators already
consume, so there is a single source of truth for what a "report row" is.
"""

import csv
from io import StringIO

from app.schemas.attendance import AttendanceReportEntry

_HEADER = ["Student", "Attendance %"]


def generate_attendance_report_csv(scope_labels: dict[str, str], summary: list[AttendanceReportEntry]) -> bytes:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([f"Department: {scope_labels['department']}"])
    writer.writerow([f"Semester: {scope_labels['semester']}"])
    writer.writerow([f"Student: {scope_labels['student']}"])
    writer.writerow([])
    writer.writerow(_HEADER)
    for entry in summary:
        writer.writerow([entry.student_name, round(entry.percentage, 1)])
    return buffer.getvalue().encode("utf-8")
