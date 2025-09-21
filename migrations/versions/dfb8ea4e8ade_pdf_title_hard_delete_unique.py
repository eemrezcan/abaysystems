"""pdf_title hard delete + unique

Revision ID: dfb8ea4e8ade
Revises: c7c84ca344b1
Create Date: 2025-09-21 01:30:15.416388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfb8ea4e8ade'
down_revision: Union[str, Sequence[str], None] = 'c7c84ca344b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 0) Soft-deleted kayıtları sil (kolon varsa)
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='pdf_title_template' AND column_name='is_deleted'
        ) THEN
            EXECUTE 'DELETE FROM pdf_title_template WHERE is_deleted = TRUE';
        END IF;
    END
    $$;
    """)

    # 1) owner+key duplikeleri temizle (en yeni kalsın)
    op.execute("""
    WITH ranked AS (
        SELECT id, owner_id, key, created_at,
               ROW_NUMBER() OVER (PARTITION BY owner_id, key ORDER BY created_at DESC, id DESC) AS rn
        FROM pdf_title_template
    )
    DELETE FROM pdf_title_template p
    USING ranked r
    WHERE p.id = r.id AND r.rn > 1;
    """)

    # 2) is_deleted kolonunu varsa düş
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='pdf_title_template' AND column_name='is_deleted'
        ) THEN
            ALTER TABLE pdf_title_template DROP COLUMN is_deleted;
        END IF;
    END
    $$;
    """)

    # 3) owner_id + key unique constraint (yoksa ekle)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'uq_pdf_title_template_owner_key'
        ) THEN
            ALTER TABLE pdf_title_template
            ADD CONSTRAINT uq_pdf_title_template_owner_key UNIQUE (owner_id, key);
        END IF;
    END
    $$;
    """)

def downgrade():
    # owner+key unique constraint'i kaldır (varsa)
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_pdf_title_template_owner_key') THEN
            ALTER TABLE pdf_title_template DROP CONSTRAINT uq_pdf_title_template_owner_key;
        END IF;
    END
    $$;
    """)

    # is_deleted kolonu geri ekle (yoksa ekle)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='pdf_title_template' AND column_name='is_deleted'
        ) THEN
            ALTER TABLE pdf_title_template
            ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
        END IF;
    END
    $$;
    """)
