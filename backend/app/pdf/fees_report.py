"""
PDF generation for the Admin Fees Report export (GET /fees/reports/pdf) —
consistency enhancement so Fees supports the same Print/PDF/Excel export
actions as the Attendance Report reference implementation.

Built entirely from app.pdf.shared's reusable layout/table/header-footer
helpers, matching app.pdf.attendance_report's shape exactly, with one
exception scoped to this file only (see `_wrapped_detail_table` below).
"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from app.pdf.shared import build_report_document, empty_state_style, styled_table
from app.schemas.report import FeesReportResponse

_REPORT_TITLE = "Fees Report"

_SECTION_HEADING_STYLE = ParagraphStyle("ReportSectionHeading", parent=getSampleStyleSheet()["Heading3"])

# Layout-bug fix, scoped to this file only (not app/pdf/shared.py's
# styled_table, which Attendance and Results also use and must stay
# byte-for-byte unchanged): reportlab's Table draws plain-string cells as a
# single, non-wrapping line — a long "Student" or "Fee Name" value doesn't
# wrap to the column width, it overflows into the next cell instead. The
# summary table above (Metric/Amount) and every other report's table are
# unaffected since their cell text is always short and fixed-format, but
# this detail table's Student/Fee Name columns are unbounded student-
# supplied text, so those two columns render as wrapping Paragraphs;
# Amount/Paid/Outstanding/Due Date stay plain strings — always short,
# fixed-format, never at risk of overflow.
_DETAIL_CELL_STYLE = ParagraphStyle("FeeDetailCell", parent=getSampleStyleSheet()["Normal"], fontSize=9, leading=11)
_DETAIL_HEADER_BG = colors.HexColor("#1f2937")
_DETAIL_ROW_ALT_BG = colors.HexColor("#f9fafb")


def _wrapped_detail_table(data: list[list[str]], col_widths: list[float]) -> Table:
    """Same visual style as app.pdf.shared.styled_table (dark header,
    zebra body rows), but wraps the Student/Fee Name columns (index 0, 1)
    in Paragraphs so long values wrap within their column instead of
    overflowing into the next one."""
    wrapped_data = [data[0]] + [
        [Paragraph(row[0], _DETAIL_CELL_STYLE), Paragraph(row[1], _DETAIL_CELL_STYLE), *row[2:]] for row in data[1:]
    ]
    table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _DETAIL_HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _DETAIL_ROW_ALT_BG]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _build_subtitle(scope_labels: dict[str, str]) -> str:
    return (
        f"Department: {scope_labels['department']}  |  "
        f"Semester: {scope_labels['semester']}  |  "
        f"Student: {scope_labels['student']}"
    )


def generate_fees_report_pdf(scope_labels: dict[str, str], report: FeesReportResponse) -> bytes:
    subtitle = _build_subtitle(scope_labels)

    table_data = [
        ["Metric", "Amount"],
        ["Collected", f"{report.total_collected:.2f}"],
        ["Outstanding", f"{report.total_outstanding:.2f}"],
        ["Overdue", f"{report.total_overdue:.2f}"],
    ]
    body = [styled_table(table_data, col_widths=[4.0 * inch, 2.0 * inch]), Spacer(1, 0.3 * inch)]

    # Detail section (consistency-audit gap closure): the itemized fees
    # that produced the summary totals above.
    body.append(Paragraph("Itemized Fees", _SECTION_HEADING_STYLE))
    if not report.details:
        body.append(Paragraph("No invoices in this scope.", empty_state_style()))
    else:
        detail_data: list[list[str]] = [["Student", "Fee Name", "Amount", "Paid", "Outstanding", "Due Date"]]
        detail_data.extend(
            [
                entry.student_name,
                entry.fee_name,
                f"{entry.amount:.2f}",
                f"{entry.paid:.2f}",
                f"{entry.outstanding:.2f}",
                entry.due_date.isoformat(),
            ]
            for entry in report.details
        )
        # 6.2in total, within A4's ~6.77in printable width (8.27in page
        # minus the 0.75in margins build_report_document uses) — portrait
        # stays sufficient, no landscape needed. Student/Fee Name get more
        # room since they're the variable-length columns; the wrapping in
        # _wrapped_detail_table handles anything still too long to fit.
        body.append(
            _wrapped_detail_table(
                detail_data,
                col_widths=[1.5 * inch, 1.9 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch],
            )
        )

    return build_report_document(report_title=_REPORT_TITLE, subtitle=subtitle, story_body=body)
