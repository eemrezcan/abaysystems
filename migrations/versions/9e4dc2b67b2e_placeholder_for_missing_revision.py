"""placeholder for missing revision

Revision ID: 9e4dc2b67b2e
Revises: 4e0d7c3cdaae
Create Date: 2025-07-31 14:44:05.414479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e4dc2b67b2e'
down_revision: Union[str, Sequence[str], None] = '4e0d7c3cdaae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
