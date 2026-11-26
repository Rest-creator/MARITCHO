"""Use cases for two-way reviews (ADR-011).

- Both sides of a completed job may review the other, within 14 days of
  sign-off.
- A review stays hidden (double-blind) until the other side has reviewed
  too, or the window closes, so neither can retaliate after reading the
  other's review.
- The person reviewed may reply once and may report a review. A report
  does not hide it; only OPS can, so nobody can bury fair criticism.
"""

import uuid
from collections.abc import Sequence

from app.apps.reviews.domain.entities import (
    JobReviewContext,
    JobReviews,
    ReportedReview,
    Review,
    ReviewPage,
)
from app.apps.reviews.domain.repositories import JobReviewContextPort, ReviewRepository
from app.apps.reviews.domain.rules import (
    MAX_TAGS,
    invalid_tags,
    other_direction,
    summarize,
    window_closes_at,
)
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    IntegrityConflictError,
    NotFoundError,
    ValidationConflictError,
)
from app.shared_kernel.clock import utcnow
from app.shared_kernel.enums import ReviewDirectionEnum, ReviewTagEnum
from app.shared_kernel.unit_of_work import UnitOfWork


def _direction_for(context: JobReviewContext, person_id: uuid.UUID) -> ReviewDirectionEnum:
    if person_id == context.buyer_id:
        return ReviewDirectionEnum.BUYER_TO_WORKER
    if context.worker_id is not None and person_id == context.worker_id:
        return ReviewDirectionEnum.WORKER_TO_BUYER
    # Not a party: indistinguishable from a job that doesn't exist.
    raise NotFoundError("Job not found")


async def _party_context(
    jobs: JobReviewContextPort, job_id: uuid.UUID, person_id: uuid.UUID
) -> tuple[JobReviewContext, ReviewDirectionEnum]:
    context = await jobs.get(job_id)
    if context is None:
        raise NotFoundError("Job not found")
    return context, _direction_for(context, person_id)


class SubmitReviewUseCase:
    def __init__(
        self, reviews: ReviewRepository, jobs: JobReviewContextPort, uow: UnitOfWork
    ) -> None:
        self._reviews = reviews
        self._jobs = jobs
        self._uow = uow

    async def execute(
        self,
        *,
        job_id: uuid.UUID,
        author_id: uuid.UUID,
        rating: int,
        tags: list[ReviewTagEnum],
        comment: str | None,
    ) -> Review:
        context, direction = await _party_context(self._jobs, job_id, author_id)
        if not context.is_completed or context.worker_id is None:
            raise ConflictError("Job must be completed before review")
        now = utcnow()
        signed_off_at = context.signed_off_at or now
        closes_at = window_closes_at(signed_off_at)
        if now > closes_at:
            raise ConflictError("The 14 days to review this job have passed")
        if not 1 <= rating <= 5:
            raise ValidationConflictError("Rating must be between 1 and 5")
        unique_tags = list(dict.fromkeys(tags))
        if len(unique_tags) > MAX_TAGS:
            raise ValidationConflictError(f"Choose up to {MAX_TAGS} tags")
        wrong = invalid_tags(direction, unique_tags)
        if wrong:
            raise ValidationConflictError(f"These tags don't fit this review: {', '.join(wrong)}")

        existing = await self._reviews.for_job(job_id)
        if any(review.direction == direction for review in existing):
            raise ConflictError("Job already reviewed")
        counterpart = next(
            (review for review in existing if review.direction == other_direction(direction)),
            None,
        )
        subject_id = (
            context.worker_id
            if direction == ReviewDirectionEnum.BUYER_TO_WORKER
            else (context.buyer_id)
        )
        review = Review(
            id=uuid.uuid4(),
            job_id=job_id,
            direction=direction,
            author_id=author_id,
            subject_id=subject_id,
            rating=rating,
            tags=unique_tags,
            comment=(comment or "").strip() or None,
            created_at=now,
            visible_after=closes_at,
            # Both sides are in: publish both together.
            published_at=now if counterpart is not None else None,
            had_dispute=context.had_dispute,
        )
        await self._reviews.add(review)
        if counterpart is not None and counterpart.published_at is None:
            await self._reviews.publish([counterpart.id], now)
        try:
            await self._uow.commit()
        except IntegrityConflictError as error:
            raise ConflictError("Job already reviewed") from error
        return review


class GetJobReviewsUseCase:
    def __init__(self, reviews: ReviewRepository, jobs: JobReviewContextPort) -> None:
        self._reviews = reviews
        self._jobs = jobs

    async def execute(self, *, job_id: uuid.UUID, person_id: uuid.UUID) -> JobReviews:
        context, direction = await _party_context(self._jobs, job_id, person_id)
        now = utcnow()
        closes_at = window_closes_at(context.signed_off_at or now) if context.is_completed else None
        existing = await self._reviews.for_job(job_id)
        mine = next((review for review in existing if review.direction == direction), None)
        theirs = next((review for review in existing if review.direction != direction), None)
        is_theirs_visible = theirs is not None and theirs.is_visible(now)
        return JobReviews(
            job_id=job_id,
            my_direction=direction,
            window_closes_at=closes_at,
            can_review=(
                context.is_completed and mine is None and closes_at is not None and now <= closes_at
            ),
            mine=mine,
            theirs=theirs if is_theirs_visible else None,
            is_theirs_waiting=theirs is not None and not is_theirs_visible,
        )


class ListReviewsAboutUseCase:
    """A worker's reviews from clients, or a client's reviews from workers."""

    def __init__(self, reviews: ReviewRepository) -> None:
        self._reviews = reviews

    async def execute(
        self,
        *,
        subject_id: uuid.UUID,
        direction: ReviewDirectionEnum,
        limit: int,
        offset: int,
    ) -> ReviewPage:
        now = utcnow()
        ratings = await self._reviews.visible_ratings(subject_id, direction, now)
        page = await self._reviews.visible_about(
            subject_id, direction, now, limit=limit, offset=offset
        )
        return ReviewPage(
            summary=summarize([rating for rating, _ in ratings], [tags for _, tags in ratings]),
            reviews=list(page),
        )


class GetClientReviewsForJobUseCase:
    """Lets a worker judge a client before offering, without revealing who
    the client is (OpenJobOut hides buyer_id until booking)."""

    def __init__(self, jobs: JobReviewContextPort, list_reviews: ListReviewsAboutUseCase) -> None:
        self._jobs = jobs
        self._list = list_reviews

    async def execute(self, *, job_id: uuid.UUID, limit: int) -> ReviewPage:
        context = await self._jobs.get(job_id)
        if context is None:
            raise NotFoundError("Job not found")
        return await self._list.execute(
            subject_id=context.buyer_id,
            direction=ReviewDirectionEnum.WORKER_TO_BUYER,
            limit=limit,
            offset=0,
        )


async def _visible_review_about(
    reviews: ReviewRepository, review_id: uuid.UUID, person_id: uuid.UUID
) -> Review:
    review = await reviews.get(review_id)
    if review is None or not review.is_visible(utcnow()):
        raise NotFoundError("Review not found")
    if review.subject_id != person_id:
        raise ForbiddenError("Only the person reviewed can do this")
    return review


class ReplyToReviewUseCase:
    def __init__(self, reviews: ReviewRepository, uow: UnitOfWork) -> None:
        self._reviews = reviews
        self._uow = uow

    async def execute(self, *, review_id: uuid.UUID, person_id: uuid.UUID, reply: str) -> Review:
        review = await _visible_review_about(self._reviews, review_id, person_id)
        if review.reply is not None:
            raise ConflictError("You have already replied to this review")
        text = reply.strip()
        if not text:
            raise ValidationConflictError("Write a reply")
        now = utcnow()
        await self._reviews.set_reply(review_id, text, now)
        await self._uow.commit()
        review.reply, review.replied_at = text, now
        return review


class ReportReviewUseCase:
    def __init__(self, reviews: ReviewRepository, uow: UnitOfWork) -> None:
        self._reviews = reviews
        self._uow = uow

    async def execute(self, *, review_id: uuid.UUID, person_id: uuid.UUID, reason: str) -> Review:
        review = await _visible_review_about(self._reviews, review_id, person_id)
        text = reason.strip()
        if not text:
            raise ValidationConflictError("Tell us what is wrong with this review")
        if review.reported_at is not None:
            return review  # Already waiting for OPS; reporting twice changes nothing.
        now = utcnow()
        await self._reviews.set_report(
            review_id, reported_by=person_id, reason=text, reported_at=now
        )
        await self._uow.commit()
        review.reported_at, review.report_reason = now, text
        return review


class ListReportedReviewsUseCase:
    def __init__(self, reviews: ReviewRepository) -> None:
        self._reviews = reviews

    async def execute(self, *, limit: int, offset: int) -> Sequence[ReportedReview]:
        return await self._reviews.reported(limit=limit, offset=offset)


class ModerateReviewUseCase:
    """OPS keeps a reported review, or removes it (abuse, threats, personal
    details, or not about the job). Removal hides it and drops it from the
    rating."""

    def __init__(self, reviews: ReviewRepository, uow: UnitOfWork) -> None:
        self._reviews = reviews
        self._uow = uow

    async def execute(
        self, *, review_id: uuid.UUID, moderator_id: uuid.UUID, remove: bool
    ) -> Review:
        review = await self._reviews.get(review_id)
        if review is None:
            raise NotFoundError("Review not found")
        now = utcnow()
        await self._reviews.set_moderation(
            review_id, moderated_by=moderator_id, moderated_at=now, hide=remove
        )
        await self._uow.commit()
        review.reported_at = None
        review.report_reason = None
        if remove:
            review.hidden_at = now
        return review
