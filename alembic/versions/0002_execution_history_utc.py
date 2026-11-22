"""Persist pipeline execution history and use timezone-aware timestamps.

Revision ID: 0002_execution_history_utc
Revises: 0001_initial
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_execution_history_utc"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipeline_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pipeline_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=200)),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("classification", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('success', 'failure', 'cancelled', 'unknown')",
            name="ck_pipeline_executions_status",
        ),
        sa.ForeignKeyConstraint(["pipeline_id"], ["pipelines.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "pipeline_id", "external_id", name="uq_pipeline_executions_pipeline_external"
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_pipeline_executions_pipeline_created",
        "pipeline_executions",
        ["pipeline_id", "created_at"],
        if_not_exists=True,
    )

    if op.get_bind().dialect.name == "postgresql":
        for table_name in (
            "pipelines",
            "test_executions",
            "infrastructure_findings",
            "notification_rules",
            "notifications",
        ):
            op.alter_column(
                table_name,
                "created_at",
                existing_type=sa.DateTime(),
                type_=sa.DateTime(timezone=True),
                postgresql_using="created_at AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    op.drop_index(
        "ix_pipeline_executions_pipeline_created",
        table_name="pipeline_executions",
        if_exists=True,
    )
    op.drop_table("pipeline_executions", if_exists=True)
    if op.get_bind().dialect.name == "postgresql":
        for table_name in (
            "notifications",
            "notification_rules",
            "infrastructure_findings",
            "test_executions",
            "pipelines",
        ):
            op.alter_column(
                table_name,
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(),
                postgresql_using="created_at AT TIME ZONE 'UTC'",
            )
