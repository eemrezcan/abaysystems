"""color: add is_default + unique default glass color

Revision ID: 10e4f26e3681
Revises: e57ad267586d
Create Date: 2025-10-22 11:00:29.021669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10e4f26e3681'
down_revision: Union[str, Sequence[str], None] = 'e57ad267586d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) is_default kolonu (varsayılan False)
    op.add_column(
        "color",
        sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
    )

    # 2) Tek default cam rengi kısıtı:
    # PostgreSQL partial unique index: type='glass' AND is_default=true AND is_deleted=false
    op.create_index(
        "uq_color_default_glass",
        "color",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("type = 'glass' AND is_default = true AND is_deleted = false"),
    )

def downgrade():
    op.drop_index("uq_color_default_glass", table_name="color")
    op.drop_column("color", "is_default")
