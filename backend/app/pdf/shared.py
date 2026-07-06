"""
Shared PDF report scaffolding (reporting infrastructure).

Reusable layout/styling/header-footer/table helpers for the new Reports
module — Attendance Reports (this vertical slice) is the reference
implementation; Results/Fees/Timetable/Users reports should reuse these
helpers rather than each hand-rolling reportlab boilerplate, and rather
than forcing every report through one over-generic API.

Deliberately independent of app/pdf/transcript_generator.py and
invoice_generator.py — those stay untouched (existing US-Letter documents
with their own established layout). New reports render on A4, since no
paper size is specified anywhere in docs/ for this new capability and A4
is the more common default outside the US-Letter convention already used
by those two pre-existing documents.
"""

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

UNIVERSITY_NAME = "ICT Education University"
_INK = colors.HexColor("#1f2937")
_MUTED = colors.HexColor("#6b7280")
_HEADER_BG = colors.HexColor("#1f2937")
_ROW_ALT_BG = colors.HexColor("#f9fafb")

_PAGE_MARGIN = 0.75 * inch


def report_styles() -> tuple[ParagraphStyle, ParagraphStyle]:
    """(title_style, subtitle_style) built on reportlab's sample stylesheet."""
    base = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=base["Title"], fontSize=16)
    subtitle_style = ParagraphStyle("ReportSubtitle", parent=base["Normal"], textColor=_MUTED)
    return title_style, subtitle_style


def empty_state_style() -> ParagraphStyle:
    base = getSampleStyleSheet()
    return ParagraphStyle("ReportEmptyState", parent=base["Normal"], textColor=_MUTED, spaceBefore=8)


def styled_table(data: list[list[str]], col_widths: list[float]) -> Table:
    """A table with a dark header row (white bold text) and zebra-striped
    body rows — the shared look every report table uses, matching the
    header styling already established in transcript_generator.py's
    per-semester course table, generalized here for reuse."""
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT_BG]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def draw_header_footer(canvas, doc, *, report_title: str) -> None:
    """Page decoration shared by every report: an institution wordmark
    (standing in for a logo asset — no real institution logo image exists
    in this project, the same documented limitation as
    transcript_generator.py's programmatic seal) plus a footer with the
    generation timestamp and page number."""
    canvas.saveState()

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(_INK)
    canvas.drawString(_PAGE_MARGIN, doc.pagesize[1] - 0.55 * inch, UNIVERSITY_NAME)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_MUTED)
    canvas.drawRightString(doc.pagesize[0] - _PAGE_MARGIN, doc.pagesize[1] - 0.55 * inch, report_title)

    canvas.drawString(
        _PAGE_MARGIN, 0.5 * inch, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    canvas.drawRightString(doc.pagesize[0] - _PAGE_MARGIN, 0.5 * inch, f"Page {doc.page}")

    canvas.restoreState()


def build_report_document(*, report_title: str, subtitle: str, story_body: list) -> bytes:
    """Assembles a full A4 report PDF: title, subtitle, then whatever
    report-specific content (`story_body` — a list of reportlab flowables,
    typically a `styled_table(...)` or an empty-state Paragraph) the
    caller supplies. Header/footer are drawn on every page automatically."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.9 * inch,
        bottomMargin=0.85 * inch,
        leftMargin=_PAGE_MARGIN,
        rightMargin=_PAGE_MARGIN,
    )
    title_style, subtitle_style = report_styles()

    story = [
        Paragraph(report_title, title_style),
        Paragraph(subtitle, subtitle_style),
        Spacer(1, 0.25 * inch),
        *story_body,
    ]

    def _decorate(canvas, doc_) -> None:
        draw_header_footer(canvas, doc_, report_title=report_title)

    doc.build(story, onFirstPage=_decorate, onLaterPages=_decorate)
    return buffer.getvalue()
