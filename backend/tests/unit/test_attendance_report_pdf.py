"""
Unit tests: app.pdf.attendance_report.generate_attendance_report_pdf —
the reporting-infrastructure vertical slice's reference PDF generator.
"""

import uuid

from app.pdf.attendance_report import generate_attendance_report_pdf
from app.schemas.attendance import AttendanceReportEntry

_ALL_SCOPE = {"department": "All Departments", "semester": "All Semesters", "student": "All Students"}


def test_produces_valid_pdf_with_summary_rows():
    summary = [
        AttendanceReportEntry(student_id=uuid.uuid4(), student_name="Alice Islam", percentage=92.5),
        AttendanceReportEntry(student_id=uuid.uuid4(), student_name="Bob Rahman", percentage=78.0),
    ]

    pdf_bytes = generate_attendance_report_pdf(_ALL_SCOPE, summary)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 0


def test_produces_valid_pdf_with_empty_summary():
    pdf_bytes = generate_attendance_report_pdf(_ALL_SCOPE, [])

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 0


def test_scoped_labels_are_used_without_error():
    scope = {"department": "Computer Science", "semester": "Fall 2025", "student": "Alice Islam"}
    summary = [AttendanceReportEntry(student_id=uuid.uuid4(), student_name="Alice Islam", percentage=100.0)]

    pdf_bytes = generate_attendance_report_pdf(scope, summary)

    assert pdf_bytes.startswith(b"%PDF")
