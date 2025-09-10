"""add unit_price to project_system_material and project_extra_material

Revision ID: 431f429ef872
Revises: 1d5358e3f548
Create Date: 2025-09-10 13:14:30.797372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '431f429ef872'
down_revision: Union[str, Sequence[str], None] = '1d5358e3f548'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "project_system_material",
        sa.Column("unit_price", sa.Numeric(), nullable=True)   # istersen Numeric(12,4)
    )
    op.add_column(
        "project_extra_material",
        sa.Column("unit_price", sa.Numeric(), nullable=True)
    )

def downgrade():
    op.drop_column("project_extra_material", "unit_price")
    op.drop_column("project_system_material", "unit_price")
