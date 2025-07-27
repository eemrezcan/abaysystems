"""Add company_name, remove email from customer

Revision ID: bccf8eedbe13
Revises: 0245e4ac189d
Create Date: 2025-07-27 23:44:40.456808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bccf8eedbe13'
down_revision: Union[str, Sequence[str], None] = '0245e4ac189d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) company_name sütununu NULL kabul edecek şekilde ekle
    op.add_column('customer',
        sa.Column('company_name', sa.String(length=100), nullable=True)
    )
    # 2) Var olan kayıtlara varsayılan atama (name değerini kopyala)
    op.execute(
        "UPDATE customer SET company_name = name WHERE company_name IS NULL"
    )
    # 3) company_name sütununu NOT NULL yap
    op.alter_column('customer', 'company_name', nullable=False)
    # 4) email sütununu kaldır
    op.drop_column('customer', 'email')


def downgrade() -> None:
    """Downgrade schema."""
    # 1) email sütununu geri ekle (nullable)
    op.add_column('customer',
        sa.Column('email', sa.VARCHAR(length=100), nullable=True)
    )
    # 2) company_name sütununu düşür
    op.drop_column('customer', 'company_name')
