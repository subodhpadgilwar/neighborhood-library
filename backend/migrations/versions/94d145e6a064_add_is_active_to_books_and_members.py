"""add is_active to books and members

Revision ID: 94d145e6a064
Revises: 9450a865b6b1
Create Date: 2026-05-24 20:32:16.060649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "94d145e6a064"
down_revision: Union[str, None] = "9450a865b6b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("books", "members", "lending_records")


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.alter_column(table, "is_active", server_default=None)


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_column(table, "is_active")
