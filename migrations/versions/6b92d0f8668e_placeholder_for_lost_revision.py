"""placeholder for lost revision

Revision ID: 6b92d0f8668e
Revises: 386423d21e5f
Create Date: 2025-07-31 13:02:38.464589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b92d0f8668e'
down_revision: Union[str, Sequence[str], None] = '386423d21e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
