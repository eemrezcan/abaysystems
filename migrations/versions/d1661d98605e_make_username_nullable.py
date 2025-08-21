"""make username nullable

Revision ID: d1661d98605e
Revises: 7442ab2d157b
Create Date: 2025-08-12 17:16:58.354758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1661d98605e'
down_revision: Union[str, Sequence[str], None] = '7442ab2d157b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # username kolonunu nullable yap
    op.alter_column(
        "app_user",
        "username",
        existing_type=sa.String(length=50),
        nullable=True,
    )

def downgrade():
    # Geri alırken NULL kullanıcı adlarını benzersiz placeholder ile doldur (unique ihlali olmasın)
    op.execute("UPDATE app_user SET username = 'temp_' || substr(id::text,1,8) WHERE username IS NULL;")
    op.alter_column(
        "app_user",
        "username",
        existing_type=sa.String(length=50),
        nullable=False,
    )