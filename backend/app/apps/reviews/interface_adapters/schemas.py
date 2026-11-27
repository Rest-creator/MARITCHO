import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared_kernel.enums import ReviewDirectionEnum, ReviewTagEnum, TradeEnum
from app.shared_kernel.text import strip_tags


def _clean(value: str | None) -> str | None:
    return strip_tags(value) if value is not None else value


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    tags: list[ReviewTagEnum] = Field(default_factory=list, max_length=3)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, value: str | None) -> str | None:
        return _clean(value)


class ReviewOut(BaseModel):
    """A review as its author, or the other party once it is visible, sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    direction: ReviewDirectionEnum
    rating: int
    tags: list[ReviewTagEnum]
    comment: str | None
    created_at: datetime
    published_at: datetime | None
    visible_after: datetime
    had_dispute: bool
    reply: str | None
    replied_at: datetime | None


class JobReviewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    my_direction: ReviewDirectionEnum
    window_closes_at: datetime | None
    can_review: bool
    mine: ReviewOut | None
    theirs: ReviewOut | None
    is_theirs_waiting: bool


class PublicReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ReviewSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    count: int
    average: Decimal | None
    score: Decimal | None
    is_new: bool
    tag_counts: dict[str, int]


class ReviewPageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: ReviewSummaryOut
    reviews: list[PublicReviewOut]


class ReplyCreate(BaseModel):
    reply: str = Field(min_length=1, max_length=500)

    @field_validator("reply")
    @classmethod
    def sanitize_reply(cls, value: str) -> str:
        return strip_tags(value)


class ReportCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=255)

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, value: str) -> str:
        return strip_tags(value)


class ReportedReviewOut(BaseModel):
    review_id: uuid.UUID
    job_id: uuid.UUID
    direction: ReviewDirectionEnum
    rating: int
    comment: str | None
    reply: str | None
    report_reason: str | None
    reported_at: datetime | None
    subject_name: str | None
    author_name: str | None


class ModerationCreate(BaseModel):
    decision: Literal["KEEP", "REMOVE"]
