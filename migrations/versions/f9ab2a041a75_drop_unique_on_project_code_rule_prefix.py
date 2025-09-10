"""drop unique on project_code_rule.prefix

Revision ID: f9ab2a041a75
Revises: 431f429ef872
Create Date: 2025-09-10 13:51:06.870453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9ab2a041a75'
down_revision: Union[str, Sequence[str], None] = '431f429ef872'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) 'prefix' üzerindeki UNIQUE kısıtı kaldır (PostgreSQL)
    op.execute("""
    DO $$
    DECLARE
        constr_name text;
    BEGIN
        SELECT con.conname INTO constr_name
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE rel.relname = 'project_code_rule'
          AND con.contype = 'u'
          AND con.conkey = ARRAY[
            (SELECT attnum FROM pg_attribute
             WHERE attrelid = rel.oid AND attname = 'prefix')
          ];
        IF constr_name IS NOT NULL THEN
            EXECUTE format('ALTER TABLE project_code_rule DROP CONSTRAINT %I', constr_name);
        END IF;
    END$$;
    """)

    # 2) 'prefix' için normal (non-unique) index’i garanti altına al
    op.execute("CREATE INDEX IF NOT EXISTS ix_pcr_prefix ON project_code_rule (prefix)")
    

def downgrade():
    # DİKKAT: Aşağıdaki UNIQUE kısıtını geri eklemek,
    # tabloda aynı 'prefix' değerinden birden fazla varsa HATA verecektir.
    # Gerekirse önce tekrarlı verileri temizleyin.

    # 1) Non-unique index’i kaldır (gereksiz tekrar olmasın)
    op.execute("DROP INDEX IF EXISTS ix_pcr_prefix")

    # 2) Tekrar UNIQUE kısıtını ekle
    op.execute("ALTER TABLE project_code_rule ADD CONSTRAINT project_code_rule_prefix_key UNIQUE (prefix)")
