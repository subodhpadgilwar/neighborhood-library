"""add staff roles

Revision ID: 8d2f1c9a4b6e
Revises: 7b1a2c3d4e5f
Create Date: 2026-05-27 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8d2f1c9a4b6e"
down_revision: Union[str, None] = "7b1a2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "staff",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="staff"),
    )
    op.execute("UPDATE staff SET role = 'admin' WHERE is_default_admin = true")
    op.alter_column("staff", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("staff", "role")
