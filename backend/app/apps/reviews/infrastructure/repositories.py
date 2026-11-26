import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.apps.accounts.infrastructure.models import PersonModel
from app.apps.jobs.domain.entities import JobStatusEnum
from app.apps.jobs.infrastructure.models import DisputeModel, JobModel, RecordEntryModel
from app.apps.reviews.domain.entities import (
    JobReviewContext,
    PublicReview,
    ReportedReview,
    Review,
)
from app.apps.reviews.domain.repositories import JobReviewContextPort, ReviewRepository
from app.apps.reviews.domain.rules import first_name
from app.apps.reviews.infrastructure.models import ReviewModel, visible_review_clause
from app.shared_kernel.enums import ReviewDirectionEnum, ReviewTagEnum


def _to_entity(model: ReviewModel) -> Review:
    return Review(
        id=model.id,
        job_id=model.job_id,
        direction=model.direction,
        author_id=model.author_id,
        subject_id=model.subject_id,
        rating=model.rating,
        tags=list(model.tags or []),
        comment=model.comment,
        created_at=model.created_at,
        visible_after=model.visible_after,
        published_at=model.published_at,
        had_dispute=model.had_dispute,
        reply=model.reply,
        replied_at=model.replied_at,
        reported_at=model.reported_at,
        report_reason=model.report_reason,
        hidden_at=model.hidden_at,
    )


class SqlAlchemyReviewRepository(ReviewRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, review_id: uuid.UUID) -> Review | None:
        model = await self._db.get(ReviewModel, review_id)
        return _to_entity(model) if model else None

    async def for_job(self, job_id: uuid.UUID) -> Sequence[Review]:
        rows = await self._db.scalars(select(ReviewModel).where(ReviewModel.job_id == job_id))
        return [_to_entity(model) for model in rows.all()]

    async def add(self, review: Review) -> None:
        is_about_worker = review.direction == ReviewDirectionEnum.BUYER_TO_WORKER
        self._db.add(
            ReviewModel(
                id=review.id,
                job_id=review.job_id,
                buyer_id=review.author_id if is_about_worker else review.subject_id,
                worker_id=review.subject_id if is_about_worker else review.author_id,
                direction=review.direction,
                author_id=review.author_id,
                subject_id=review.subject_id,
                rating=review.rating,
                tags=review.tags,
                comment=review.comment,
                created_at=review.created_at,
                visible_after=review.visible_after,
                published_at=review.published_at,
                had_dispute=review.had_dispute,
            )
        )
        await self._db.flush()

    async def publish(self, review_ids: Sequence[uuid.UUID], published_at: datetime) -> None:
        await self._db.execute(
            update(ReviewModel)
            .where(ReviewModel.id.in_(review_ids))
            .values(published_at=published_at)
        )

    async def set_reply(self, review_id: uuid.UUID, reply: str, replied_at: datetime) -> None:
        await self._db.execute(
            update(ReviewModel)
            .where(ReviewModel.id == review_id)
            .values(reply=reply, replied_at=replied_at)
        )

    async def set_report(
        self, review_id: uuid.UUID, *, reported_by: uuid.UUID, reason: str, reported_at: datetime
    ) -> None:
        await self._db.execute(
            update(ReviewModel)
            .where(ReviewModel.id == review_id)
            .values(reported_by=reported_by, report_reason=reason, reported_at=reported_at)
        )

    async def set_moderation(
        self,
        review_id: uuid.UUID,
        *,
        moderated_by: uuid.UUID,
        moderated_at: datetime,
        hide: bool,
    ) -> None:
        values: dict[str, object] = {
            "moderated_by": moderated_by,
            "moderated_at": moderated_at,
            "reported_at": None,
            "report_reason": None,
            "reported_by": None,
        }
        if hide:
            values["hidden_at"] = moderated_at
        await self._db.execute(
            update(ReviewModel).where(ReviewModel.id == review_id).values(**values)
        )

    async def visible_about(
        self,
        subject_id: uuid.UUID,
        direction: ReviewDirectionEnum,
        now: datetime,
        *,
        limit: int,
        offset: int,
    ) -> Sequence[PublicReview]:
        rows = await self._db.execute(
            select(ReviewModel, PersonModel.display_name, PersonModel.home_suburb, JobModel.trade)
            .join(PersonModel, PersonModel.id == ReviewModel.author_id)
            .join(JobModel, JobModel.id == ReviewModel.job_id)
            .where(
                ReviewModel.subject_id == subject_id,
                ReviewModel.direction == direction,
                visible_review_clause(now),
            )
            .order_by(desc(ReviewModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        return [
            PublicReview(
                id=model.id,
                direction=model.direction,
                rating=model.rating,
                tags=list(model.tags or []),
                comment=model.comment,
                reviewer_name=first_name(name),
                reviewer_suburb=suburb,
                trade=trade,
                created_at=model.created_at,
                had_dispute=model.had_dispute,
                reply=model.reply,
                replied_at=model.replied_at,
            )
            for model, name, suburb, trade in rows.all()
        ]

    async def visible_ratings(
        self, subject_id: uuid.UUID, direction: ReviewDirectionEnum, now: datetime
    ) -> Sequence[tuple[int, list[ReviewTagEnum]]]:
        rows = await self._db.execute(
            select(ReviewModel.rating, ReviewModel.tags).where(
                ReviewModel.subject_id == subject_id,
                ReviewModel.direction == direction,
                visible_review_clause(now),
            )
        )
        return [(rating, list(tags or [])) for rating, tags in rows.all()]

    async def reported(self, *, limit: int, offset: int) -> Sequence[ReportedReview]:
        subject = aliased(PersonModel)
        author = aliased(PersonModel)
        rows = await self._db.execute(
            select(ReviewModel, subject.display_name, author.display_name)
            .join(subject, subject.id == ReviewModel.subject_id)
            .join(author, author.id == ReviewModel.author_id)
            .where(ReviewModel.reported_at.is_not(None), ReviewModel.hidden_at.is_(None))
            .order_by(ReviewModel.reported_at)
            .limit(limit)
            .offset(offset)
        )
        return [
            ReportedReview(
                review=_to_entity(model), subject_name=subject_name, author_name=author_name
            )
            for model, subject_name, author_name in rows.all()
        ]


class SqlAlchemyJobReviewContextAdapter(JobReviewContextPort):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, job_id: uuid.UUID) -> JobReviewContext | None:
        job = await self._db.get(JobModel, job_id)
        if job is None:
            return None
        signed_off_at = await self._db.scalar(
            select(RecordEntryModel.signed_off_at).where(RecordEntryModel.job_id == job_id)
        )
        dispute_count = await self._db.scalar(
            select(func.count()).select_from(DisputeModel).where(DisputeModel.job_id == job_id)
        )
        is_completed = job.status == JobStatusEnum.COMPLETED
        return JobReviewContext(
            job_id=job.id,
            buyer_id=job.buyer_id,
            worker_id=job.worker_id,
            is_completed=is_completed,
            # A job completed without a record entry (e.g. through a
            # resolved dispute) falls back to its last update.
            signed_off_at=signed_off_at or (job.updated_at if is_completed else None),
            had_dispute=bool(dispute_count),
            trade=job.trade,
        )


async def worker_rating_stats(
    db: AsyncSession, worker_ids: Sequence[uuid.UUID] | set[uuid.UUID], now: datetime
) -> dict[uuid.UUID, tuple[Decimal | None, int]]:
    """Average and count of *visible* client reviews per worker, for the
    directory, profiles, matching and standing. Hidden (double-blind or
    removed) reviews never count."""
    if not worker_ids:
        return {}
    rows = await db.execute(
        select(ReviewModel.subject_id, func.avg(ReviewModel.rating), func.count())
        .where(
            ReviewModel.subject_id.in_(list(worker_ids)),
            ReviewModel.direction == ReviewDirectionEnum.BUYER_TO_WORKER,
            visible_review_clause(now),
        )
        .group_by(ReviewModel.subject_id)
    )
    return {subject_id: (average, int(count)) for subject_id, average, count in rows.all()}
