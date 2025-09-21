"""add teklif/status fields and indexes to project

Revision ID: 96e6aaa515e0
Revises: c4efcbee2757
Create Date: 2025-09-21 15:53:39.220774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import expression, text


# revision identifiers, used by Alembic.
revision: str = '96e6aaa515e0'
down_revision: Union[str, Sequence[str], None] = 'c4efcbee2757'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # --- Columns ---
    op.add_column(
        "project",
        sa.Column(
            "is_teklif",
            sa.Boolean(),
            nullable=False,
            server_default=expression.true(),  # var olan kayıtlara True yazılsın
        ),
    )
    op.add_column(
        "project",
        sa.Column(
            "paint_status",
            sa.String(length=50),
            nullable=False,
            server_default=text("'durum belirtilmedi'"),
        ),
    )
    op.add_column(
        "project",
        sa.Column(
            "glass_status",
            sa.String(length=50),
            nullable=False,
            server_default=text("'durum belirtilmedi'"),
        ),
    )
    op.add_column(
        "project",
        sa.Column(
            "production_status",
            sa.String(length=50),
            nullable=False,
            server_default=text("'durum belirtilmedi'"),
        ),
    )
    op.add_column(
        "project",
        sa.Column(
            "approval_date",
            sa.Date(),
            nullable=True,  # kural CRUD'da çalışacak
        ),
    )

    # --- Indexes ---
    op.create_index("ix_project_is_teklif", "project", ["is_teklif"], unique=False)
    op.create_index("ix_project_approval_date", "project", ["approval_date"], unique=False)

    # --- (Opsiyonel) Eski kayıtlara güvenli backfill ---
    # Burada server_default zaten yazdı; fakat explicit güncelleme isterseniz:
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE project
        SET paint_status = 'durum belirtilmedi'
        WHERE paint_status IS NULL
    """))
    conn.execute(text("""
        UPDATE project
        SET glass_status = 'durum belirtilmedi'
        WHERE glass_status IS NULL
    """))
    conn.execute(text("""
        UPDATE project
        SET production_status = 'durum belirtilmedi'
        WHERE production_status IS NULL
    """))


def downgrade():
    op.drop_index("ix_project_approval_date", table_name="project")
    op.drop_index("ix_project_is_teklif", table_name="project")

    op.drop_column("project", "approval_date")
    op.drop_column("project", "production_status")
    op.drop_column("project", "glass_status")
    op.drop_column("project", "paint_status")
    op.drop_column("project", "is_teklif")
