"""add unit_price to extra_profile_and_glass

Revision ID: c4efcbee2757
Revises: dfb8ea4e8ade
Create Date: 2025-09-21 12:41:06.958075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4efcbee2757'
down_revision: Union[str, Sequence[str], None] = 'dfb8ea4e8ade'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # project_extra_profile: unit_price (zaten olabilir)
    op.execute(
        "ALTER TABLE project_extra_profile "
        "ADD COLUMN IF NOT EXISTS unit_price NUMERIC"
    )

    # project_extra_glass: unit_price (büyük ihtimalle yok)
    op.execute(
        "ALTER TABLE project_extra_glass "
        "ADD COLUMN IF NOT EXISTS unit_price NUMERIC"
    )


def downgrade():
    # Güvenli drop (varsa)
    op.execute(
        "ALTER TABLE project_extra_glass "
        "DROP COLUMN IF EXISTS unit_price"
    )
    op.execute(
        "ALTER TABLE project_extra_profile "
        "DROP COLUMN IF EXISTS unit_price"
    )