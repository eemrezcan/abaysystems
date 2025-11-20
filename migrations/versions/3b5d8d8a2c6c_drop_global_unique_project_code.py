"""Drop global unique constraint from project_kodu

Revision ID: 3b5d8d8a2c6c
Revises: 2c9a5d07e8ab
Create Date: 2025-11-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "3b5d8d8a2c6c"
down_revision: Union[str, Sequence[str], None] = "2c9a5d07e8ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Global UNIQUE constraint project_project_kodu_key'yi kaldır
    op.drop_constraint("project_project_kodu_key", "project", type_="unique")


def downgrade():
    # Geri yükleme: tekil constraint'i yeniden ekle
    op.create_unique_constraint("project_project_kodu_key", "project", ["project_kodu"])

