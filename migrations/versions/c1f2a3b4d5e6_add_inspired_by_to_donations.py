"""add inspired_by to donations

Revision ID: c1f2a3b4d5e6
Revises: bf7c5d3ce2b0
Create Date: 2026-06-20 13:34:23.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1f2a3b4d5e6"
down_revision: Union[str, None] = "0e3f8118994f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add inspired_by column (nullable, indexed)
    op.add_column(
        "donations",
        sa.Column("inspired_by", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ix_donations_inspired_by", "donations", ["inspired_by"], unique=False
    )

    # Add inspired_by_friend_name column (nullable, no index needed)
    op.add_column(
        "donations",
        sa.Column("inspired_by_friend_name", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("donations", "inspired_by_friend_name")
    op.drop_index("ix_donations_inspired_by", table_name="donations")
    op.drop_column("donations", "inspired_by")
