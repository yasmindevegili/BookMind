"""Convert book status to native PostgreSQL enum

Revision ID: 0001
Revises:
Create Date: 2026-08-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

book_status_enum = sa.Enum(
    "none", "want_to_read", "reading", "read", "abandoned",
    name="bookstatus",
)


def upgrade() -> None:
    book_status_enum.create(op.get_bind(), checkfirst=True)

    op.execute("""
        ALTER TABLE books
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE bookstatus
            USING (
                CASE status
                    WHEN 'nenhum'     THEN 'none'::bookstatus
                    WHEN 'quero_ler'  THEN 'want_to_read'::bookstatus
                    WHEN 'lendo'      THEN 'reading'::bookstatus
                    WHEN 'lido'       THEN 'read'::bookstatus
                    WHEN 'abandonei'  THEN 'abandoned'::bookstatus
                    ELSE 'none'::bookstatus
                END
            ),
            ALTER COLUMN status SET DEFAULT 'none'::bookstatus
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE books
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE varchar(20)
            USING (
                CASE status::text
                    WHEN 'none'         THEN 'nenhum'
                    WHEN 'want_to_read' THEN 'quero_ler'
                    WHEN 'reading'      THEN 'lendo'
                    WHEN 'read'         THEN 'lido'
                    WHEN 'abandoned'    THEN 'abandonei'
                    ELSE 'nenhum'
                END
            ),
            ALTER COLUMN status SET DEFAULT 'nenhum'
    """)

    book_status_enum.drop(op.get_bind(), checkfirst=True)
