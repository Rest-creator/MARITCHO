import asyncio
import itertools
import os
from decimal import Decimal
from pathlib import Path

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/maricho_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import asyncpg
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.auth import create_access_token
from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import GradeEnum, Person, RoleEnum, ServiceArea, Skill, Standing, TradeEnum

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Derived from DATABASE_URL (not hardcoded) so this works against whatever
# host/port/credentials the test database actually uses — e.g. CI, where
# Postgres isn't necessarily on localhost:5432.
_test_db_url = make_url(os.environ["DATABASE_URL"])
TEST_DB_NAME = _test_db_url.database
ADMIN_DSN = _test_db_url.set(drivername="postgresql", database="postgres").render_as_string(
    hide_password=False
)

APP_TABLES = [
    "record_entries",
    "ledger_entries",
    "disputes",
    "crew_order_ledger_entries",
    "crew_orders",
    "crew_members",
    "crews",
    "standings",
    "jobs",
    "service_areas",
    "skills",
    "persons",
]


async def _ensure_test_database() -> None:
    conn = await asyncpg.connect(dsn=ADMIN_DSN)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


def _run_migrations() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(config, "head")


@pytest.fixture(scope="session", autouse=True)
def _test_database() -> None:
    asyncio.run(_ensure_test_database())
    _run_migrations()


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(APP_TABLES)} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _make_person(session, role: RoleEnum, phone: str) -> Person:
    person = Person(phone=phone, role=role)
    session.add(person)
    await session.commit()
    await session.refresh(person)
    return person


@pytest_asyncio.fixture
async def buyer(db_session) -> Person:
    return await _make_person(db_session, RoleEnum.BUYER, "+263771000001")


@pytest_asyncio.fixture
async def other_buyer(db_session) -> Person:
    return await _make_person(db_session, RoleEnum.BUYER, "+263771000002")


@pytest_asyncio.fixture
async def worker(db_session) -> Person:
    return await _make_person(db_session, RoleEnum.WORKER, "+263771000003")


@pytest_asyncio.fixture
async def ops_user(db_session) -> Person:
    return await _make_person(db_session, RoleEnum.OPS, "+263771000004")


@pytest_asyncio.fixture
async def aggregator(db_session) -> Person:
    return await _make_person(db_session, RoleEnum.AGGREGATOR, "+263771000005")


@pytest_asyncio.fixture
async def other_aggregator(db_session) -> Person:
    return await _make_person(db_session, RoleEnum.AGGREGATOR, "+263771000006")


def auth_headers(person: Person) -> dict[str, str]:
    token = create_access_token(data={"sub": person.phone})
    return {"Authorization": f"Bearer {token}"}


_worker_phone_seq = itertools.count(1)


@pytest_asyncio.fixture
def worker_factory(db_session):
    async def _create(
        trade: TradeEnum,
        suburb: str,
        *,
        grade: GradeEnum = GradeEnum.REGISTERED,
        on_time_rate: Decimal = Decimal("100.00"),
        dispute_rate: Decimal = Decimal("0.00"),
        fill_rate: Decimal = Decimal("0.00"),
        jobs_completed: int = 0,
        travel_means: str = "WALKING",
        skip_standing: bool = False,
    ) -> Person:
        phone = f"+2637720{next(_worker_phone_seq):05d}"
        worker_person = Person(phone=phone, role=RoleEnum.WORKER)
        db_session.add(worker_person)
        await db_session.flush()

        db_session.add(Skill(worker_id=worker_person.id, trade=trade))
        db_session.add(
            ServiceArea(worker_id=worker_person.id, suburb=suburb, travel_means=travel_means)
        )
        if not skip_standing:
            db_session.add(
                Standing(
                    worker_id=worker_person.id,
                    grade=grade,
                    on_time_rate=on_time_rate,
                    dispute_rate=dispute_rate,
                    fill_rate=fill_rate,
                    jobs_completed=jobs_completed,
                )
            )
        await db_session.commit()
        await db_session.refresh(worker_person)
        return worker_person

    return _create
