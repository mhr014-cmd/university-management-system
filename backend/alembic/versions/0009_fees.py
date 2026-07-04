"""fees

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-17

Milestone 8 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.23-6.25 for the exact schema this migration implements. Creates
fee_structure, payment, and invoice, including the Milestone 8 design
note's unique (student_id, fee_structure_id) constraint on invoice.

Hand-authored, not produced by `alembic revision --autogenerate` — written
to mirror app/models/fee_structure.py, payment.py, and invoice.py
column-for-column, including index=True/UniqueConstraint/CheckConstraint
declarations on the models themselves (per the Milestone 2 review
finding) so an autogenerate diff-check is expected to be empty.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

invoice_status = postgresql.ENUM("unpaid", "partially_paid", "paid", "overdue", name="invoice_status")


def upgrade() -> None:
    op.create_table(
        "fee_structure",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("semester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["department_id"], ["department.id"], name="fk_fee_structure_department_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["semester_id"], ["semester.id"], name="fk_fee_structure_semester_id", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("amount > 0", name="ck_fee_structure_amount_positive"),
    )

    op.create_table(
        "invoice",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fee_structure_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", invoice_status, nullable=False, server_default="unpaid"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pdf_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"], name="fk_invoice_student_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["fee_structure_id"], ["fee_structure.id"], name="fk_invoice_fee_structure_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("student_id", "fee_structure_id", name="uq_invoice_student_fee_structure"),
    )
    op.create_index("ix_invoice_student_id_status", "invoice", ["student_id", "status"])

    op.create_table(
        "payment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fee_structure_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recorded_by_admin_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("payment_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payment_method", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"], name="fk_payment_student_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["fee_structure_id"], ["fee_structure.id"], name="fk_payment_fee_structure_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_admin_id"], ["admin.id"], name="fk_payment_recorded_by_admin_id", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )
    op.create_index("ix_payment_student_id", "payment", ["student_id"])
    op.create_index("ix_payment_fee_structure_id", "payment", ["fee_structure_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_fee_structure_id", table_name="payment")
    op.drop_index("ix_payment_student_id", table_name="payment")
    op.drop_table("payment")
    op.drop_index("ix_invoice_student_id_status", table_name="invoice")
    op.drop_table("invoice")
    op.drop_table("fee_structure")
    # Unlike creation, op.drop_table() does NOT automatically drop enum
    # types it used — confirmed against a real database during Milestone 2.
    # checkfirst=True so this is a no-op if the type is somehow already gone.
    invoice_status.drop(op.get_bind(), checkfirst=True)
