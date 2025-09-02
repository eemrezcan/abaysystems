"""add system_remote_template table

Revision ID: 81c572e69f82
Revises: 9b547a36885a
Create Date: 2025-09-02 13:30:28.318195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '81c572e69f82'
down_revision: Union[str, Sequence[str], None] = '9b547a36885a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "system_remote_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("system_variant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("system_variant.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("remote_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("remote.id"),
                  nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    # (Opsiyonel) Sıralı listelemeyi hızlandırmak için index:
    # op.create_index(
    #     "ix_system_remote_tpl_variant_order",
    #     "system_remote_template",
    #     ["system_variant_id", "order_index"]
    # )

    # (Opsiyonel) Aynı variant’a aynı kumandanın iki kez eklenmesini engelle:
    # op.create_unique_constraint(
    #     "uq_system_remote_tpl_variant_remote",
    #     "system_remote_template",
    #     ["system_variant_id", "remote_id"]
    # )


def downgrade():
    # (Varsa önce index/unique constraintleri kaldır)
    # op.drop_constraint("uq_system_remote_tpl_variant_remote", "system_remote_template", type_="unique")
    # op.drop_index("ix_system_remote_tpl_variant_order", table_name="system_remote_template")

    op.drop_table("system_remote_template")