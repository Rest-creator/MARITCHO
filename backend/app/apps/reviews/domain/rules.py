"""Review rules (ADR-011). Pure functions, no framework."""

from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.apps.reviews.domain.entities import ReviewSummary
from app.shared_kernel.enums import ReviewDirectionEnum, ReviewTagEnum

REVIEW_WINDOW = timedelta(days=14)
# Fewer reviews than this and the person is shown as "New".
MIN_REVIEWS_FOR_RATING = 3
# Bayesian prior: every score starts as if it had this many reviews at
# this mean, so it moves towards the real average as reviews add up.
PRIOR_MEAN = Decimal("4.0")
PRIOR_WEIGHT = 5
MAX_TAGS = 3

TAGS_BY_DIRECTION: dict[ReviewDirectionEnum, frozenset[ReviewTagEnum]] = {
    ReviewDirectionEnum.BUYER_TO_WORKER: frozenset(
        {
            ReviewTagEnum.CLEAN,
            ReviewTagEnum.ON_TIME,
            ReviewTagEnum.PROFESSIONAL,
            ReviewTagEnum.GOOD_COMMUNICATION,
            ReviewTagEnum.QUALITY_WORK,
            ReviewTagEnum.FAIR_PRICE,
            ReviewTagEnum.RELIABLE,
        }
    ),
    ReviewDirectionEnum.WORKER_TO_BUYER: frozenset(
        {
            ReviewTagEnum.PAID_ON_TIME,
            ReviewTagEnum.JOB_AS_DESCRIBED,
            ReviewTagEnum.RESPECTFUL,
            ReviewTagEnum.SAFE_WORKPLACE,
            ReviewTagEnum.GOOD_COMMUNICATION,
        }
    ),
}


def other_direction(direction: ReviewDirectionEnum) -> ReviewDirectionEnum:
    if direction == ReviewDirectionEnum.BUYER_TO_WORKER:
        return ReviewDirectionEnum.WORKER_TO_BUYER
    return ReviewDirectionEnum.BUYER_TO_WORKER


def window_closes_at(signed_off_at: datetime) -> datetime:
    return signed_off_at + REVIEW_WINDOW


def invalid_tags(direction: ReviewDirectionEnum, tags: Iterable[ReviewTagEnum]) -> list[str]:
    allowed = TAGS_BY_DIRECTION[direction]
    return [tag.value for tag in tags if tag not in allowed]


def _one_decimal(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def weighted_score(total: int, count: int) -> Decimal | None:
    """Bayesian average: (prior_mean * prior_weight + sum) / (prior_weight + n)."""
    if count == 0:
        return None
    return _one_decimal(
        (PRIOR_MEAN * PRIOR_WEIGHT + Decimal(total)) / Decimal(PRIOR_WEIGHT + count)
    )


def summarize(ratings: list[int], tags: Iterable[Iterable[ReviewTagEnum]]) -> ReviewSummary:
    count = len(ratings)
    total = sum(ratings)
    counter: Counter[str] = Counter(tag.value for group in tags for tag in group)
    return ReviewSummary(
        count=count,
        average=_one_decimal(Decimal(total) / Decimal(count)) if count else None,
        score=weighted_score(total, count),
        is_new=count < MIN_REVIEWS_FOR_RATING,
        tag_counts=dict(counter.most_common()),
    )


def first_name(display_name: str | None) -> str:
    """Reviewers appear by first name only."""
    name = (display_name or "").strip()
    return name.split()[0] if name else "A Maritcho user"
