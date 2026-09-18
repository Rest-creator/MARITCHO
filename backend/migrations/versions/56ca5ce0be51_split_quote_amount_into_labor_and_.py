"""split quote amount into labor and materials on jobs and crew orders

Revision ID: 56ca5ce0be51
Revises: b4bcfbff527d
Create Date: 2026-09-18 11:40:12.021329

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '56ca5ce0be51'
down_revision: Union[str, Sequence[str], None] = 'b4bcfbff527d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'crew_orders', sa.Column('labor_amount', sa.Numeric(precision=10, scale=2), nullable=True)
    )
    op.add_column(
        'crew_orders',
        sa.Column('materials_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.add_column(
        'jobs', sa.Column('labor_amount', sa.Numeric(precision=10, scale=2), nullable=True)
    )
    op.add_column(
        'jobs', sa.Column('materials_amount', sa.Numeric(precision=10, scale=2), nullable=True)
    )

    op.create_check_constraint(
        'check_job_quote_equals_labor_plus_materials',
        'jobs',
        '(quote_amount IS NULL AND labor_amount IS NULL AND materials_amount IS NULL)'
        ' OR (quote_amount IS NOT NULL AND labor_amount IS NOT NULL'
        ' AND materials_amount IS NOT NULL'
        ' AND quote_amount = labor_amount + materials_amount)',
    )
    op.create_check_constraint(
        'check_crew_order_quote_equals_labor_plus_materials',
        'crew_orders',
        '(quote_amount IS NULL AND labor_amount IS NULL AND materials_amount IS NULL)'
        ' OR (quote_amount IS NOT NULL AND labor_amount IS NOT NULL'
        ' AND materials_amount IS NOT NULL'
        ' AND quote_amount = labor_amount + materials_amount)',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('check_crew_order_quote_equals_labor_plus_materials', 'crew_orders')
    op.drop_constraint('check_job_quote_equals_labor_plus_materials', 'jobs')

    op.drop_column('jobs', 'materials_amount')
    op.drop_column('jobs', 'labor_amount')
    op.drop_column('crew_orders', 'materials_amount')
    op.drop_column('crew_orders', 'labor_amount')
