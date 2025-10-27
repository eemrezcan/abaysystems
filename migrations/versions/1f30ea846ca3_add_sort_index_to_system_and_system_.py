"""add sort_index to system and system_variant

Revision ID: 1f30ea846ca3
Revises: 54c6abd5df8b
Create Date: 2025-10-27 14:39:54.515616

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = '1f30ea846ca3'
down_revision: Union[str, Sequence[str], None] = '54c6abd5df8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Kolonlar (geçici server_default=0 ile ekle -> hızlı)
    op.add_column(
        "system",
        sa.Column("sort_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "system_variant",
        sa.Column("sort_index", sa.Integer(), nullable=False, server_default="0"),
    )

    # 2) Mevcut veriyi akıllı doldurma (küçükten büyüğe = önce)
    # Sistemleri: created_at, name ile stabilize edip 10'un katları veriyoruz (araya ekleme payı kalsın)
    conn = op.get_bind()
    conn.execute(
        text(
            """
            WITH ordered AS (
                SELECT id,
                       (ROW_NUMBER() OVER (ORDER BY created_at NULLS LAST, name ASC)) * 10 AS rn
                FROM "system"
                WHERE is_deleted = FALSE
            )
            UPDATE "system" s
            SET sort_index = o.rn
            FROM ordered o
            WHERE s.id = o.id;
            """
        )
    )

    # Varyantları: her system içinde created_at, name ile sırala; 10'un katları ver
    conn.execute(
        text(
            """
            WITH ordered AS (
                SELECT id,
                       (ROW_NUMBER() OVER (
                           PARTITION BY system_id
                           ORDER BY created_at NULLS LAST, name ASC
                       )) * 10 AS rn
                FROM system_variant
                WHERE is_deleted = FALSE
            )
            UPDATE system_variant v
            SET sort_index = o.rn
            FROM ordered o
            WHERE v.id = o.id;
            """
        )
    )

    # 3) Index'ler
    op.create_index(
        "ix_system_sort_index",
        "system",
        ["sort_index"],
        unique=False,
    )
    op.create_index(
        "ix_system_variant_system_sort_index",
        "system_variant",
        ["system_id", "sort_index"],
        unique=False,
    )

    # 4) İstersen server_default’ü kaldır (opsiyonel)
    op.alter_column("system", "sort_index", server_default=None)
    op.alter_column("system_variant", "sort_index", server_default=None)


def downgrade():
    # Söküm: indexleri sil, kolonları kaldır
    op.drop_index("ix_system_variant_system_sort_index", table_name="system_variant")
    op.drop_index("ix_system_sort_index", table_name="system")
    op.drop_column("system_variant", "sort_index")
    op.drop_column("system", "sort_index")
