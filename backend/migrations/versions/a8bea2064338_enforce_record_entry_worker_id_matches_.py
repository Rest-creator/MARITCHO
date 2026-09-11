"""enforce record entry worker id matches job worker id

Revision ID: a8bea2064338
Revises: 6d1158370df3
Create Date: 2026-09-11 18:15:27.842710

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a8bea2064338'
down_revision: Union[str, Sequence[str], None] = '6d1158370df3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    RecordEntry.worker_id duplicates Job.worker_id (reachable via job_id)
    for read convenience (worker-scoped record queries without a join).
    Nothing previously enforced the two stay in sync — this trigger closes
    that gap. Only checked BEFORE INSERT: record_entries is already
    immutable (see prevent_mutation()), so there is no UPDATE path to
    guard against.
    """
    op.execute("""
        CREATE OR REPLACE FUNCTION check_record_entry_worker_matches_job()
        RETURNS TRIGGER AS $$
        DECLARE
            job_worker_id UUID;
        BEGIN
            SELECT worker_id INTO job_worker_id FROM jobs WHERE id = NEW.job_id;
            IF job_worker_id IS NULL OR job_worker_id != NEW.worker_id THEN
                RAISE EXCEPTION
                    'record_entries.worker_id (%) does not match jobs.worker_id (%) for job_id %',
                    NEW.worker_id, job_worker_id, NEW.job_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER record_entries_worker_matches_job
        BEFORE INSERT ON record_entries
        FOR EACH ROW EXECUTE FUNCTION check_record_entry_worker_matches_job();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DROP TRIGGER IF EXISTS record_entries_worker_matches_job ON record_entries;"
    )
    op.execute("DROP FUNCTION IF EXISTS check_record_entry_worker_matches_job();")
