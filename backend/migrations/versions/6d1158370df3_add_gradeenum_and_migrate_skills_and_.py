"""add gradeenum and migrate skills and standings grade columns

Revision ID: 6d1158370df3
Revises: 4fa80902185b
Create Date: 2026-09-11 18:07:51.717998

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6d1158370df3'
down_revision: Union[str, Sequence[str], None] = '4fa80902185b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "CREATE TYPE gradeenum AS ENUM "
        "('REGISTERED', 'IDENTIFIED', 'APPRENTICE', 'JOURNEYMAN', 'EXPERT')"
    )

    op.execute(
        "ALTER TABLE skills ALTER COLUMN grade TYPE gradeenum USING grade::gradeenum"
    )
    op.execute(
        "ALTER TABLE standings ALTER COLUMN grade TYPE gradeenum USING grade::gradeenum"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE standings ALTER COLUMN grade TYPE VARCHAR(50) USING grade::text")
    op.execute("ALTER TABLE skills ALTER COLUMN grade TYPE VARCHAR(50) USING grade::text")
    op.execute("DROP TYPE gradeenum")
