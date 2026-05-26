"""add integrity constraints and indexes

Revision ID: 7b1a2c3d4e5f
Revises: 2cafe4652a6b
Create Date: 2026-05-26 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b1a2c3d4e5f"
down_revision: Union[str, None] = "2cafe4652a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE books SET copies_available = copies_total "
        "WHERE copies_available > copies_total"
    )
    op.create_check_constraint(
        "ck_books_copies_available_lte_total",
        "books",
        "copies_available <= copies_total",
    )

    op.create_index("ix_books_title", "books", ["title"])
    op.create_index("ix_books_author", "books", ["author"])
    op.create_index("ix_books_genre", "books", ["genre"])
    op.create_index("ix_members_name", "members", ["name"])
    op.create_index("ix_lending_records_book_id", "lending_records", ["book_id"])
    op.create_index("ix_lending_records_member_id", "lending_records", ["member_id"])
    op.create_index(
        "ix_lending_records_borrowed_at",
        "lending_records",
        ["borrowed_at"],
    )
    op.create_index("ix_lending_records_due_date", "lending_records", ["due_date"])
    op.create_index(
        "ix_lending_records_returned_at",
        "lending_records",
        ["returned_at"],
    )
    op.create_index(
        "uq_lending_active_book_member",
        "lending_records",
        ["book_id", "member_id"],
        unique=True,
        postgresql_where=sa.text("returned_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_lending_active_book_member", table_name="lending_records")
    op.drop_index("ix_lending_records_returned_at", table_name="lending_records")
    op.drop_index("ix_lending_records_due_date", table_name="lending_records")
    op.drop_index("ix_lending_records_borrowed_at", table_name="lending_records")
    op.drop_index("ix_lending_records_member_id", table_name="lending_records")
    op.drop_index("ix_lending_records_book_id", table_name="lending_records")
    op.drop_index("ix_members_name", table_name="members")
    op.drop_index("ix_books_genre", table_name="books")
    op.drop_index("ix_books_author", table_name="books")
    op.drop_index("ix_books_title", table_name="books")
    op.drop_constraint(
        "ck_books_copies_available_lte_total",
        "books",
        type_="check",
    )
