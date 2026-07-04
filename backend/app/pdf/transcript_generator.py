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
this project, so the "university seal" (FR-036) is rendered as a simple
drawn circle + text placeholder, not an embedded image — see
PROJECT_PROGRESS.md's Milestone 7 entry.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.result import ResultSemesterEntry

UNIVERSITY_NAME = "ICT Education University"


def _draw_seal(canvas, doc) -> None:
    canvas.saveState()
    x, y, radius = doc.pagesize[0] - 1.3 * inch, doc.pagesize[1] - 1.3 * inch, 0.6 * inch
    canvas.setStrokeColor(colors.HexColor("#1f2937"))
    canvas.setLineWidth(2)
    canvas.circle(x, y, radius, stroke=1, fill=0)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawCentredString(x, y + 6, "OFFICIAL")
    canvas.drawCentredString(x, y - 6, "SEAL")
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
