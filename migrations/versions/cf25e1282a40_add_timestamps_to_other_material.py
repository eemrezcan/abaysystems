"""add timestamps to other_material

Revision ID: cf25e1282a40
Revises: 7ef5b82a57f3
Create Date: 2025-07-22 00:47:22.405927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf25e1282a40'
down_revision: Union[str, Sequence[str], None] = '7ef5b82a57f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) created_at ve updated_at sütunlarını ekle
    # op.add_column(
    #     'other_material',
    #     sa.Column(
    #         'created_at',
    #         sa.TIMESTAMP(timezone=True),
    #         server_default=sa.text('now()'),
    #         nullable=False
    #     )
    # )
    # op.add_column(
    #     'other_material',
    #     sa.Column(
    #         'updated_at',
    #         sa.TIMESTAMP(timezone=True),
    #         server_default=sa.text('now()'),
    #         nullable=False
    #     )
    # )
    pass

def downgrade():
    # # rollback: önce updated_at, sonra created_at'i kaldır
    # op.drop_column('other_material', 'updated_at')
    # op.drop_column('other_material', 'created_at')
    pass