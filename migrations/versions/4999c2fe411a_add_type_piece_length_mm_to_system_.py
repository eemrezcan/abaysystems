"""add type & piece_length_mm to system_material_template

Revision ID: 4999c2fe411a
Revises: e2dd494ceaaf
Create Date: 2025-09-03 22:13:13.300803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4999c2fe411a'
down_revision: Union[str, Sequence[str], None] = 'e2dd494ceaaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Postgres için güvenli: batch_alter_table
    with op.batch_alter_table('system_material_template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('piece_length_mm', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('system_material_template', schema=None) as batch_op:
        batch_op.drop_column('piece_length_mm')
        batch_op.drop_column('type')
