"""add pdf flags (all true) to project items

Revision ID: 78dbff81f127
Revises: 0201b58506c7
Create Date: 2025-09-04 01:16:32.102014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78dbff81f127'
down_revision: Union[str, Sequence[str], None] = '0201b58506c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRUE = sa.text("true")

PDF_COLUMNS = (
    ("cam_ciktisi",                   TRUE),
    ("profil_aksesuar_ciktisi",       TRUE),
    ("boya_ciktisi",                  TRUE),
    ("siparis_ciktisi",               TRUE),
    ("optimizasyon_detayli_ciktisi",  TRUE),
    ("optimizasyon_detaysiz_ciktisi", TRUE),
)

TABLES = (
    # Project system item'ları
    "project_system_profile",
    "project_system_glass",
    "project_system_material",
    "project_system_remote",
    # Extra item'lar (kullanmak istemezsen bu 4'ü listeden çıkar)
    "project_extra_profile",
    "project_extra_glass",
    "project_extra_material",
    "project_extra_remote",
)

def upgrade() -> None:
    for table in TABLES:
        for col_name, default in PDF_COLUMNS:
            op.add_column(
                table,
                sa.Column(col_name, sa.Boolean(), nullable=False, server_default=default),
            )
    # İstersen server_default'ları kaldırma adımı ekleyebilirsin:
    # for table in TABLES:
    #     for col_name, _ in PDF_COLUMNS:
    #         op.alter_column(table, col_name, server_default=None)

def downgrade() -> None:
    # Tersten sil
    for table in reversed(TABLES):
        for col_name, _ in reversed(PDF_COLUMNS):
            op.drop_column(table, col_name)