"""add glass_color_id to project_system_glass and project_extra_glass

Revision ID: 29a9fdde8b29
Revises: f058cc7a9f46
Create Date: 2025-09-22 01:37:13.684398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '29a9fdde8b29'
down_revision: Union[str, Sequence[str], None] = 'f058cc7a9f46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # project_system_glass.glass_color_id
    op.add_column(
        "project_system_glass",
        sa.Column("glass_color_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_psg_glass_color_id", "project_system_glass", ["glass_color_id"], unique=False
    )
    op.create_foreign_key(
        "fk_psg_glass_color", "project_system_glass", "color",
        ["glass_color_id"], ["id"], ondelete="SET NULL"
    )

    # project_extra_glass.glass_color_id
    op.add_column(
        "project_extra_glass",
        sa.Column("glass_color_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_peg_glass_color_id", "project_extra_glass", ["glass_color_id"], unique=False
    )
    op.create_foreign_key(
        "fk_peg_glass_color", "project_extra_glass", "color",
        ["glass_color_id"], ["id"], ondelete="SET NULL"
    )


def downgrade():
    # project_extra_glass
    op.drop_constraint("fk_peg_glass_color", "project_extra_glass", type_="foreignkey")
    op.drop_index("ix_peg_glass_color_id", table_name="project_extra_glass")
    op.drop_column("project_extra_glass", "glass_color_id")

    # project_system_glass
    op.drop_constraint("fk_psg_glass_color", "project_system_glass", type_="foreignkey")
    op.drop_index("ix_psg_glass_color_id", table_name="project_system_glass")
    op.drop_column("project_system_glass", "glass_color_id")
