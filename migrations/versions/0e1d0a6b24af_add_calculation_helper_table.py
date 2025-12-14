"""add calculation_helper table

Revision ID: 0e1d0a6b24af
Revises: 5c8e1c51f6de
Create Date: 2025-12-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0e1d0a6b24af"
down_revision: Union[str, Sequence[str], None] = "5c8e1c51f6de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calculation_helper",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=True),
        sa.Column("bicak_payi", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("boya_payi", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Tek owner (dealer) için tek kayıt; admin varsayılanı owner_id NULL satırı
    op.create_unique_constraint(
        "uq_calculation_helper_owner", "calculation_helper", ["owner_id"]
    )
    # owner_id IS NULL olan varsayılan satır için de tekil kısıt
    op.create_index(
        "uq_calculation_helper_default_owner_null",
        "calculation_helper",
        ["owner_id"],
        unique=True,
        postgresql_where=sa.text("owner_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_calculation_helper_default_owner_null", table_name="calculation_helper")
    op.drop_constraint("uq_calculation_helper_owner", "calculation_helper", type_="unique")
    op.drop_table("calculation_helper")
