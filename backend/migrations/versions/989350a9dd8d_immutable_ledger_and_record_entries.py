"""immutable ledger and record entries

Revision ID: 989350a9dd8d
Revises: a725b45e4046
Create Date: 2026-09-11 13:18:11.348930

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '989350a9dd8d'
down_revision: Union[str, Sequence[str], None] = 'a725b45e4046'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION '% is immutable: % not permitted on table %',
                TG_TABLE_NAME, TG_OP, TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;
    """)

    for table in ("ledger_entries", "record_entries"):
        op.execute(f"""
            CREATE TRIGGER {table}_immutable
            BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
        """)


def downgrade() -> None:
    """Downgrade schema."""
    for table in ("ledger_entries", "record_entries"):
        op.execute(f"DROP TRIGGER IF EXISTS {table}_immutable ON {table};")

    op.execute("DROP FUNCTION IF EXISTS prevent_mutation();")
