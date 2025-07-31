"""add profile_color_id & glass_color_id to project

Revision ID: b69d0fc50fd9
Revises: 4e0d7c3cdaae
Create Date: 2025-07-31 12:03:30.649338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b69d0fc50fd9'
down_revision: Union[str, Sequence[str], None] = '4e0d7c3cdaae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
