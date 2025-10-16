"""make project.customer_id nullable and ondelete set null

Revision ID: 1147cad3ab94
Revises: e8fe22414a96
Create Date: 2025-10-16 13:05:53.806760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1147cad3ab94'
down_revision: Union[str, Sequence[str], None] = 'e8fe22414a96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None




def upgrade():
    # 1) customer_id'yi nullable yap
    op.alter_column(
        'project',
        'customer_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True
    )

    # 2) FK'yi SET NULL olacak şekilde yeniden yarat
    # Varsayılan isim genelde "project_customer_id_fkey" olur; farklıysa kendi adını kullan.
    with op.batch_alter_table('project', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('project_customer_id_fkey', type_='foreignkey')
        except Exception:
            pass
        batch_op.create_foreign_key(
            'project_customer_id_fkey',
            'customer',
            ['customer_id'],
            ['id'],
            ondelete='SET NULL'
        )

def downgrade():
    # FK'yi eski haline döndür (ondelete yok)
    with op.batch_alter_table('project', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('project_customer_id_fkey', type_='foreignkey')
        except Exception:
            pass
        batch_op.create_foreign_key(
            'project_customer_id_fkey',
            'customer',
            ['customer_id'],
            ['id']
        )

    # Sütunu tekrar NOT NULL yap
    op.alter_column(
        'project',
        'customer_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False
    )
