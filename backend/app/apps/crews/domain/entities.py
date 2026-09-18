import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.shared_kernel.enums import CurrencyEnum, DistanceBandEnum, LedgerEntryTypeEnum, TradeEnum


class CrewOrderStatusEnum(str, enum.Enum):
    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    BOOKED = "BOOKED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# A crew already tied to one of these order states can't take on a new one.
CREW_BUSY_STATUSES = (CrewOrderStatusEnum.BOOKED, CrewOrderStatusEnum.IN_PROGRESS)


@dataclass
class Crew:
    id: uuid.UUID
    lead_id: uuid.UUID
    name: str | None = None


@dataclass
class CrewMember:
    crew_id: uuid.UUID
    worker_id: uuid.UUID


@dataclass
class CrewView:
    """Crew plus its current roster — the shape every crews/me endpoint
    returns, computed from Crew + CrewMember rows, never stored."""

    id: uuid.UUID
    lead_id: uuid.UUID
    name: str | None
    member_ids: list[uuid.UUID]


@dataclass
class CrewOrder:
    id: uuid.UUID
    buyer_id: uuid.UUID
    crew_id: uuid.UUID | None
    status: CrewOrderStatusEnum
    trade: TradeEnum
    suburb: str
    address: str
    landmark_narrative: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    workers_needed: int
    problem_description: str | None
    currency: CurrencyEnum | None
    labor_amount: Decimal | None
    materials_amount: Decimal | None
    quote_amount: Decimal | None
    completion_note: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class CrewOrderLedgerEntry:
    id: uuid.UUID
    crew_order_id: uuid.UUID
    amount: Decimal
    entry_type: LedgerEntryTypeEnum
    currency: CurrencyEnum
    external_reference: str | None = None
    created_at: datetime | None = None


@dataclass
class CrewMatchCandidate:
    crew_id: uuid.UUID
    crew_name: str | None
    lead_id: uuid.UUID
    qualifying_members: int
    total_members: int
    distance_band: DistanceBandEnum
    distance_km: float
    reason: str
