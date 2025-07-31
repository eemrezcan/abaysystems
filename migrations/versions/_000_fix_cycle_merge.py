"""merge all cycle nodes – fixes CycleDetected

Revision ID: fix_cycle0001
Revises: 0950ea57718f, 386423d21e5f, 4e0d7c3cdaae,
         6b92d0f8668e, 6ff1f7a1fe8f, a3dd578426be,
         b69d0fc50fd9, de6b88f9532f
Create Date: 2025-07-31
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "fix_cycle0001"         # benzersiz ID
down_revision: Union[str, Sequence[str], None] = (
    "0950ea57718f",
    "386423d21e5f",
    "4e0d7c3cdaae",
    "6b92d0f8668e",
    "6ff1f7a1fe8f",
    "a3dd578426be",
    "b69d0fc50fd9",
    "de6b88f9532f",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
