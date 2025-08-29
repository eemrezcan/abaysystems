"""partial unique index on app_user.email where is_deleted=false

Revision ID: b8d955410329
Revises: fc13152f24e0
Create Date: 2025-08-30 01:10:52.213245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8d955410329'
down_revision: Union[str, Sequence[str], None] = 'fc13152f24e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Varsa eski UNIQUE kısıtını kaldır
    # Bazı ortamlarda adını bilmediğimiz için sistem kataloğundan düşüyoruz
    op.execute("""
    DO $$
    DECLARE
        consname text;
    BEGIN
        SELECT conname INTO consname
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE t.relname = 'app_user'
          AND n.nspname = 'public'
          AND c.contype = 'u'
          AND array_to_string(ARRAY(
                SELECT attname
                FROM pg_attribute
                WHERE attrelid = c.conrelid
                  AND ARRAY[attnum] <@ c.conkey
                ORDER BY attnum
              ), ',') = 'email';

        IF consname IS NOT NULL THEN
            EXECUTE format('ALTER TABLE public.app_user DROP CONSTRAINT %I', consname);
        END IF;
    END$$;
    """)

    # 2) Aktif kullanıcılar arasında çakışma olmadığını doğrula (güvenli kurulum)
    op.execute("""
    DO $$
    DECLARE
        dup_count int;
    BEGIN
        SELECT COUNT(*) INTO dup_count FROM (
            SELECT lower(email) AS e, COUNT(*) 
            FROM public.app_user
            WHERE is_deleted = FALSE
            GROUP BY lower(email)
            HAVING COUNT(*) > 1
        ) t;

        IF dup_count > 0 THEN
            RAISE EXCEPTION 'Migration aborted: There are % duplicates among active emails', dup_count;
        END IF;
    END$$;
    """)

    # 3) Partial, case-insensitive UNIQUE index oluştur
    # Not: CONCURRENTLY için autocommit gereklidir; Alembic'te context ile açıyoruz
    ctx = op.get_context()
    with ctx.autocommit_block():
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
            ux_app_user_email_active_ci
            ON public.app_user (lower(email))
            WHERE is_deleted = FALSE;
        """)


def downgrade():
    # 1) Partial unique index'i kaldır
    ctx = op.get_context()
    with ctx.autocommit_block():
        op.execute("""
            DROP INDEX IF EXISTS ux_app_user_email_active_ci;
        """)

    # 2) Eski davranışa dön: tam tablo unique constraint (adını sabit veriyoruz)
    op.execute("""
        ALTER TABLE public.app_user
        ADD CONSTRAINT uq_app_user_email UNIQUE (email);
    """)
