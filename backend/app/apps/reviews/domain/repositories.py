import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from app.apps.reviews.domain.entities import (
    JobReviewContext,
    PublicReview,
    ReportedReview,
    Review,
)
from app.shared_kernel.enums import ReviewDirectionEnum, ReviewTagEnum


class ReviewRepository(ABC):
    @abstractmethod
    async def get(self, review_id: uuid.UUID) -> Review | None: ...

    @abstractmethod
    async def for_job(self, job_id: uuid.UUID) -> Sequence[Review]:
        """Both directions' reviews for one job (0, 1 or 2)."""

    @abstractmethod
    async def add(self, review: Review) -> None:
        """Stages only. A second review in the same direction surfaces as
        IntegrityConflictError on commit."""

    @abstractmethod
    async def publish(self, review_ids: Sequence[uuid.UUID], published_at: datetime) -> None:
        """Stages only."""

    @abstractmethod
    async def set_reply(self, review_id: uuid.UUID, reply: str, replied_at: datetime) -> None:
        """Stages only."""

    @abstractmethod
    async def set_report(
        self, review_id: uuid.UUID, *, reported_by: uuid.UUID, reason: str, reported_at: datetime
    ) -> None:
        """Stages only."""

    @abstractmethod
    async def set_moderation(
        self,
        review_id: uuid.UUID,
        *,
        moderated_by: uuid.UUID,
        moderated_at: datetime,
        hide: bool,
    ) -> None:
        """Stages only. Clears the report either way."""

    @abstractmethod
    async def visible_about(
        self,
        subject_id: uuid.UUID,
        direction: ReviewDirectionEnum,
        now: datetime,
        *,
        limit: int,
        offset: int,
    ) -> Sequence[PublicReview]:
        """Visible reviews about a person, newest first."""

    @abstractmethod
    async def visible_ratings(
        self, subject_id: uuid.UUID, direction: ReviewDirectionEnum, now: datetime
    ) -> Sequence[tuple[int, list[ReviewTagEnum]]]:
        """Every visible (rating, tags) about a person, for the summary."""

    @abstractmethod
    async def reported(self, *, limit: int, offset: int) -> Sequence[ReportedReview]:
        """Reviews reported and not yet moderated, oldest report first."""


class JobReviewContextPort(ABC):
    @abstractmethod
    async def get(self, job_id: uuid.UUID) -> JobReviewContext | None: ...
