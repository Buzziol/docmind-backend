"""create document comparisons table

Revision ID: 202605222100
Revises: 202605222030
Create Date: 2026-05-22 21:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202605222100"
down_revision: Union[str, None] = "202605222030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

document_comparison_type = postgresql.ENUM(
    "GENERAL",
    "RISKS",
    "FINANCIAL",
    "DATES",
    "OBLIGATIONS",
    name="document_comparison_type",
    create_type=False,
)


def upgrade() -> None:
    document_comparison_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "document_comparisons",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("comparison_type", document_comparison_type, nullable=False),
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
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["base_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_comparisons_workspace_id", "document_comparisons", ["workspace_id"])
    op.create_index(
        "ix_document_comparisons_base_document_id",
        "document_comparisons",
        ["base_document_id"],
    )
    op.create_index(
        "ix_document_comparisons_target_document_id",
        "document_comparisons",
        ["target_document_id"],
    )
    op.create_index(
        "ix_document_comparisons_comparison_type",
        "document_comparisons",
        ["comparison_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_document_comparisons_comparison_type", table_name="document_comparisons")
    op.drop_index("ix_document_comparisons_target_document_id", table_name="document_comparisons")
    op.drop_index("ix_document_comparisons_base_document_id", table_name="document_comparisons")
    op.drop_index("ix_document_comparisons_workspace_id", table_name="document_comparisons")
    op.drop_table("document_comparisons")
    document_comparison_type.drop(op.get_bind(), checkfirst=True)
