"""scope pdf titles/brands by owner_id

Revision ID: a104096eeb83
Revises: ea7b5605af40
Create Date: 2025-09-06 00:10:42.376877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a104096eeb83'
down_revision: Union[str, Sequence[str], None] = 'ea7b5605af40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ---- pdf_title_template ----
    # Eski unique(key) varsa kaldır
    try:
        op.drop_constraint("uq_pdf_title_template_key", "pdf_title_template", type_="unique")
    except Exception:
        pass

    op.add_column("pdf_title_template", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_pdf_title_template_owner", "pdf_title_template",
        "app_user", ["owner_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_pdf_title_template_owner_id", "pdf_title_template", ["owner_id"])
    op.create_unique_constraint("uq_pdf_title_template_owner_key", "pdf_title_template", ["owner_id", "key"])

    # Mevcut satırlar için bir admin kullanıcıya bağla (varsa)
    op.execute("""
    DO $$
    DECLARE admin_id uuid;
    BEGIN
      SELECT id INTO admin_id FROM app_user WHERE role='admin' ORDER BY created_at NULLS LAST LIMIT 1;
      IF admin_id IS NOT NULL THEN
        UPDATE pdf_title_template SET owner_id = admin_id WHERE owner_id IS NULL;
      END IF;
    END$$;
    """)

    # Owner_id artık zorunlu
    op.alter_column("pdf_title_template", "owner_id", nullable=False)

    # ---- pdf_brand ----
    try:
        op.drop_constraint("uq_pdf_brand_key", "pdf_brand", type_="unique")
    except Exception:
        pass

    op.add_column("pdf_brand", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_pdf_brand_owner", "pdf_brand",
        "app_user", ["owner_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_pdf_brand_owner_id", "pdf_brand", ["owner_id"])
    op.create_unique_constraint("uq_pdf_brand_owner_key", "pdf_brand", ["owner_id", "key"])

    op.execute("""
    DO $$
    DECLARE admin_id uuid;
    BEGIN
      SELECT id INTO admin_id FROM app_user WHERE role='admin' ORDER BY created_at NULLS LAST LIMIT 1;
      IF admin_id IS NOT NULL THEN
        UPDATE pdf_brand SET owner_id = admin_id WHERE owner_id IS NULL;
      END IF;
    END$$;
    """)

    op.alter_column("pdf_brand", "owner_id", nullable=False)

def downgrade():
    # Basitleştirilmiş downgrade (isteğe göre genişletebilirsin)
    op.drop_constraint("uq_pdf_brand_owner_key", "pdf_brand", type_="unique")
    op.drop_index("ix_pdf_brand_owner_id", table_name="pdf_brand")
    op.drop_constraint("fk_pdf_brand_owner", "pdf_brand", type_="foreignkey")
    op.drop_column("pdf_brand", "owner_id")

    op.drop_constraint("uq_pdf_title_template_owner_key", "pdf_title_template", type_="unique")
    op.drop_index("ix_pdf_title_template_owner_id", table_name="pdf_title_template")
    op.drop_constraint("fk_pdf_title_template_owner", "pdf_title_template", type_="foreignkey")
    op.drop_column("pdf_title_template", "owner_id")
