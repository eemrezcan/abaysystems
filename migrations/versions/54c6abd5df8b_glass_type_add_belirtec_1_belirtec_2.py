"""glass_type: add belirtec_1 & belirtec_2

Revision ID: 54c6abd5df8b
Revises: b754234c6d00
Create Date: 2025-10-25 19:58:11.636897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54c6abd5df8b'
down_revision: Union[str, Sequence[str], None] = 'b754234c6d00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("glass_type", sa.Column("belirtec_1", sa.Integer(), nullable=True))
    op.add_column("glass_type", sa.Column("belirtec_2", sa.Integer(), nullable=True))

def downgrade():
    op.drop_column("glass_type", "belirtec_2")
    op.drop_column("glass_type", "belirtec_1")