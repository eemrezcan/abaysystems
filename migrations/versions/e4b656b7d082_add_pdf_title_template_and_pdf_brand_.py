"""add pdf_title_template and pdf_brand tables

Revision ID: e4b656b7d082
Revises: 78dbff81f127
Create Date: 2025-09-05 23:30:17.617350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e4b656b7d082'
down_revision: Union[str, Sequence[str], None] = '78dbff81f127'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "pdf_title_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("key", name="uq_pdf_title_template_key"),
    )
    op.create_index("ix_pdf_title_template_key", "pdf_title_template", ["key"], unique=False)

    op.create_table(
        "pdf_brand",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("key", name="uq_pdf_brand_key"),
    )
    op.create_index("ix_pdf_brand_key", "pdf_brand", ["key"], unique=False)


def downgrade():
    op.drop_index("ix_pdf_brand_key", table_name="pdf_brand")
    op.drop_table("pdf_brand")

    op.drop_index("ix_pdf_title_template_key", table_name="pdf_title_template")
    op.drop_table("pdf_title_template")
