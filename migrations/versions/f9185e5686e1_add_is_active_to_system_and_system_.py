"""add is_active to system and system_variant

Revision ID: f9185e5686e1
Revises: 1147cad3ab94
Create Date: 2025-10-16 19:10:59.097450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9185e5686e1'
down_revision: Union[str, Sequence[str], None] = '1147cad3ab94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # system.is_active
    op.add_column(
        "system",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    # system_variant.is_active
    op.add_column(
        "system_variant",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    # Emniyet güncellemesi: mevcut satırlar null kalmasın (bazı sürümlerde gerekmez, biz yine de netleştiriyoruz)
    op.execute("UPDATE system SET is_active = TRUE WHERE is_active IS NULL;")
    op.execute("UPDATE system_variant SET is_active = TRUE WHERE is_active IS NULL;")


def downgrade() -> None:
    op.drop_column("system_variant", "is_active")
    op.drop_column("system", "is_active")
