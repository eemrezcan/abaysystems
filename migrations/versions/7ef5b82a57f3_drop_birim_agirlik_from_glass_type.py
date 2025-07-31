"""drop birim_agirlik from glass_type

Revision ID: 7ef5b82a57f3
Revises: 00ae97d86eeb
Create Date: 2025-07-22 00:39:55.403996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ef5b82a57f3'
down_revision: Union[str, Sequence[str], None] = '00ae97d86eeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # # glass_type tablosundan birim_agirlik sütununu düş
    # op.drop_column('glass_type', 'birim_agirlik')
    pass

def downgrade() -> None:
    """Downgrade schema."""
    # # rollback: birim_agirlik sütununu yeniden ekle
    # op.add_column(
    #     'glass_type',
    #     sa.Column('birim_agirlik', sa.Numeric(), nullable=False, server_default='0')
    # )
    # # varsayılan değeri kaldırmak isterseniz:
    # op.alter_column('glass_type', 'birim_agirlik', server_default=None)
    pass