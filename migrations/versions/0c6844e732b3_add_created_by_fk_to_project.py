"""add created_by FK to project

Revision ID: 0c6844e732b3
Revises: bec1611ac105
Create Date: 2025-07-13 17:04:15.375320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c6844e732b3'
down_revision: Union[str, Sequence[str], None] = 'bec1611ac105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'project', 'app_user', ['created_by'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'project', type_='foreignkey')
    op.drop_column('project', 'created_by')
    # ### end Alembic commands ###
