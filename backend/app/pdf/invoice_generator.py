"""
PDF invoice generation (FR-042).

Generated on demand within the request/response cycle for
`GET /fees/invoices/{id}` — same pattern as Milestone 7's
`transcript_generator.py`: run via `fastapi.concurrency.run_in_threadpool`
to keep the async event loop unblocked (System_Architecture.md §2.4)
while still matching the documented synchronous binary-stream response.
`invoice.pdf_url` stays permanently null — nothing is pre-generated or
stored (see Database_Design.md §6.25's design note).

Production-readiness audit gap closure: there is no separate "Receipt"
generator anywhere in this codebase, and the brief's own instruction was
not to build a duplicate implementation unnecessarily — this same
document already contains everything a receipt needs (amount paid, date,
status). The only change here is the document title: once
`invoice_data["status"] == "paid"`, the same PDF is labeled "Fee Receipt"
instead of "Fee Invoice", since a fully-paid invoice *is* the receipt of
that payment.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

UNIVERSITY_NAME = "ICT Education University"


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    is_receipt = invoice_data["status"] == "paid"
    document_label = "Fee Receipt" if is_receipt else "Fee Invoice"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("InvoiceTitle", parent=styles["Title"], fontSize=16)

    table_data = [
        ["Fee", invoice_data["fee_structure_name"]],
        ["Amount", f"{invoice_data['amount']:.2f}"],
        ["Due Date", invoice_data["due_date"].isoformat()],
        ["Status", invoice_data["status"].replace("_", " ").title()],
        ["Amount Paid", f"{invoice_data['paid']:.2f}"],
        ["Outstanding Balance", f"{invoice_data['outstanding']:.2f}"],
    ]
    table = Table(table_data, colWidths=[2.2 * inch, 3.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
            ]
        )
    )

    story = [
        Paragraph(UNIVERSITY_NAME, title_style),
        Paragraph(document_label, styles["Heading3"]),
        Spacer(1, 0.15 * inch),
        Paragraph(f"Student: {invoice_data['student_name']}", styles["Normal"]),
        Paragraph(f"Issued: {invoice_data['issued_at'].date().isoformat()}", styles["Normal"]),
        Spacer(1, 0.25 * inch),
        table,
    ]

    doc.build(story)
    return buffer.getvalue()
