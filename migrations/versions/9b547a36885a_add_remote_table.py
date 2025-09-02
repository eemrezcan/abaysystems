"""add remote table

Revision ID: 9b547a36885a
Revises: b8d955410329
Create Date: 2025-09-02 12:21:09.294117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9b547a36885a'
down_revision: Union[str, Sequence[str], None] = 'b8d955410329'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "remote",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("kumanda_isim", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("kapasite", sa.Integer(), nullable=False),

        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),

        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    # Opsiyonel: isim aramalarını hızlandırmak istersen
    # op.create_index("ix_remote_kumanda_isim", "remote", ["kumanda_isim"])


def downgrade():
    # Opsiyonel index oluşturduysan önce onu sil
    # op.drop_index("ix_remote_kumanda_isim", table_name="remote")
    op.drop_table("remote")
