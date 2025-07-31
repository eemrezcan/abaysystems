"""fix customer dealer_id FK

Revision ID: bec1611ac105
Revises: c41c62758024
Create Date: 2025-07-12 22:46:12.873497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bec1611ac105'
down_revision: Union[str, Sequence[str], None] = 'c41c62758024'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # FK’yi düzelt – tabloyu yeniden yaratma!
    op.drop_constraint(
        "customer_dealer_id_fkey",
        "customer",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None,               # otomatik isimlendir
        "customer",         # kaynak tablo
        "app_user",         # hedef tablo
        ["dealer_id"],      # kaynak sütun(lar)
        ["id"],             # hedef sütun(lar)
        ondelete="SET NULL"
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    # eski FK’yi geri koy
    op.drop_constraint(
        None, "customer", type_="foreignkey"
    )
    op.create_foreign_key(
        "customer_dealer_id_fkey",
        "customer",
        "app_user",
        ["dealer_id"],
        ["id"],
    )

