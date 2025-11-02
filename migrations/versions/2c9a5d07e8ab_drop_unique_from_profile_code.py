"""profile: drop unique constraint from profil_kodu

Revision ID: 2c9a5d07e8ab
Revises: 8ac5f1e5cb2a
Create Date: 2025-10-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c9a5d07e8ab'
down_revision: Union[str, Sequence[str], None] = '8ac5f1e5cb2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # profil_kodu kolonu üzerindeki UNIQUE kısıtı kaldır
    op.execute(
        """
        DO $$
        DECLARE
            constr_name text;
        BEGIN
            SELECT con.conname INTO constr_name
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE rel.relname = 'profile'
              AND con.contype = 'u'
              AND con.conkey = ARRAY[
                (SELECT attnum
                 FROM pg_attribute
                 WHERE attrelid = rel.oid AND attname = 'profil_kodu')
              ];

            IF constr_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE profile DROP CONSTRAINT %I', constr_name);
            END IF;
        END$$;
        """
    )


def downgrade():
    # UNIQUE kısıtını geri ekle (varsa tekrar hata olmasın diye isim sabit)
    op.execute("ALTER TABLE profile ADD CONSTRAINT profile_profil_kodu_key UNIQUE (profil_kodu)")
