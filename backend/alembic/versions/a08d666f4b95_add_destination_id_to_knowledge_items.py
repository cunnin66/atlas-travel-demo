"""Add destination_id to knowledge_items

Revision ID: a08d666f4b95
Revises: kb001_pgvector
Create Date: 2025-10-01 03:13:45.205025

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a08d666f4b95"
down_revision = "kb001_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add destination_id column to knowledge_items table
    op.add_column(
        "knowledge_items", sa.Column("destination_id", sa.Integer(), nullable=True)
    )

    # Add foreign key constraint to destinations table
    op.create_foreign_key(
        "knowledge_items_destination_id_fkey",
        "knowledge_items",
        "destinations",
        ["destination_id"],
        ["id"],
    )

    # Add index for better query performance
    op.create_index(
        op.f("ix_knowledge_items_destination_id"),
        "knowledge_items",
        ["destination_id"],
        unique=False,
    )


def downgrade() -> None:
    # Remove index
    op.drop_index(
        op.f("ix_knowledge_items_destination_id"), table_name="knowledge_items"
    )

    # Remove foreign key constraint
    op.drop_constraint(
        "knowledge_items_destination_id_fkey", "knowledge_items", type_="foreignkey"
    )

    # Remove destination_id column
    op.drop_column("knowledge_items", "destination_id")
