"""add dealer_profile_picture table

Revision ID: ea7b5605af40
Revises: e4b656b7d082
Create Date: 2025-09-05 23:35:10.750813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ea7b5605af40'
down_revision: Union[str, Sequence[str], None] = 'e4b656b7d082'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "dealer_profile_picture",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_dealer_profile_picture_user"),
    )
    op.create_index("ix_dealer_profile_picture_user_id", "dealer_profile_picture", ["user_id"], unique=False)


def downgrade():
    op.drop_index("ix_dealer_profile_picture_user_id", table_name="dealer_profile_picture")
    op.drop_table("dealer_profile_picture")
