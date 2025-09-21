"""pdf_brand singleton + hard delete

Revision ID: c7c84ca344b1
Revises: 5545e7ddd5b6
Create Date: 2025-09-21 01:03:38.495394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7c84ca344b1'
down_revision: Union[str, Sequence[str], None] = '5545e7ddd5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 0) Soft-deleted kayıtları tamamen sil (kolonu varsa)
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='pdf_brand' AND column_name='is_deleted'
        ) THEN
            EXECUTE 'DELETE FROM pdf_brand WHERE is_deleted = TRUE';
        END IF;
    END
    $$;
    """)

    # 1) Aynı owner_id'ye ait birden fazla brand varsa, en yenisi hariç hepsini sil
    #    (created_at eşitse id’ye göre karar veriyoruz)
    op.execute("""
    WITH ranked AS (
        SELECT id,
               owner_id,
               created_at,
               ROW_NUMBER() OVER (PARTITION BY owner_id ORDER BY created_at DESC, id DESC) AS rn
        FROM pdf_brand
    )
    DELETE FROM pdf_brand
    USING ranked
    WHERE pdf_brand.id = ranked.id AND ranked.rn > 1;
    """)

    # 2) is_deleted kolonunu varsa düş
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='pdf_brand' AND column_name='is_deleted'
        ) THEN
            ALTER TABLE pdf_brand DROP COLUMN is_deleted;
        END IF;
    END
    $$;
    """)

    # 3) owner_id + key için unique constraint (yoksa ekle)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_pdf_brand_owner_key'
        ) THEN
            ALTER TABLE pdf_brand
            ADD CONSTRAINT uq_pdf_brand_owner_key UNIQUE (owner_id, key);
        END IF;
    END
    $$;
    """)

    # 4) Her kullanıcı için tek brand: owner_id üzerinde unique (yoksa ekle)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_pdf_brand_owner'
        ) THEN
            ALTER TABLE pdf_brand
            ADD CONSTRAINT uq_pdf_brand_owner UNIQUE (owner_id);
        END IF;
    END
    $$;
    """)


def downgrade():
    # 4) owner_id unique constraint'i kaldır (varsa)
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_pdf_brand_owner'
        ) THEN
            ALTER TABLE pdf_brand
            DROP CONSTRAINT uq_pdf_brand_owner;
        END IF;
    END
    $$;
    """)

    # 3) owner_id + key unique constraint'i kaldırmak istersen (opsiyonel)
    # NOT: Eski şemanda genelde bu constraint zaten var olurdu; ihtiyaç yoksa kaldırma.
    # op.execute("""
    # DO $$
    # BEGIN
    #     IF EXISTS (
    #         SELECT 1 FROM pg_constraint
    #         WHERE conname = 'uq_pdf_brand_owner_key'
    #     ) THEN
    #         ALTER TABLE pdf_brand
    #         DROP CONSTRAINT uq_pdf_brand_owner_key;
    #     END IF;
    # END
    # $$;
    # """)

    # 2) is_deleted kolonunu geri ekle (yoksa ekle)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='pdf_brand' AND column_name='is_deleted'
        ) THEN
            ALTER TABLE pdf_brand
            ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
        END IF;
    END
    $$;
    """)