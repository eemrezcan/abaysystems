"""add is_painted to project profiles

Revision ID: da762e56d7fc
Revises: 207f63c801c3
Create Date: 2025-09-11 15:27:54.015525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da762e56d7fc'
down_revision: Union[str, Sequence[str], None] = '207f63c801c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # --- 1) project_system_profile → is_painted: NOT NULL, önce server_default=false ile ekle
    op.add_column(
        "project_system_profile",
        sa.Column("is_painted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    # ardından default'u kaldır (uygulama tarafı default=False kullanacak)
    op.alter_column("project_system_profile", "is_painted", server_default=None)

    # --- 2) project_extra_profile → is_painted
    op.add_column(
        "project_extra_profile",
        sa.Column("is_painted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.alter_column("project_extra_profile", "is_painted", server_default=None)


def downgrade():
    op.drop_column("project_extra_profile", "is_painted")
    op.drop_column("project_system_profile", "is_painted")
