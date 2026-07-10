"""
PDF generation for the Admin Results Report export (GET /results/reports/pdf)
— consistency enhancement so Results supports the same Print/PDF/Excel
export actions as the Attendance Report reference implementation.

Built entirely from app.pdf.shared's reusable layout/table/header-footer
helpers, matching app.pdf.attendance_report's shape exactly.
"""

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from app.pdf.shared import build_report_document, empty_state_style, styled_table
from app.schemas.report import ResultsReportResponse

_REPORT_TITLE = "Results Report"

_SECTION_HEADING_STYLE = ParagraphStyle("ReportSectionHeading", parent=getSampleStyleSheet()["Heading3"])


def _build_subtitle(scope_labels: dict[str, str]) -> str:
    return (
        f"Department: {scope_labels['department']}  |  "
        f"Semester: {scope_labels['semester']}  |  "
        f"Student: {scope_labels['student']}"
    )


def generate_results_report_pdf(scope_labels: dict[str, str], report: ResultsReportResponse) -> bytes:
    subtitle = _build_subtitle(scope_labels)

    summary_data = [
        ["Pass Count", "Fail Count", "Average GPA"],
        [str(report.pass_count), str(report.fail_count), f"{report.average_gpa:.2f}"],
    ]
    body = [styled_table(summary_data, col_widths=[2.0 * inch, 2.0 * inch, 2.0 * inch]), Spacer(1, 0.3 * inch)]

    if not report.grade_distribution:
        body.append(Paragraph("No published results in this scope.", empty_state_style()))
    else:
        table_data: list[list[str]] = [["Grade Letter", "Count"]]
        table_data.extend([entry.grade_letter, str(entry.count)] for entry in report.grade_distribution)
        body.append(styled_table(table_data, col_widths=[4.0 * inch, 2.0 * inch]))

    # Detail section (consistency-audit gap closure): which academic
    # records produced the summary/distribution above.
    body.append(Spacer(1, 0.3 * inch))
    body.append(Paragraph("Detailed Results", _SECTION_HEADING_STYLE))
    if not report.details:
        body.append(Paragraph("No published results in this scope.", empty_state_style()))
    else:
        detail_data: list[list[str]] = [["Student", "Course", "Exam", "Grade", "GPA"]]
        detail_data.extend(
            [
                entry.student_name,
                entry.course_name,
                entry.exam_title or "—",
                entry.grade_letter,
                f"{entry.grade_point:.2f}",
            ]
            for entry in report.details
        )
        body.append(
            styled_table(
                detail_data, col_widths=[1.6 * inch, 1.6 * inch, 1.6 * inch, 0.7 * inch, 0.5 * inch]
            )
        )

    return build_report_document(report_title=_REPORT_TITLE, subtitle=subtitle, story_body=body)
