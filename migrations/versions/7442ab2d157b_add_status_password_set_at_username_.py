"""add status & password_set_at; username nullable

Revision ID: 7442ab2d157b
Revises: c141a423e099
Create Date: 2025-08-12 16:28:57.343168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7442ab2d157b'
down_revision: Union[str, Sequence[str], None] = 'c141a423e099'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Kolonları ekle — status için geçici server_default veriyoruz ki NOT NULL hatası olmasın
    with op.batch_alter_table('app_user') as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=False, server_default='invited'))
        batch_op.add_column(sa.Column('password_set_at', sa.TIMESTAMP(timezone=True), nullable=True))

    # 2) Mevcut kullanıcıları mantıklı değerlere çek
    # Şifresi olanları 'active', olmayanları 'invited' yap
    op.execute("UPDATE app_user SET status='active' WHERE password_hash IS NOT NULL;")
    op.execute("UPDATE app_user SET status='invited' WHERE password_hash IS NULL;")

    # 3) (Varsa) check constraint ekle — bir kere ekle!
    # Eğer autogenerate zaten ck_app_user_status eklediyse BU SATIRI KOYMAYIN.
    op.create_check_constraint(
        'ck_app_user_status', 'app_user',
        "status IN ('invited','active','suspended')"
    )

    # 4) İstersen DB tarafındaki default’u kaldır (ORM’de default zaten 'invited')
    op.alter_column('app_user', 'status', server_default=None)


def downgrade():
    # Downgrade'de önce constraint'i kaldır, sonra kolonları düşür
    # (Constraint’i autogenerate eklediyse isim farklı olabilir — ona göre düzelt)
    try:
        op.drop_constraint('ck_app_user_status', 'app_user', type_='check')
    except Exception:
        pass

    with op.batch_alter_table('app_user') as batch_op:
        batch_op.drop_column('password_set_at')
        batch_op.drop_column('status')
