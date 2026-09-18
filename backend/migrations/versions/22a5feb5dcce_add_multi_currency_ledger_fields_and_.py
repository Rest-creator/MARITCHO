"""add multi-currency ledger fields and ecocash payment gateway integration

Revision ID: 22a5feb5dcce
Revises: c776d5d98df3
Create Date: 2026-09-18 12:51:06.617542

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '22a5feb5dcce'
down_revision: Union[str, Sequence[str], None] = 'c776d5d98df3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_currency_enum = sa.Enum('USD', 'ECOCASH', 'ZWG', name='currencyenum')


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ecocash_callback_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('external_reference', sa.String(length=100), nullable=False),
        sa.Column('raw_payload', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_ecocash_callback_logs_external_reference'),
        'ecocash_callback_logs',
        ['external_reference'],
        unique=False,
    )
    # Append-only audit log, same as ledger_entries/record_entries — reuses
    # the existing prevent_mutation() trigger function.
    op.execute("""
        CREATE TRIGGER ecocash_callback_logs_immutable
            BEFORE UPDATE OR DELETE ON ecocash_callback_logs
            FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
    """)
    op.create_table(
        'payment_gateway_configs',
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('merchant_code', sa.String(length=100), nullable=True),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('base_url', sa.String(length=255), nullable=True),
        sa.Column('is_sandbox', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('provider'),
    )

    _currency_enum.create(op.get_bind())

    # jobs/crew_orders.currency are nullable (unset until booking), so a
    # plain add_column is safe regardless of existing row count.
    op.add_column('crew_orders', sa.Column('currency', _currency_enum, nullable=True))
    op.add_column('jobs', sa.Column('currency', _currency_enum, nullable=True))

    # ledger_entries/crew_order_ledger_entries.currency are NOT NULL. Add
    # with a server-side default so existing rows backfill to 'USD' (the
    # only currency that ever existed before this migration), then drop
    # the server default — currency is set explicitly by the app from
    # here on, matching this project's "Python-side default only" pattern
    # used elsewhere (e.g. Standing.grade).
    op.add_column(
        'ledger_entries',
        sa.Column('currency', _currency_enum, nullable=False, server_default='USD'),
    )
    op.add_column('ledger_entries', sa.Column('external_reference', sa.String(length=100)))
    op.alter_column('ledger_entries', 'currency', server_default=None)

    op.add_column(
        'crew_order_ledger_entries',
        sa.Column('currency', _currency_enum, nullable=False, server_default='USD'),
    )
    op.add_column(
        'crew_order_ledger_entries', sa.Column('external_reference', sa.String(length=100))
    )
    op.alter_column('crew_order_ledger_entries', 'currency', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DROP TRIGGER IF EXISTS ecocash_callback_logs_immutable ON ecocash_callback_logs;"
    )

    op.drop_column('ledger_entries', 'external_reference')
    op.drop_column('ledger_entries', 'currency')
    op.drop_column('jobs', 'currency')
    op.drop_column('crew_orders', 'currency')
    op.drop_column('crew_order_ledger_entries', 'external_reference')
    op.drop_column('crew_order_ledger_entries', 'currency')

    _currency_enum.drop(op.get_bind())

    op.drop_table('payment_gateway_configs')
    op.drop_index(
        op.f('ix_ecocash_callback_logs_external_reference'), table_name='ecocash_callback_logs'
    )
    op.drop_table('ecocash_callback_logs')
