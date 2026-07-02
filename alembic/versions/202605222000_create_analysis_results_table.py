"""create analysis results table

Revision ID: 202605222000
Revises: 202605221930
Create Date: 2026-05-22 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202605222000"
down_revision: Union[str, None] = "202605221930"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

analysis_type = postgresql.ENUM(
    "EXECUTIVE_SUMMARY",
    "RISK_ANALYSIS",
    "DATA_EXTRACTION",
    name="analysis_type",
    create_type=False,
)


def upgrade() -> None:
    analysis_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_type", analysis_type, nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_results_document_id", "analysis_results", ["document_id"])
    op.create_index("ix_analysis_results_analysis_type", "analysis_results", ["analysis_type"])


def downgrade() -> None:
    op.drop_index("ix_analysis_results_analysis_type", table_name="analysis_results")
    op.drop_index("ix_analysis_results_document_id", table_name="analysis_results")
    op.drop_table("analysis_results")
    analysis_type.drop(op.get_bind(), checkfirst=True)
