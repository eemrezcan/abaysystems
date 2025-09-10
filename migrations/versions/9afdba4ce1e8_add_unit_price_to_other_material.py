"""add unit_price to other_material

Revision ID: 9afdba4ce1e8
Revises: b3215e676904
Create Date: 2025-09-10 12:47:53.822980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9afdba4ce1e8'
down_revision: Union[str, Sequence[str], None] = 'b3215e676904'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "other_material",
        sa.Column("unit_price", sa.Numeric(), nullable=True)
    )

def downgrade():
    op.drop_column("other_material", "unit_price")
