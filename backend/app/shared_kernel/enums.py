"""Enums genuinely shared by 2+ apps (ADR-007).

Single-app enums (JobStatusEnum, DisputeStatusEnum, CrewOrderStatusEnum)
live in their owning app's `domain/entities.py` instead — see the "Shared
enum placement" table in the migration plan for why each one is here.
"""

import enum


class RoleEnum(str, enum.Enum):
    BUYER = "BUYER"
    WORKER = "WORKER"
    OPS = "OPS"
    AGGREGATOR = "AGGREGATOR"


class TradeEnum(str, enum.Enum):
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    SOLAR = "SOLAR"
    WELDING = "WELDING"
    BUILDING = "BUILDING"
    APPLIANCE_REPAIR = "APPLIANCE_REPAIR"
    GARDENING = "GARDENING"
    CARPENTRY = "CARPENTRY"
    PAINTING = "PAINTING"
    TILING = "TILING"
    ROOFING = "ROOFING"
    GENERAL_MAINTENANCE = "GENERAL_MAINTENANCE"


class NeededByEnum(str, enum.Enum):
    TODAY = "TODAY"
    THIS_WEEK = "THIS_WEEK"
    FLEXIBLE = "FLEXIBLE"


class PricingModeEnum(str, enum.Enum):
    FIXED = "FIXED"
    NEGOTIABLE = "NEGOTIABLE"
    AFTER_VISIT = "AFTER_VISIT"


class ReviewTagEnum(str, enum.Enum):
    CLEAN = "CLEAN"
    ON_TIME = "ON_TIME"
    PROFESSIONAL = "PROFESSIONAL"
    GOOD_COMMUNICATION = "GOOD_COMMUNICATION"
    QUALITY_WORK = "QUALITY_WORK"
    FAIR_PRICE = "FAIR_PRICE"
    RELIABLE = "RELIABLE"
    # Worker -> client tags (two-way reviews, ADR-011).
    PAID_ON_TIME = "PAID_ON_TIME"
    JOB_AS_DESCRIBED = "JOB_AS_DESCRIBED"
    RESPECTFUL = "RESPECTFUL"
    SAFE_WORKPLACE = "SAFE_WORKPLACE"


class ReviewDirectionEnum(str, enum.Enum):
    """Who reviewed whom on a job (ADR-011)."""

    BUYER_TO_WORKER = "BUYER_TO_WORKER"
    WORKER_TO_BUYER = "WORKER_TO_BUYER"


class VerificationStatusEnum(str, enum.Enum):
    """Review state of a vetting document (ADR-010). Unsubmitted = no row value."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class GradeEnum(str, enum.Enum):
    REGISTERED = "REGISTERED"
    IDENTIFIED = "IDENTIFIED"
    APPRENTICE = "APPRENTICE"
    JOURNEYMAN = "JOURNEYMAN"
    EXPERT = "EXPERT"


class CurrencyEnum(str, enum.Enum):
    """ADR-002: the settlement rail a job's payments run on."""

    USD = "USD"
    ECOCASH = "ECOCASH"
    ZWG = "ZWG"


class LedgerEntryTypeEnum(str, enum.Enum):
    """Same Postgres enum type backs both jobs' and crews' ledger tables."""

    DEPOSIT_HELD = "DEPOSIT_HELD"
    BALANCE_COMMITTED = "BALANCE_COMMITTED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"


class DistanceBandEnum(str, enum.Enum):
    SAME_SUBURB = "SAME_SUBURB"
    NEARBY = "NEARBY"
    MODERATE = "MODERATE"
    FAR = "FAR"
