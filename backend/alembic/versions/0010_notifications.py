"""notifications

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-19

Milestone 9 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.26 for the exact schema this migration implements. Creates notification.

Hand-authored, not produced by `alembic revision --autogenerate` — written
to mirror app/models/notification.py column-for-column, including
index=True/Index declarations on the model itself (per the Milestone 2
review finding) so an autogenerate diff-check is expected to be empty.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

notification_type = postgresql.ENUM(
    "result_published", "schedule_change", "attendance_warning", "fee_due", "other", name="notification_type"
)


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_notification_user_id", ondelete="RESTRICT"),
    )
    op.create_index("ix_notification_user_id_is_read", "notification", ["user_id", "is_read"])
    op.create_index("ix_notification_created_at", "notification", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_notification_created_at", table_name="notification")
    op.drop_index("ix_notification_user_id_is_read", table_name="notification")
    op.drop_table("notification")
    # Unlike creation, op.drop_table() does NOT automatically drop enum
    # types it used — confirmed against a real database during Milestone 2.
    # checkfirst=True so this is a no-op if the type is somehow already gone.
    notification_type.drop(op.get_bind(), checkfirst=True)
