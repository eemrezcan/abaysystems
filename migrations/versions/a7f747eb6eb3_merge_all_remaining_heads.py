"""merge all remaining heads

Revision ID: a7f747eb6eb3
Revises: fix_cycle0001, bccf8eedbe13, zmerge0001
Create Date: 2025-08-01 00:16:46.059179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7f747eb6eb3'
down_revision: Union[str, Sequence[str], None] = ('fix_cycle0001', 'bccf8eedbe13', 'zmerge0001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
