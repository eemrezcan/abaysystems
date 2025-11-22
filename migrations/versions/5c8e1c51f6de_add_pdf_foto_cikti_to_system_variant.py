"""add pdf_foto_cikti to system_variant

Revision ID: 5c8e1c51f6de
Revises: 3b5d8d8a2c6c
Create Date: 2025-11-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5c8e1c51f6de"
down_revision: Union[str, Sequence[str], None] = "3b5d8d8a2c6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "system_variant",
        sa.Column("pdf_foto_cikti", sa.String(length=300), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("system_variant", "pdf_foto_cikti")
