"""color: add is_default_2 + unique default2 glass

Revision ID: b754234c6d00
Revises: 10e4f26e3681
Create Date: 2025-10-22 22:36:26.484219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b754234c6d00'
down_revision: Union[str, Sequence[str], None] = '10e4f26e3681'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "color",
        sa.Column("is_default_2", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    # Tekil kısıt: yalnızca glass ve true ve silinmemiş için
    op.create_index(
        "uq_color_default2_glass",
        "color",
        ["is_default_2"],
        unique=True,
        postgresql_where=sa.text("type = 'glass' AND is_default_2 = true AND is_deleted = false"),
    )

def downgrade():
    op.drop_index("uq_color_default2_glass", table_name="color")
    op.drop_column("color", "is_default_2")
