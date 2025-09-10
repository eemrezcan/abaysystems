"""add unit_price to system_material_template

Revision ID: 1d5358e3f548
Revises: 9afdba4ce1e8
Create Date: 2025-09-10 13:01:08.353837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d5358e3f548'
down_revision: Union[str, Sequence[str], None] = '9afdba4ce1e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "system_material_template",
        sa.Column("unit_price", sa.Numeric(), nullable=True)
        # İstersen: sa.Numeric(12, 4)
    )

def downgrade():
    op.drop_column("system_material_template", "unit_price")
