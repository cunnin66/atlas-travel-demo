"""Add knowledge base tables and pgvector support

Revision ID: kb001_pgvector
Revises: f9621e7e20e8
Create Date: 2025-10-01 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "kb001_pgvector"
down_revision = "f9621e7e20e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create knowledge_items table
    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("item_metadata", sa.JSON(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["org_id"], ["orgs.id"]),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_items_id"), "knowledge_items", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_knowledge_items_org_id"), "knowledge_items", ["org_id"], unique=False
    )
    op.create_index(
        op.f("ix_knowledge_items_destination_id"),
        "knowledge_items",
        ["destination_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_items_source_type"),
        "knowledge_items",
        ["source_type"],
        unique=False,
    )

    # Create embeddings table
    op.create_table(
        "embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("knowledge_item_id", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding_vector", Vector(1536), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["knowledge_item_id"], ["knowledge_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_embeddings_id"), "embeddings", ["id"], unique=False)
    op.create_index(
        op.f("ix_embeddings_knowledge_item_id"),
        "embeddings",
        ["knowledge_item_id"],
        unique=False,
    )

    # Create vector index for efficient similarity search
    # Note: This will be created by the setup_vector_index function when needed
    # op.execute("""
    #     CREATE INDEX CONCURRENTLY IF NOT EXISTS embeddings_vector_idx
    #     ON embeddings USING ivfflat (embedding_vector vector_cosine_ops)
    #     WITH (lists = 100)
    # """)


def downgrade() -> None:
    # Drop tables
    op.drop_table("embeddings")
    op.drop_table("knowledge_items")

    # Drop pgvector extension (optional - might be used by other parts)
    # op.execute("DROP EXTENSION IF EXISTS vector")
