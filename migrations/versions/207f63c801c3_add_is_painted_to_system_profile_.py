"""add is_painted to system_profile_template

Revision ID: 207f63c801c3
Revises: f9ab2a041a75
Create Date: 2025-09-11 15:06:15.817298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '207f63c801c3'
down_revision: Union[str, Sequence[str], None] = 'f9ab2a041a75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Kolonu ekle: mevcut satırlar için güvenli varsayılan (false)
    op.add_column(
        "system_profile_template",
        sa.Column("is_painted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    # 2) Sunucu varsayılanını kaldır: bundan sonra uygulamadaki default=False yeterli
    op.alter_column("system_profile_template", "is_painted", server_default=None)


def downgrade():
    op.drop_column("system_profile_template", "is_painted")
