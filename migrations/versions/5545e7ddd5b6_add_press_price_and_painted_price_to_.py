"""add press_price and painted_price to project

Revision ID: 5545e7ddd5b6
Revises: da762e56d7fc
Create Date: 2025-09-11 16:56:46.714304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5545e7ddd5b6'
down_revision: Union[str, Sequence[str], None] = 'da762e56d7fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Numeric, nullable=True — server_default gerekmez
    op.add_column(
        "project",
        sa.Column("press_price", sa.Numeric(), nullable=True),
    )
    op.add_column(
        "project",
        sa.Column("painted_price", sa.Numeric(), nullable=True),
    )


def downgrade():
    op.drop_column("project", "painted_price")
    op.drop_column("project", "press_price")
