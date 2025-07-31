"""add order_index to project system tables

Revision ID: 4e0d7c3cdaae
Revises: 6b92d0f8668e
Create Date: 2025-07-31 13:57:46.259306
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4e0d7c3cdaae"
down_revision: Union[str, Sequence[str], None] = "6b92d0f8668e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ――― project_system_profile ―――
    op.add_column(
        "project_system_profile",
        sa.Column("order_index", sa.Integer(), nullable=True),
        schema=None,
    )
    # ――― project_system_glass ―――
    op.add_column(
        "project_system_glass",
        sa.Column("order_index", sa.Integer(), nullable=True),
    )
    # ――― project_system_material ―――
    op.add_column(
        "project_system_material",
        sa.Column("order_index", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("project_system_material", "order_index")
    op.drop_column("project_system_glass", "order_index")
    op.drop_column("project_system_profile", "order_index")
