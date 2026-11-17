"""Which workers may see, offer on, or be booked for a job.

The rule is strict by design: a job needs its declared trade, and a worker
qualifies only through a listed skill in that trade (a solar installer can't
take a plumbing job). Similarity search widens exactly one case: a job posted
as GENERAL_MAINTENANCE whose description clearly reads as a specific trade
(e.g. "geyser leaking") is also open to that trade's specialists. "Clearly"
means `infer_best_trade` scores at least SIMILARITY_MATCH_THRESHOLD; vague
descriptions ("odd jobs", "door handle loose") stay general-maintenance only.

Every denial is written to the audit log with who, what and why.
"""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from app.core.telemetry import logger
from app.shared_kernel.embeddings import infer_best_trade
from app.shared_kernel.enums import TradeEnum

# Calibrated on the embedding model: clear trade descriptions score 0.50–0.71,
# vague or misread ones 0–0.43 ("build a wardrobe" -> BUILDING at 0.43).
SIMILARITY_MATCH_THRESHOLD = 0.5

CATCH_ALL_TRADE = TradeEnum.GENERAL_MAINTENANCE

_TRADE_LABELS: dict[TradeEnum, str] = {
    TradeEnum.PLUMBING: "plumbing",
    TradeEnum.ELECTRICAL: "electrical work",
    TradeEnum.SOLAR: "solar installation",
    TradeEnum.WELDING: "welding",
    TradeEnum.BUILDING: "building",
    TradeEnum.APPLIANCE_REPAIR: "appliance repair",
    TradeEnum.GARDENING: "gardening",
    TradeEnum.CARPENTRY: "carpentry",
    TradeEnum.PAINTING: "painting",
    TradeEnum.TILING: "tiling",
    TradeEnum.ROOFING: "roofing",
    TradeEnum.GENERAL_MAINTENANCE: "general maintenance",
}


class MatchBasis(str, Enum):
    TRADE = "TRADE"
    SIMILARITY = "SIMILARITY"


class EligibilityAction(str, Enum):
    VIEW = "VIEW"
    SEARCH = "SEARCH"
    OFFER = "OFFER"
    BOOK = "BOOK"


@dataclass(frozen=True)
class JobEligibility:
    is_eligible: bool
    required_trade: TradeEnum
    matched_by: MatchBasis | None
    similarity_score: float | None
    reason: str


def trade_label(trade: TradeEnum) -> str:
    return _TRADE_LABELS.get(trade, trade.value.replace("_", " ").lower())


def inferred_specialist_trade(
    job_trade: TradeEnum, problem_description: str
) -> tuple[TradeEnum | None, float]:
    """For a catch-all job, the specific trade its description clearly
    describes (score >= threshold); otherwise (None, score)."""
    if job_trade != CATCH_ALL_TRADE or not problem_description.strip():
        return None, 0.0
    trade, score = infer_best_trade(problem_description)
    if trade is None or trade == CATCH_ALL_TRADE or score < SIMILARITY_MATCH_THRESHOLD:
        return None, score
    return trade, score


def evaluate_job_eligibility(
    *, job_trade: TradeEnum, problem_description: str, worker_skills: Iterable[TradeEnum]
) -> JobEligibility:
    skills: set[TradeEnum] = set(worker_skills)
    if job_trade in skills:
        return JobEligibility(
            is_eligible=True,
            required_trade=job_trade,
            matched_by=MatchBasis.TRADE,
            similarity_score=None,
            reason=f"Matches your {trade_label(job_trade)} skill.",
        )

    specialist, score = inferred_specialist_trade(job_trade, problem_description)
    if specialist is not None and specialist in skills:
        return JobEligibility(
            is_eligible=True,
            required_trade=job_trade,
            matched_by=MatchBasis.SIMILARITY,
            similarity_score=round(score, 4),
            reason=f"This general job reads as {trade_label(specialist)}, one of your skills.",
        )

    if skills:
        yours = ", ".join(sorted(trade_label(skill) for skill in skills))
        reason = (
            f"This job needs {trade_label(job_trade)}, which isn't one of your skills "
            f"({yours}). Add it to your skills if it's work you do."
        )
    else:
        reason = (
            f"This job needs {trade_label(job_trade)}. Add your skills first so we can "
            "show you jobs that match."
        )
    return JobEligibility(
        is_eligible=False,
        required_trade=job_trade,
        matched_by=None,
        similarity_score=round(score, 4) if score else None,
        reason=reason,
    )


def trades_worth_scanning(worker_skills: Iterable[TradeEnum]) -> list[TradeEnum]:
    """Job trades that can hold jobs this worker qualifies for: their own
    trades, plus catch-all jobs (filtered afterwards by similarity)."""
    trades: set[TradeEnum] = set(worker_skills)
    if trades:
        trades.add(CATCH_ALL_TRADE)
    return sorted(trades, key=lambda trade: trade.value)


def audit_eligibility_denial(
    *,
    action: EligibilityAction,
    worker_id: uuid.UUID,
    job_id: uuid.UUID,
    eligibility: JobEligibility,
    worker_skills: Iterable[TradeEnum],
) -> None:
    """Structured audit record for a blocked view, offer or booking."""
    logger.warning(
        f"job eligibility denied action={action.value} worker_id={worker_id} job_id={job_id}",
        extra={
            "audit": {
                "event": "job_eligibility_denied",
                "action": action.value,
                "worker_id": str(worker_id),
                "job_id": str(job_id),
                "required_trade": eligibility.required_trade.value,
                "worker_skills": sorted(skill.value for skill in worker_skills),
                "similarity_score": eligibility.similarity_score,
                "reason": eligibility.reason,
            }
        },
    )
