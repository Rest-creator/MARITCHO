"""add crew orders and crew order ledger entries

Revision ID: 447e4d827227
Revises: fded931081b3
Create Date: 2026-09-11 14:22:05.409546

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '447e4d827227'
down_revision: Union[str, Sequence[str], None] = 'fded931081b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "CREATE TYPE creworderstatusenum AS ENUM "
        "('REQUESTED', 'MATCHED', 'BOOKED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')"
    )

    op.execute("""
        CREATE TABLE crew_orders (
            id UUID PRIMARY KEY,
            buyer_id UUID NOT NULL REFERENCES persons(id),
            crew_id UUID REFERENCES crews(id),
            status creworderstatusenum NOT NULL,
            trade tradeenum NOT NULL,
            suburb VARCHAR(100) NOT NULL REFERENCES suburbs(name),
            address TEXT NOT NULL,
            workers_needed INTEGER NOT NULL,
            problem_description TEXT,
            quote_amount NUMERIC(10, 2),
            completion_note TEXT,
            created_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT check_workers_needed_positive CHECK (workers_needed > 0)
        )
    """)

    op.execute("""
        CREATE TABLE crew_order_ledger_entries (
            id UUID PRIMARY KEY,
            crew_order_id UUID NOT NULL REFERENCES crew_orders(id),
            amount NUMERIC(10, 2) NOT NULL,
            entry_type ledgerentrytypeenum NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT check_crew_order_amount_positive CHECK (amount > 0)
        )
    """)

    # Immutable, like ledger_entries/record_entries: reuses the same trigger function.
    op.execute("""
        CREATE TRIGGER crew_order_ledger_entries_immutable
            BEFORE UPDATE OR DELETE ON crew_order_ledger_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE crew_order_ledger_entries")
    op.execute("DROP TABLE crew_orders")
    op.execute("DROP TYPE creworderstatusenum")
