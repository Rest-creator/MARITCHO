import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CrewOrderLedgerEntry, LedgerEntry, LedgerEntryTypeEnum


async def sum_ledger_entries(
    db: AsyncSession, job_id: uuid.UUID, entry_type: LedgerEntryTypeEnum
) -> Decimal:
    """Total amount already recorded for a job under one ledger entry type.

    ledger_entries is insert-only (DB trigger blocks UPDATE/DELETE), so this
    sum is always the authoritative running total for that type.
    """
    result = await db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.job_id == job_id, LedgerEntry.entry_type == entry_type
        )
    )
    return result.scalar_one()


async def sum_crew_order_ledger_entries(
    db: AsyncSession, crew_order_id: uuid.UUID, entry_type: LedgerEntryTypeEnum
) -> Decimal:
    """Same as sum_ledger_entries, for the crew-order ledger."""
    result = await db.execute(
        select(func.coalesce(func.sum(CrewOrderLedgerEntry.amount), 0)).where(
            CrewOrderLedgerEntry.crew_order_id == crew_order_id,
            CrewOrderLedgerEntry.entry_type == entry_type,
        )
    )
    return result.scalar_one()
