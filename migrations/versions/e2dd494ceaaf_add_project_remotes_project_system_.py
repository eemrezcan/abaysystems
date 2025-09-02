"""add project remotes (project_system_remote, project_extra_remote)

Revision ID: e2dd494ceaaf
Revises: 81c572e69f82
Create Date: 2025-09-02 13:54:20.287713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e2dd494ceaaf'
down_revision: Union[str, Sequence[str], None] = '81c572e69f82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Varyant altı kumandalar
    op.create_table(
        "project_system_remote",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_system_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("project_system.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("remote_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("remote.id"),
                  nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
    )
    # (Opsiyonel) Sorguları hızlandırmak için index’ler
    op.create_index("ix_psr_project_system", "project_system_remote", ["project_system_id"])
    op.create_index("ix_psr_remote", "project_system_remote", ["remote_id"])
    op.create_index("ix_psr_order", "project_system_remote", ["project_system_id", "order_index"])

    # (Opsiyonel) Aynı project_system içinde aynı remote tekrar eklenmesin
    # op.create_unique_constraint(
    #     "uq_psr_project_system_remote",
    #     "project_system_remote",
    #     ["project_system_id", "remote_id"]
    # )

    # 2) Proje geneli ekstra kumandalar
    op.create_table(
        "project_extra_remote",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("project.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("remote_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("remote.id"),
                  nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_per_project", "project_extra_remote", ["project_id"])
    op.create_index("ix_per_remote", "project_extra_remote", ["remote_id"])


def downgrade():
    op.drop_index("ix_per_remote", table_name="project_extra_remote")
    op.drop_index("ix_per_project", table_name="project_extra_remote")
    op.drop_table("project_extra_remote")

    # psr indexleri
    op.drop_index("ix_psr_order", table_name="project_system_remote")
    op.drop_index("ix_psr_remote", table_name="project_system_remote")
    op.drop_index("ix_psr_project_system", table_name="project_system_remote")
    # op.drop_constraint("uq_psr_project_system_remote", "project_system_remote", type_="unique")
    op.drop_table("project_system_remote")