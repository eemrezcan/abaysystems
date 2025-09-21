"""change project.approval_date to timestamptz

Revision ID: f058cc7a9f46
Revises: 96e6aaa515e0
Create Date: 2025-09-21 16:05:38.389902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f058cc7a9f46'
down_revision: Union[str, Sequence[str], None] = '96e6aaa515e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Date -> TIMESTAMPTZ (saat:dk bilgisini tutmak için)
    op.alter_column(
        "project",
        "approval_date",
        type_=sa.TIMESTAMP(timezone=True),
        existing_nullable=True,
        postgresql_using="approval_date::timestamp"
    )


def downgrade():
    # Geri dönüş: TIMESTAMPTZ -> Date (saat bilgisini kaybeder)
    op.alter_column(
        "project",
        "approval_date",
        type_=sa.Date(),
        existing_nullable=True,
        postgresql_using="approval_date::date"
    )
