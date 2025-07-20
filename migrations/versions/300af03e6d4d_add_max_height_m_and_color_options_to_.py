"""add max_height_m and color_options to system_variant

Revision ID: 300af03e6d4d
Revises: 16340b18a59a
Create Date: 2025-07-17 00:32:03.619084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '300af03e6d4d'
down_revision: Union[str, Sequence[str], None] = '16340b18a59a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        'system_variant',
        sa.Column('max_height_m', sa.Numeric(), nullable=True),
    )
    op.add_column(
        'system_variant',
        sa.Column('color_options', sa.ARRAY(sa.String()), nullable=True),
    )

def downgrade():
    op.drop_column('system_variant', 'color_options')
    op.drop_column('system_variant', 'max_height_m')

