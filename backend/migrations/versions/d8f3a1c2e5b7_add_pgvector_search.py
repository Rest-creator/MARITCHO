"""add pgvector extension, problem_embedding column, and HNSW cosine index to jobs."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from app.shared_kernel.embeddings import EMBEDDING_DIM, embed_text

revision: str = "d8f3a1c2e5b7"
down_revision: Union[str, Sequence[str], None] = "c1e7b2f4a901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.add_column(
        "jobs",
        sa.Column("problem_embedding", Vector(EMBEDDING_DIM), nullable=True),
    )

    # Backfill embeddings for any existing jobs
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, trade::text, suburb, problem_description FROM jobs")
    ).fetchall()
    for row in rows:
        vec = embed_text(row.problem_description, trade=row.trade, suburb=row.suburb)
        vec_literal = "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
        bind.execute(
            sa.text("UPDATE jobs SET problem_embedding = CAST(:vec AS vector) WHERE id = :id"),
            {"vec": vec_literal, "id": row.id},
        )

    op.create_index(
        "ix_jobs_problem_embedding_hnsw",
        "jobs",
        ["problem_embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"problem_embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_problem_embedding_hnsw", table_name="jobs")
    op.drop_column("jobs", "problem_embedding")
