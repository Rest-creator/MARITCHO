"""merge password_hash and pgvector heads

Revision ID: 1c880d901383
Revises: d3f6a1b8c9e2, d8f3a1c2e5b7
Create Date: 2026-11-16 20:53:46.852613

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '1c880d901383'
down_revision: Union[str, Sequence[str], None] = ('d3f6a1b8c9e2', 'd8f3a1c2e5b7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
