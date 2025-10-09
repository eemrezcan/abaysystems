"""add indexes for project status filters

Revision ID: 55bc2f0d92ae
Revises: 29a9fdde8b29
Create Date: 2025-10-09 11:30:57.829259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55bc2f0d92ae'
down_revision: Union[str, Sequence[str], None] = '29a9fdde8b29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL'de CONCURRENTLY kullanmak için transaction dışına çık
    op.execute("COMMIT")
    # IF NOT EXISTS ile idempotent (tekrar çalışırsa hata vermez)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_project_paint_status "
        "ON project (paint_status) "
        "WITH (FILLFACTOR=90)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_project_glass_status "
        "ON project (glass_status) "
        "WITH (FILLFACTOR=90)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_project_production_status "
        "ON project (production_status) "
        "WITH (FILLFACTOR=90)"
    )
    # Büyük tabloda online oluşturma için:
    # op.create_index('ix_project_paint_status', 'project', ['paint_status'], postgresql_concurrently=True)
    # op.create_index('ix_project_glass_status', 'project', ['glass_status'], postgresql_concurrently=True)
    # op.create_index('ix_project_production_status', 'project', ['production_status'], postgresql_concurrently=True)


def downgrade() -> None:
    op.execute("COMMIT")
    op.execute("DROP INDEX IF EXISTS ix_project_production_status")
    op.execute("DROP INDEX IF EXISTS ix_project_glass_status")
    op.execute("DROP INDEX IF EXISTS ix_project_paint_status")
    # Alternatif:
    # op.drop_index('ix_project_production_status', table_name='project', postgresql_concurrently=True)
    # op.drop_index('ix_project_glass_status', table_name='project', postgresql_concurrently=True)
    # op.drop_index('ix_project_paint_status', table_name='project', postgresql_concurrently=True)
