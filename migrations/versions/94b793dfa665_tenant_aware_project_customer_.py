"""tenant-aware: project & customer constraints

Revision ID: 94b793dfa665
Revises: 3720e9a5cf71
Create Date: 2025-08-16 14:25:19.055036

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94b793dfa665'
down_revision: Union[str, Sequence[str], None] = '3720e9a5cf71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_unique_on_columns(insp, table_name, columns_lower_sorted):
    """
    Tablo üzerinde verilen sütun setine (case-insensitive) sahip bir UNIQUE constraint var mı?
    """
    for uc in insp.get_unique_constraints(table_name):
        cols = [c.lower() for c in (uc.get("column_names") or [])]
        if sorted(cols) == sorted(columns_lower_sorted):
            return True, uc["name"]
    return False, None


def _has_index(insp, table_name, index_name):
    return any(ix["name"] == index_name for ix in insp.get_indexes(table_name))


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # ------------------------------
    # PROJECT: global unique'i kaldır, owner+code unique'i ekle, indexler
    # ------------------------------
    # Eski global unique: sadece ('project_kodu')
    exists, old_uc_name = _has_unique_on_columns(insp, "project", ["project_kodu"])
    if exists and old_uc_name:
        op.drop_constraint(old_uc_name, "project", type_="unique")
    else:
        # Geliştirme ortamında default isim olabilir:
        try:
            op.drop_constraint("project_project_kodu_key", "project", type_="unique")
        except Exception:
            pass

    # created_by index
    if not _has_index(insp, "project", "ix_project_created_by"):
        op.create_index("ix_project_created_by", "project", ["created_by"], unique=False)

    # customer_id index
    if not _has_index(insp, "project", "ix_project_customer"):
        op.create_index("ix_project_customer", "project", ["customer_id"], unique=False)

    # owner+code unique
    exists_uc, _ = _has_unique_on_columns(insp, "project", ["created_by", "project_kodu"])
    if not exists_uc:
        op.create_unique_constraint("uq_project_owner_code", "project", ["created_by", "project_kodu"])

    # ------------------------------
    # CUSTOMER: birleşik index + kısmi unique (lower(name), dealer_id) where is_deleted=false
    # ------------------------------
    if not _has_index(insp, "customer", "ix_customer_owner_notdeleted"):
        op.create_index("ix_customer_owner_notdeleted", "customer", ["dealer_id", "is_deleted"], unique=False)

    # Kısmi + expression index için en sağlam yol: raw SQL
    # Not: IF NOT EXISTS PostgreSQL’de mevcut; tekrarlı koşumlarda güvenli.
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_customer_owner_name_active
            ON customer (lower(name), dealer_id)
            WHERE is_deleted = false;
            """
        )
    )


def downgrade():
    # CUSTOMER: kısmi unique'i ve index'i kaldır
    op.execute(sa.text("DROP INDEX IF EXISTS ux_customer_owner_name_active;"))
    try:
        op.drop_index("ix_customer_owner_notdeleted", table_name="customer")
    except Exception:
        pass

    # PROJECT: owner+code unique'i kaldır, created_by/customer_id indexlerini kaldır,
    # global unique'i geri getir
    try:
        op.drop_constraint("uq_project_owner_code", "project", type_="unique")
    except Exception:
        pass

    try:
        op.drop_index("ix_project_created_by", table_name="project")
    except Exception:
        pass

    try:
        op.drop_index("ix_project_customer", table_name="project")
    except Exception:
        pass

    # Eski global unique'i (tek sütuna) geri ekle
    # DİKKAT: Eğer tabloda aynı project_kodu değerine sahip satırlar varsa downgrade burada hata verir.
    op.create_unique_constraint("uq_project_kodu_global", "project", ["project_kodu"])
