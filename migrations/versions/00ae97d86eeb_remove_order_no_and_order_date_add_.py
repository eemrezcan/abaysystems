"""remove order_no and order_date, add project_name

Revision ID: 00ae97d86eeb
Revises: bc5d48c0e649
Create Date: 2025-07-21 23:27:45.047837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00ae97d86eeb'
down_revision: Union[str, Sequence[str], None] = 'bc5d48c0e649'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Yeni sütunu ekle
    op.add_column(
        'project',
        sa.Column('project_name', sa.String(length=100), nullable=False, server_default='')
    )
# 2) Eski sütunları sil
    op.drop_column('project', 'order_no')
    op.drop_column('project', 'order_date')
# 3) Server default’u kaldır (isteğe bağlı)
    op.alter_column('project', 'project_name', server_default=None)



def downgrade() -> None:
# rollback için önce eski sütunları geri ekle
    op.add_column(
        'project',
        sa.Column('order_date', sa.Date(), nullable=True)
    )
    op.add_column(
        'project',
        sa.Column('order_no', sa.String(length=50), nullable=True)
    )
# project_name sütununu kaldır
    op.drop_column('project', 'project_name')

