"""add order_index to project system tables

Revision ID: 4e0d7c3cdaae
Revises: 6b92d0f8668e
Create Date: 2025-07-31 13:57:46.259306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e0d7c3cdaae'
down_revision: Union[str, Sequence[str], None] = '6b92d0f8668e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# … revision, down_revision vs. aynen kalsın …

def _add_column_if_missing(table_name: str, column: sa.Column):
    """Helper: tabloya kolon yoksa ekle."""
    conn = op.get_bind()
    insp = inspect(conn)
    column_names = {c["name"] for c in insp.get_columns(table_name)}
    if column.name not in column_names:
        op.add_column(table_name, column)

def upgrade() -> None:
    col = sa.Column("order_index", sa.Integer(), nullable=True)
    _add_column_if_missing("project_system_profile", col.copy())
    _add_column_if_missing("project_system_glass",   col.copy())
    _add_column_if_missing("project_system_material", col.copy())

def downgrade() -> None:
    # Downgrade’de IF EXISTS kullanmak daha pratik
    op.execute("ALTER TABLE project_system_material DROP COLUMN IF EXISTS order_index")
    op.execute("ALTER TABLE project_system_glass   DROP COLUMN IF EXISTS order_index")
    op.execute("ALTER TABLE project_system_profile DROP COLUMN IF EXISTS order_index")


