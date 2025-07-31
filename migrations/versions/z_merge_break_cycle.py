"""merge all heads to break cycle

Revision ID: z_merge_break_cycle            # rasgele eşsiz bir ID
Revises: 0950ea57718f, 386423d21e5f, 4e0d7c3cdaae,
         6b92d0f8668e, 6ff1f7a1fe8f, a3dd578426be,
         b69d0fc50fd9, de6b88f9532f
Create Date: 2025-07-31
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# !!!  Revision kimliğini yalnızca harf-rakam karışık, boşluksuz bir dize yap
revision: str = "zmerge0001"
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
    """schema merge: no-op"""
    pass


def downgrade() -> None:
    pass
