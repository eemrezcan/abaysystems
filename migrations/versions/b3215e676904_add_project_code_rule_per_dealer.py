"""add project_code_rule per dealer

Revision ID: b3215e676904
Revises: a104096eeb83
Create Date: 2025-09-06 00:55:31.953542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3215e676904'
down_revision: Union[str, Sequence[str], None] = 'a104096eeb83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.create_table(
        "project_code_rule",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prefix", sa.String(length=32), nullable=False),
        sa.Column("separator", sa.String(length=5), nullable=False, server_default="-"),
        sa.Column("padding", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("start_number", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("current_number", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["app_user.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("owner_id", name="uq_pcr_owner"),
        sa.UniqueConstraint("prefix",   name="uq_pcr_prefix"),
    )
    op.create_index("ix_pcr_owner", "project_code_rule", ["owner_id"], unique=False)
    op.create_index("ix_pcr_prefix", "project_code_rule", ["prefix"], unique=False)

def downgrade():
    op.drop_index("ix_pcr_prefix", table_name="project_code_rule")
    op.drop_index("ix_pcr_owner", table_name="project_code_rule")
    op.drop_table("project_code_rule")

