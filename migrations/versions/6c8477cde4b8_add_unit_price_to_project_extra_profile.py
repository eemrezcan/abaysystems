"""add unit_price to project_extra_profile

Revision ID: 6c8477cde4b8
Revises: bad49275378c
Create Date: 2025-08-01 10:19:18.806913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c8477cde4b8'
down_revision: Union[str, Sequence[str], None] = 'bad49275378c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "project_extra_profile",
        sa.Column("unit_price", sa.Numeric(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("project_extra_profile", "unit_price")
