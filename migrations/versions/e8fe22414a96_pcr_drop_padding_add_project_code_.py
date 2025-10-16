"""pcr: drop padding; add project_code_ledger; backfill

Revision ID: e8fe22414a96
Revises: 55bc2f0d92ae
Create Date: 2025-10-16 10:38:31.075686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8fe22414a96'
down_revision: Union[str, Sequence[str], None] = '55bc2f0d92ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # --- 1) padding ve check constraint'i kaldır (varsa) ---
    op.execute("ALTER TABLE project_code_rule DROP CONSTRAINT IF EXISTS ck_pcr_padding_nonneg;")
    op.execute("ALTER TABLE project_code_rule DROP COLUMN IF EXISTS padding;")

    # --- 2) project_code_ledger tablosu ---
    op.create_table(
        'project_code_ledger',
        sa.Column('owner_id', sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('app_user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('number', sa.BigInteger(), nullable=False),
        sa.Column('project_id', sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('project.id', ondelete='SET NULL'), nullable=True),
        sa.Column('project_kodu', sa.String(length=50), nullable=True),
        sa.Column('used_at', sa.dialects.postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('owner_id', 'number', name='pk_project_code_ledger')
    )
    op.create_index('ix_pcl_owner', 'project_code_ledger', ['owner_id'])
    op.create_index('ix_pcl_owner_number', 'project_code_ledger', ['owner_id', 'number'])

    # --- 3) Backfill: mevcut project'lerden kullanılan numaraları ledger'a doldur ---
    # project.created_by -> owner_id
    # number = project_kodu'nun SONUNDAKI rakamlar (regex: ([0-9]+)$)
    op.execute("""
        INSERT INTO project_code_ledger (owner_id, number, project_id, project_kodu, used_at)
        SELECT
            p.created_by AS owner_id,
            (regexp_matches(p.project_kodu, '([0-9]+)$'))[1]::bigint AS number,
            p.id AS project_id,
            p.project_kodu,
            NOW() AS used_at
        FROM project p
        WHERE p.project_kodu ~ '([0-9]+)$'
        ON CONFLICT ON CONSTRAINT pk_project_code_ledger DO NOTHING;
    """)

    # (Opsiyonel) Bilgi amaçlı: current_number'ı ledger'daki max ile senkronla
    op.execute("""
        UPDATE project_code_rule r
        SET current_number = GREATEST(
            r.current_number,
            COALESCE((
                SELECT MAX(l.number) FROM project_code_ledger l WHERE l.owner_id = r.owner_id
            ), 0)
        )
    """)


def downgrade():
    # --- 1) ledger'ı kaldır ---
    op.drop_index('ix_pcl_owner_number', table_name='project_code_ledger')
    op.drop_index('ix_pcl_owner', table_name='project_code_ledger')
    op.drop_table('project_code_ledger')

    # --- 2) padding kolonunu ve check constraint'i geri getir ---
    op.execute("ALTER TABLE project_code_rule ADD COLUMN padding BIGINT NOT NULL DEFAULT 0;")
    op.create_check_constraint('ck_pcr_padding_nonneg', 'project_code_rule', 'padding >= 0')
