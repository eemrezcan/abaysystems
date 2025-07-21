"""drop max_width and max_height from system_variant

Revision ID: bbcae448a88b
Revises: cf25e1282a40
Create Date: 2025-07-22 01:02:57.649858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbcae448a88b'
down_revision: Union[str, Sequence[str], None] = 'cf25e1282a40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # system_variant tablosundan max_width_m ve max_height_m sütunlarını kaldır
    op.drop_column('system_variant', 'max_width_m')
    op.drop_column('system_variant', 'max_height_m')


def downgrade() -> None:
    """Downgrade schema."""
    # rollback için max_width_m ve max_height_m sütunlarını geri ekle
    op.add_column(
        'system_variant',
        sa.Column('max_width_m', sa.Numeric(), nullable=True)
    )
    op.add_column(
        'system_variant',
        sa.Column('max_height_m', sa.Numeric(), nullable=True)
    )
