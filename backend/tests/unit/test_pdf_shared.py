"""
Unit tests: app.pdf.shared — the reusable A4 report layout/table/
header-footer helpers introduced for the Version 1.2 reporting
infrastructure (Attendance Reports is the reference implementation;
Results/Fees/Timetable/Users reports reuse these same helpers later).
"""

from reportlab.platypus import Paragraph

from app.pdf.shared import build_report_document, empty_state_style, report_styles, styled_table


def test_report_styles_returns_distinct_title_and_subtitle_styles():
    title_style, subtitle_style = report_styles()
    assert title_style.name == "ReportTitle"
    assert subtitle_style.name == "ReportSubtitle"
    assert title_style.fontSize > subtitle_style.fontSize


def test_styled_table_preserves_row_count_and_content():
    data = [["Student", "Attendance %"], ["Alice", "90.0%"], ["Bob", "75.0%"]]
    table = styled_table(data, col_widths=[200, 100])
    assert table._cellvalues == data


def test_build_report_document_produces_valid_pdf_bytes():
    body = [Paragraph("No records in this scope.", empty_state_style())]
    pdf_bytes = build_report_document(report_title="Test Report", subtitle="Department: All", story_body=body)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 0


def test_build_report_document_with_a_table_body():
    table = styled_table([["Student", "Attendance %"], ["Alice", "90.0%"]], col_widths=[200, 100])
    pdf_bytes = build_report_document(report_title="Attendance Report", subtitle="All Departments", story_body=[table])
    assert pdf_bytes.startswith(b"%PDF")
