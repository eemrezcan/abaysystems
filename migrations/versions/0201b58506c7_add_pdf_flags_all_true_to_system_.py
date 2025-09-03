"""add pdf flags (all true) to system templates

Revision ID: 0201b58506c7
Revises: 6429bfc27cbb
Create Date: 2025-09-04 00:41:43.470197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0201b58506c7'
down_revision: Union[str, Sequence[str], None] = '6429bfc27cbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRUE = sa.text("true")

def add_flags(table_name: str):
    op.add_column(table_name, sa.Column("cam_ciktisi",                   sa.Boolean(), nullable=False, server_default=TRUE))
    op.add_column(table_name, sa.Column("profil_aksesuar_ciktisi",       sa.Boolean(), nullable=False, server_default=TRUE))
    op.add_column(table_name, sa.Column("boya_ciktisi",                  sa.Boolean(), nullable=False, server_default=TRUE))
    op.add_column(table_name, sa.Column("siparis_ciktisi",               sa.Boolean(), nullable=False, server_default=TRUE))
    op.add_column(table_name, sa.Column("optimizasyon_detayli_ciktisi",  sa.Boolean(), nullable=False, server_default=TRUE))
    op.add_column(table_name, sa.Column("optimizasyon_detaysiz_ciktisi", sa.Boolean(), nullable=False, server_default=TRUE))

def drop_flags(table_name: str):
    # Tersten sil ki bağımlılık/constraint olasılıklarında sorun çıkmasın
    op.drop_column(table_name, "optimizasyon_detaysiz_ciktisi")
    op.drop_column(table_name, "optimizasyon_detayli_ciktisi")
    op.drop_column(table_name, "siparis_ciktisi")
    op.drop_column(table_name, "boya_ciktisi")
    op.drop_column(table_name, "profil_aksesuar_ciktisi")
    op.drop_column(table_name, "cam_ciktisi")

def upgrade() -> None:
    add_flags("system_profile_template")
    add_flags("system_glass_template")
    add_flags("system_material_template")
    add_flags("system_remote_template")

    # NOT: İstersen aşağıdaki satırlarla server_default'ları kaldırabilirsin.
    # Ama "hepsi default TRUE" istediğin için DB default'larını bırakmak mantıklı.
    # for t in ("system_profile_template","system_glass_template","system_material_template","system_remote_template"):
    #     for c in ("cam_ciktisi","profil_aksesuar_ciktisi","boya_ciktisi","siparis_ciktisi","optimizasyon_detayli_ciktisi","optimizasyon_detaysiz_ciktisi"):
    #         op.alter_column(t, c, server_default=None)

def downgrade() -> None:
    drop_flags("system_remote_template")
    drop_flags("system_material_template")
    drop_flags("system_glass_template")
    drop_flags("system_profile_template")