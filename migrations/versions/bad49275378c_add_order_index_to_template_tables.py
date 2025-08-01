"""add order_index to template tables

Revision ID: bad49275378c
Revises: a7f747eb6eb3
Create Date: 2025-08-01 10:09:36.698891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bad49275378c'
down_revision: Union[str, Sequence[str], None] = 'a7f747eb6eb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # system_glass_template
    op.add_column(
        "system_glass_template",
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )

    # system_material_template
    op.add_column(
        "system_material_template",
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )

    # system_profile_template
    op.add_column(
        "system_profile_template",
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("system_profile_template", "order_index")
    op.drop_column("system_material_template", "order_index")
    op.drop_column("system_glass_template", "order_index")

