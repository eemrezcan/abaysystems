"""placeholder for lost unit_price migration

Revision ID: 0950ea57718f
Revises: b69d0fc50fd9
Create Date: 2025-07-31
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0950ea57718f"
down_revision: Union[str, Sequence[str], None] = "b69d0fc50fd9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # column was added in later merge migration
    pass


def downgrade() -> None:
    pass
