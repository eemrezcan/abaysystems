"""drop legacy glass_color_id from project_*_glass + add helpful indexes

Revision ID: e57ad267586d
Revises: 4b7af4111845
Create Date: 2025-10-20 09:49:33.319139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql


# revision identifiers, used by Alembic.
revision: str = 'e57ad267586d'
down_revision: Union[str, Sequence[str], None] = '4b7af4111845'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fk_name_for_column(bind, table: str, column: str) -> str | None:
    """
    Verilen tabloda, 'column' adındaki kolona bağlı FK'nın adını döndürür (ilk eşleşen).
    """
    insp = sa.inspect(bind)
    for fk in insp.get_foreign_keys(table):
        cols = fk.get("constrained_columns") or []
        if column in cols:
            return fk.get("name")
    return None

def _index_exists(bind, table: str, index_name: str) -> bool:
    insp = sa.inspect(bind)
    for idx in insp.get_indexes(table):
        if idx.get("name") == index_name:
            return True
    return False

def _column_exists(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    for col in insp.get_columns(table):
        if col.get("name") == column:
            return True
    return False


def upgrade():
    bind = op.get_bind()

    # ----------------------------
    # project_system_glass
    # ----------------------------
    with op.batch_alter_table("project_system_glass", schema=None) as batch:
        fk_name = _fk_name_for_column(bind, "project_system_glass", "glass_color_id")
        if fk_name:
            batch.drop_constraint(fk_name, type_="foreignkey")

        if _index_exists(bind, "project_system_glass", "ix_project_system_glass_glass_color_id"):
            batch.drop_index("ix_project_system_glass_glass_color_id")

        if _column_exists(bind, "project_system_glass", "glass_color_id"):
            batch.drop_column("glass_color_id")

        if not _index_exists(bind, "project_system_glass", "ix_psg_proj_sys_id_glass_type"):
            batch.create_index(
                "ix_psg_proj_sys_id_glass_type",
                ["project_system_id", "glass_type_id"],
                unique=False,
            )
        if not _index_exists(bind, "project_system_glass", "ix_psg_color_ids_pair"):
            batch.create_index(
                "ix_psg_color_ids_pair",
                ["glass_color_id_1", "glass_color_id_2"],
                unique=False,
            )

    # ----------------------------
    # project_extra_glass
    # ----------------------------
    with op.batch_alter_table("project_extra_glass", schema=None) as batch:
        fk_name = _fk_name_for_column(bind, "project_extra_glass", "glass_color_id")
        if fk_name:
            batch.drop_constraint(fk_name, type_="foreignkey")

        if _index_exists(bind, "project_extra_glass", "ix_project_extra_glass_glass_color_id"):
            batch.drop_index("ix_project_extra_glass_glass_color_id")

        if _column_exists(bind, "project_extra_glass", "glass_color_id"):
            batch.drop_column("glass_color_id")

        if not _index_exists(bind, "project_extra_glass", "ix_peg_project_glass_type"):
            batch.create_index(
                "ix_peg_project_glass_type",
                ["project_id", "glass_type_id"],
                unique=False,
            )
        if not _index_exists(bind, "project_extra_glass", "ix_peg_color_ids_pair"):
            batch.create_index(
                "ix_peg_color_ids_pair",
                ["glass_color_id_1", "glass_color_id_2"],
                unique=False,
            )


def downgrade():
    # Geri al: eski tekli kolonu geri ekle (FK + index’leriyle)
    with op.batch_alter_table("project_system_glass", schema=None) as batch:
        try:
            batch.add_column(sa.Column("glass_color_id", psql.UUID(as_uuid=True), nullable=True))
        except Exception:
            pass
        try:
            batch.create_foreign_key(
                "project_system_glass_glass_color_id_fkey",
                "color",
                local_cols=["glass_color_id"],
                remote_cols=["id"],
                ondelete=None,
            )
        except Exception:
            pass
        try:
            batch.create_index("ix_project_system_glass_glass_color_id", ["glass_color_id"])
        except Exception:
            pass

        # Downgrade’te ek indexleri kaldır
        for idx in ("ix_psg_proj_sys_id_glass_type", "ix_psg_color_ids_pair"):
            try:
                batch.drop_index(idx)
            except Exception:
                pass

    with op.batch_alter_table("project_extra_glass", schema=None) as batch:
        try:
            batch.add_column(sa.Column("glass_color_id", psql.UUID(as_uuid=True), nullable=True))
        except Exception:
            pass
        try:
            batch.create_foreign_key(
                "project_extra_glass_glass_color_id_fkey",
                "color",
                local_cols=["glass_color_id"],
                remote_cols=["id"],
                ondelete=None,
            )
        except Exception:
            pass
        try:
            batch.create_index("ix_project_extra_glass_glass_color_id", ["glass_color_id"])
        except Exception:
            pass

        for idx in ("ix_peg_project_glass_type", "ix_peg_color_ids_pair"):
            try:
                batch.drop_index(idx)
            except Exception:
                pass
