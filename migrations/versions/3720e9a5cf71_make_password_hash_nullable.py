"""make password_hash nullable

Revision ID: 3720e9a5cf71
Revises: d1661d98605e
Create Date: 2025-08-12 17:22:05.557776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3720e9a5cf71'
down_revision: Union[str, Sequence[str], None] = 'd1661d98605e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "app_user",
        "password_hash",
        existing_type=sa.String(length=200),
        nullable=True,
    )

def downgrade():
    # Geri alırken NULL olanları boş string ile doldur ki NOT NULL'a dönebil
    op.execute("UPDATE app_user SET password_hash = '' WHERE password_hash IS NULL;")
    op.alter_column(
        "app_user",
        "password_hash",
        existing_type=sa.String(length=200),
        nullable=False,
    )