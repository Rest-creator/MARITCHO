"""add progressive vetting tiers: worker vetting references and vouches

Revision ID: c776d5d98df3
Revises: 56ca5ce0be51
Create Date: 2026-09-18 11:50:29.473550

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c776d5d98df3'
down_revision: Union[str, Sequence[str], None] = '56ca5ce0be51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'worker_references',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('worker_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['persons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_worker_references_worker_id'), 'worker_references', ['worker_id'], unique=False
    )
    op.create_table(
        'worker_vetting',
        sa.Column('worker_id', sa.UUID(), nullable=False),
        sa.Column('id_photo_url', sa.String(length=255), nullable=True),
        sa.Column('id_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['persons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('worker_id'),
    )
    op.create_table(
        'worker_vouches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('worker_id', sa.UUID(), nullable=False),
        sa.Column('voucher_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('worker_id != voucher_id', name='check_worker_vouches_no_self_vouch'),
        sa.ForeignKeyConstraint(['voucher_id'], ['persons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worker_id'], ['persons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('worker_id', 'voucher_id', name='uq_worker_vouches_worker_voucher'),
    )
    op.create_index(
        op.f('ix_worker_vouches_voucher_id'), 'worker_vouches', ['voucher_id'], unique=False
    )
    op.create_index(
        op.f('ix_worker_vouches_worker_id'), 'worker_vouches', ['worker_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_worker_vouches_worker_id'), table_name='worker_vouches')
    op.drop_index(op.f('ix_worker_vouches_voucher_id'), table_name='worker_vouches')
    op.drop_table('worker_vouches')
    op.drop_table('worker_vetting')
    op.drop_index(op.f('ix_worker_references_worker_id'), table_name='worker_references')
    op.drop_table('worker_references')
