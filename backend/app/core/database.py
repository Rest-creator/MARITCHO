import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Default to a local postgres instance for development
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/maricho"
)

# pool_size + max_overflow = 15 max connections per instance. Sized so that
# several horizontally-scaled API replicas stay well under Postgres's default
# max_connections=100 (15/instance leaves room for 6 replicas at 90, plus
# headroom for migrations/psql/monitoring) — see engineering_standards.md §3
# for the connection-budget formula behind this number.
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        yield session
