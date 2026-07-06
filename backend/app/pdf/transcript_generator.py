"""
PDF transcript generation (FR-036, BR-002 — only published results appear).

Generation runs synchronously within the request/response cycle for
`GET /results/{studentId}/transcript` (per API_Contract.md §5.5's
documented binary-stream response — there is no polling/job-status
mechanism for this endpoint). This still satisfies System_Architecture.md
§2.4's "avoid blocking the request thread" guidance: reportlab's work for
a single transcript is CPU-bound but fast, and the router offloads the
call via `fastapi.concurrency.run_in_threadpool` so the async event loop
is never blocked while it runs.

Known simplification: no real institution logo/seal image asset exists in
this project, so the "university seal" (FR-036) is rendered as a
programmatically-drawn seal (concentric rings, curved institution name,
and a center emblem) rather than an embedded image asset — see
docs/Proposal_vs_Engineering_Additions.md.
"""

import math
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.result import ResultSemesterEntry

UNIVERSITY_NAME = "ICT Education University"
_SEAL_INK = colors.HexColor("#1f2937")


def _draw_circular_text(
    canvas, text: str, center_x: float, center_y: float, radius: float, *, start_deg: float, end_deg: float,
    font: str, size: float, flip: bool = False,
) -> None:
    """Places one character per computed angle along an arc, each rotated
    to stay tangent to the circle — reportlab has no built-in curved-text
    primitive, so this is the standard manual technique for one. `flip`
    adds a 180-degree turn per character, needed for text running along
    the bottom half of the circle so it reads upright rather than
    upside-down (the standard "banner text" seal convention)."""
    canvas.setFont(font, size)
    span = 0.0 if len(text) <= 1 else end_deg - start_deg
    step = span / max(len(text) - 1, 1)
    for i, char in enumerate(text):
        angle_deg = start_deg + i * step
        angle_rad = math.radians(angle_deg)
        x = center_x + radius * math.sin(angle_rad)
        y = center_y + radius * math.cos(angle_rad)
        canvas.saveState()
        canvas.translate(x, y)
        canvas.rotate(-angle_deg + (180 if flip else 0))
        canvas.drawCentredString(0, 0, char)
        canvas.restoreState()


def _draw_star(canvas, center_x: float, center_y: float, outer_radius: float, inner_radius: float) -> None:
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = outer_radius if i % 2 == 0 else inner_radius
        points.append((center_x + r * math.cos(angle), center_y + r * math.sin(angle)))
    path = canvas.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    path.close()
    canvas.drawPath(path, fill=1, stroke=0)


def _draw_seal(canvas, doc) -> None:
    canvas.saveState()
    x, y = doc.pagesize[0] - 1.35 * inch, doc.pagesize[1] - 1.35 * inch
    outer_radius, inner_radius = 0.62 * inch, 0.5 * inch

    canvas.setStrokeColor(_SEAL_INK)
    canvas.setFillColor(_SEAL_INK)
    canvas.setLineWidth(1.75)
    canvas.circle(x, y, outer_radius, stroke=1, fill=0)
    canvas.setLineWidth(1)
    canvas.circle(x, y, inner_radius, stroke=1, fill=0)

    text_radius = (outer_radius + inner_radius) / 2
    _draw_circular_text(
        canvas, UNIVERSITY_NAME.upper(), x, y, text_radius, start_deg=-100, end_deg=100, font="Helvetica-Bold", size=6.2
    )
    _draw_circular_text(
        canvas, "OFFICIAL SEAL", x, y, text_radius, start_deg=235, end_deg=125, font="Helvetica-Bold", size=6.2,
        flip=True,
    )

    _draw_star(canvas, x, y, inner_radius * 0.42, inner_radius * 0.16)
    canvas.restoreState()


def generate_transcript_pdf(student_name: str, semesters: list[ResultSemesterEntry]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TranscriptTitle", parent=styles["Title"], fontSize=16)
    heading_style = ParagraphStyle("SemesterHeading", parent=styles["Heading2"], spaceBefore=12)

    story = [
        Paragraph(UNIVERSITY_NAME, title_style),
        Paragraph("Official Academic Transcript", styles["Heading3"]),
        Spacer(1, 0.15 * inch),
        Paragraph(f"Student: {student_name}", styles["Normal"]),
        Spacer(1, 0.25 * inch),
    ]

    if not semesters:
        story.append(Paragraph("No published results are available yet.", styles["Normal"]))
    else:
        for semester in semesters:
            story.append(Paragraph(f"{semester.semester_name} — GPA: {semester.gpa:.2f}", heading_style))
            table_data = [["Course", "Grade", "Grade Points"]]
            for course in semester.courses:
                table_data.append([course.course_name, course.grade_letter, f"{course.grade_point:.2f}"])
            table = Table(table_data, colWidths=[3.2 * inch, 1.5 * inch, 1.5 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 0.1 * inch))

    doc.build(story, onFirstPage=_draw_seal, onLaterPages=_draw_seal)
    return buffer.getvalue()
