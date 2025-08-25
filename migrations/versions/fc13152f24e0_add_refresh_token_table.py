"""add refresh_token table

Revision ID: fc13152f24e0
Revises: fb27cc598548
Create Date: 2025-08-25 23:43:08.075153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fc13152f24e0'
down_revision: Union[str, Sequence[str], None] = 'fb27cc598548'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_token",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # Yardımcı indexler
    op.create_index("ix_refresh_token_user", "refresh_token", ["user_id"])
    op.create_index("ix_refresh_token_valid", "refresh_token", ["user_id", "expires_at"])


def downgrade() -> None:
    op.drop_index("ix_refresh_token_valid", table_name="refresh_token")
    op.drop_index("ix_refresh_token_user", table_name="refresh_token")
    op.drop_table("refresh_token")
