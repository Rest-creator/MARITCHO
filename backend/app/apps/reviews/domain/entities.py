"""Two-way ratings and reviews after sign-off (ADR-011). Framework-free."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.shared_kernel.enums import ReviewDirectionEnum, ReviewTagEnum, TradeEnum


@dataclass
class Review:
    id: uuid.UUID
    job_id: uuid.UUID
    direction: ReviewDirectionEnum
    author_id: uuid.UUID
    subject_id: uuid.UUID
    rating: int
    tags: list[ReviewTagEnum]
    comment: str | None
    created_at: datetime
    # Hidden from everyone but its author until the other side reviews too,
    # or until `visible_after` (the end of the review window).
    visible_after: datetime
    published_at: datetime | None = None
    had_dispute: bool = False
    reply: str | None = None
    replied_at: datetime | None = None
    reported_at: datetime | None = None
    report_reason: str | None = None
    hidden_at: datetime | None = None

    def is_visible(self, now: datetime) -> bool:
        if self.hidden_at is not None:
            return False
        return self.published_at is not None or self.visible_after <= now


@dataclass
class JobReviewContext:
    """What the review rules need to know about a job."""

    job_id: uuid.UUID
    buyer_id: uuid.UUID
    worker_id: uuid.UUID | None
    is_completed: bool
    signed_off_at: datetime | None
    had_dispute: bool
    trade: TradeEnum


@dataclass
class PublicReview:
    """A visible review as anyone signed in may see it: the reviewer is
    shown by first name and suburb only."""

    id: uuid.UUID
    direction: ReviewDirectionEnum
    rating: int
    tags: list[ReviewTagEnum]
    comment: str | None
    reviewer_name: str
    reviewer_suburb: str | None
    trade: TradeEnum
    created_at: datetime
    had_dispute: bool
    reply: str | None
    replied_at: datetime | None


@dataclass
class ReviewSummary:
    count: int
    average: Decimal | None
    # Weighted towards a neutral prior so a single 5-star review can't
    # outrank a long, steady record (see rules.weighted_score).
    score: Decimal | None
    is_new: bool
    tag_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class ReviewPage:
    summary: ReviewSummary
    reviews: list[PublicReview]


@dataclass
class JobReviews:
    """Both sides of one job's reviews, as one party sees them."""

    job_id: uuid.UUID
    my_direction: ReviewDirectionEnum
    window_closes_at: datetime | None
    can_review: bool
    mine: Review | None
    theirs: Review | None
    # The other side has reviewed, but it isn't shown yet (double-blind).
    is_theirs_waiting: bool


@dataclass
class ReportedReview:
    review: Review
    subject_name: str | None
    author_name: str | None
