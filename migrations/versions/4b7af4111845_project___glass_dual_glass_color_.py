"""project_*_glass: dual glass color columns (id_1/text_1/id_2/text_2) add+backfill

Revision ID: 4b7af4111845
Revises: f9185e5686e1
Create Date: 2025-10-20 09:21:25.963201

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql


# revision identifiers, used by Alembic.
revision: str = '4b7af4111845'
down_revision: Union[str, Sequence[str], None] = 'f9185e5686e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # --- 1) project_system_glass: kolon ekle ---
    with op.batch_alter_table("project_system_glass", schema=None) as batch:
        batch.add_column(sa.Column("glass_color_id_1", psql.UUID(as_uuid=True), nullable=True))
        batch.add_column(sa.Column("glass_color_1", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("glass_color_id_2", psql.UUID(as_uuid=True), nullable=True))
        batch.add_column(sa.Column("glass_color_2", sa.String(length=50), nullable=True))
        # FK'ler (color.id)
        batch.create_foreign_key(
            "fk_proj_sys_glass_color_id_1__color",
            "color",
            local_cols=["glass_color_id_1"],
            remote_cols=["id"],
            ondelete=None,
        )
        batch.create_foreign_key(
            "fk_proj_sys_glass_color_id_2__color",
            "color",
            local_cols=["glass_color_id_2"],
            remote_cols=["id"],
            ondelete=None,
        )

    # --- 2) project_extra_glass: kolon ekle ---
    with op.batch_alter_table("project_extra_glass", schema=None) as batch:
        batch.add_column(sa.Column("glass_color_id_1", psql.UUID(as_uuid=True), nullable=True))
        batch.add_column(sa.Column("glass_color_1", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("glass_color_id_2", psql.UUID(as_uuid=True), nullable=True))
        batch.add_column(sa.Column("glass_color_2", sa.String(length=50), nullable=True))
        # FK'ler (color.id)
        batch.create_foreign_key(
            "fk_proj_extra_glass_color_id_1__color",
            "color",
            local_cols=["glass_color_id_1"],
            remote_cols=["id"],
            ondelete=None,
        )
        batch.create_foreign_key(
            "fk_proj_extra_glass_color_id_2__color",
            "color",
            local_cols=["glass_color_id_2"],
            remote_cols=["id"],
            ondelete=None,
        )

    # --- 3) Backfill (eski tekli kolonlardan yeni *_1 kolonlarına kopya) ---
    # Not: Bazı tablolarda serbest metin 'glass_color' kolonu hiç olmayabilir.
    # Bu nedenle sadece id kopyalıyoruz; metin kolonunu NULL bırakmak güvenli.
    conn = op.get_bind()

    # project_system_glass: id backfill
    # Eğer tabloda 'glass_color_id' kolonu yoksa bu UPDATE hata verir.
    # Bu yüzden koşullu çalıştırmak için try..except kullanıyoruz.
    try:
        conn.execute(sa.text("""
            UPDATE project_system_glass
               SET glass_color_id_1 = glass_color_id
            WHERE glass_color_id_1 IS NULL
              AND glass_color_id IS NOT NULL
        """))
    except Exception:
        # kolon yoksa sessiz geç
        pass

    # project_extra_glass: id backfill
    try:
        conn.execute(sa.text("""
            UPDATE project_extra_glass
               SET glass_color_id_1 = glass_color_id
            WHERE glass_color_id_1 IS NULL
              AND glass_color_id IS NOT NULL
        """))
    except Exception:
        pass


def downgrade():
    # --- backfill rollback ihtiyacımız yok; sadece yeni kolonları ve FK'leri kaldır ---
    with op.batch_alter_table("project_system_glass", schema=None) as batch:
        # Önce FK'leri sök
        try:
            batch.drop_constraint("fk_proj_sys_glass_color_id_1__color", type_="foreignkey")
        except Exception:
            pass
        try:
            batch.drop_constraint("fk_proj_sys_glass_color_id_2__color", type_="foreignkey")
        except Exception:
            pass
        # Sonra kolonları drop
        for col in ["glass_color_id_1", "glass_color_1", "glass_color_id_2", "glass_color_2"]:
            try:
                batch.drop_column(col)
            except Exception:
                pass

    with op.batch_alter_table("project_extra_glass", schema=None) as batch:
        try:
            batch.drop_constraint("fk_proj_extra_glass_color_id_1__color", type_="foreignkey")
        except Exception:
            pass
        try:
            batch.drop_constraint("fk_proj_extra_glass_color_id_2__color", type_="foreignkey")
        except Exception:
            pass
        for col in ["glass_color_id_1", "glass_color_1", "glass_color_id_2", "glass_color_2"]:
            try:
                batch.drop_column(col)
            except Exception:
                pass
