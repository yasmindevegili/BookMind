"""Cria tabelas collections e collection_books para curadoria editorial

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("slug", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("type", sa.String(50), nullable=False, server_default="curadoria"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_collections_name", "collections", ["name"])
    op.create_index("ix_collections_slug", "collections", ["slug"])

    op.create_table(
        "collection_books",
        sa.Column("collection_id", sa.Integer, sa.ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("book_id", sa.Integer, sa.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("collection_books")
    op.drop_table("collections")
