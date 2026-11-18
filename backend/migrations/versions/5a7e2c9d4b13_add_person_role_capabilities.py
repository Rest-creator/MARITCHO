"""add persons.roles: what an account may do, separate from its active mode

One account can both hire (BUYER) and find work (WORKER). `persons.role`
stays the *active mode* (navigation, home screen, which side a shared
screen acts as); `persons.roles` is the set of capabilities the account has
unlocked. Backfilled from the current role, so existing accounts behave
exactly as before.

Revision ID: 5a7e2c9d4b13
Revises: 1c880d901383
Create Date: 2026-11-17 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5a7e2c9d4b13"
down_revision: str | Sequence[str] | None = "1c880d901383"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column(
            "roles",
            postgresql.ARRAY(sa.String(length=16)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
    )
    op.execute("UPDATE persons SET roles = ARRAY[role::text]::varchar[]")
    op.create_index("ix_persons_roles", "persons", ["roles"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_persons_roles", table_name="persons")
    op.drop_column("persons", "roles")
