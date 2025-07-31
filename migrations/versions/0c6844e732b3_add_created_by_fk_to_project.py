"""add created_by FK to project

Revision ID: 0c6844e732b3
Revises: bec1611ac105
Create Date: 2025-07-13 17:04:15.375320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c6844e732b3'
down_revision: Union[str, Sequence[str], None] = 'bec1611ac105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# revision, down_revision satırlarına dokunma
def upgrade() -> None:
    # Sadece FK’yi ekle – kolon ekleme satırını sil!
    # op.add_column('project', sa.Column('created_by', sa.UUID(), nullable=True))  ← SİL veya yorum satırı (#)
    op.create_foreign_key(
        None,              # isim otomatik
        "project",         # kaynak tablo
        "app_user",        # hedef tablo
        ["created_by"],    # kaynak sütun
        ["id"],            # hedef sütun
        ondelete="SET NULL"
    )

def downgrade() -> None:
    # FK’yi geri kaldır
    op.drop_constraint(None, "project", type_="foreignkey")
    # op.drop_column("project", "created_by")   # gerekiyorsa, yoksa PASS

