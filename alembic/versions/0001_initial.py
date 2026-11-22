"""Create initial DeployGuard tables

Revision ID: 0001_initial
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("repository", sa.String(length=500)),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("findings", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        if_not_exists=True,
    )
    op.create_table(
        "test_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_format", sa.String(length=30), nullable=False),
        sa.Column("suite", sa.String(length=200), nullable=False),
        sa.Column("test_name", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("failure_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        if_not_exists=True,
    )
    op.create_table(
        "infrastructure_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("resource", sa.String(length=500), nullable=False),
        sa.Column("rule", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        if_not_exists=True,
    )
    op.create_table(
        "notification_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("minimum_severity", sa.String(length=30), nullable=False),
        sa.Column("webhook_url", sa.String(length=2000)),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        if_not_exists=True,
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("notification_rules")
    op.drop_table("infrastructure_findings")
    op.drop_table("test_executions")
    op.drop_table("pipelines")
