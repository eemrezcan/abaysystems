"""add type & piece_length_mm to project_system_material

Revision ID: 6429bfc27cbb
Revises: 4999c2fe411a
Create Date: 2025-09-03 22:33:04.031172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6429bfc27cbb'
down_revision: Union[str, Sequence[str], None] = '4999c2fe411a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table('project_system_material', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('piece_length_mm', sa.Integer(), nullable=True))

def downgrade():
    with op.batch_alter_table('project_system_material', schema=None) as batch_op:
        batch_op.drop_column('piece_length_mm')
        batch_op.drop_column('type')
