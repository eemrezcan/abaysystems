"""add unit_price to project_system_glass

Revision ID: 8ac5f1e5cb2a
Revises: 1f30ea846ca3
Create Date: 2025-10-27 15:52:21.866449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ac5f1e5cb2a'
down_revision: Union[str, Sequence[str], None] = '1f30ea846ca3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        'project_system_glass',
        sa.Column('unit_price', sa.Numeric(), nullable=True)
    )

def downgrade():
    op.drop_column('project_system_glass', 'unit_price')
