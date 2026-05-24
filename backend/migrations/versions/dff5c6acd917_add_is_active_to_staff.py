"""add is_active to staff

Revision ID: dff5c6acd917
Revises: 94d145e6a064
Create Date: 2026-05-24 20:57:48.899288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dff5c6acd917"
down_revision: Union[str, None] = "94d145e6a064"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "staff",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("staff", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_column("staff", "is_active")
