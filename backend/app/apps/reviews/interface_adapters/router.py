"""Two-way ratings and reviews (ADR-011)."""

import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, Query, status
from opentelemetry import trace

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole, get_current_user
from app.apps.reviews.domain.entities import JobReviews, Review, ReviewPage
from app.apps.reviews.domain.services import (
    GetClientReviewsForJobUseCase,
    GetJobReviewsUseCase,
    ListReportedReviewsUseCase,
    ListReviewsAboutUseCase,
    ModerateReviewUseCase,
    ReplyToReviewUseCase,
    ReportReviewUseCase,
    SubmitReviewUseCase,
)
from app.apps.reviews.interface_adapters.dependencies import (
    get_client_reviews_for_job_use_case,
    get_job_reviews_use_case,
    get_list_reported_reviews_use_case,
    get_list_reviews_about_use_case,
    get_moderate_review_use_case,
    get_reply_to_review_use_case,
    get_report_review_use_case,
    get_submit_review_use_case,
)
from app.apps.reviews.interface_adapters.schemas import (
    JobReviewsOut,
    ModerationCreate,
    ReplyCreate,
    ReportCreate,
    ReportedReviewOut,
    ReviewCreate,
    ReviewOut,
    ReviewPageOut,
)
from app.core.pagination import Pagination, pagination_params
from app.core.telemetry import logger
from app.shared_kernel.enums import ReviewDirectionEnum, RoleEnum

router = APIRouter(tags=["reviews"])
ops_router = APIRouter(prefix="/ops/reviews", tags=["ops"])
tracer = trace.get_tracer(__name__)


@router.post("/jobs/{job_id}/review", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def review_completed_job(
    job_id: uuid.UUID,
    payload: ReviewCreate,
    current_user: Person = Depends(get_current_user),
    use_case: SubmitReviewUseCase = Depends(get_submit_review_use_case),
) -> Review:
    """Either party reviews the other within 14 days of sign-off. Hidden
    until the other side reviews too, or the 14 days pass."""
    with tracer.start_as_current_span("reviews.submit") as span:
        span.set_attribute("job.id", str(job_id))
        review = await use_case.execute(
            job_id=job_id,
            author_id=current_user.id,
            rating=payload.rating,
            tags=payload.tags,
            comment=payload.comment,
        )
        span.set_attribute("review.direction", review.direction.value)
        span.set_attribute("review.published", review.published_at is not None)
        logger.info(
            f"Review submitted job_id={job_id} direction={review.direction.value} "
            f"published={review.published_at is not None}"
        )
        return review


@router.get("/jobs/{job_id}/reviews", response_model=JobReviewsOut)
async def get_job_reviews(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    use_case: GetJobReviewsUseCase = Depends(get_job_reviews_use_case),
) -> JobReviews:
    """Both sides' reviews of one job, as one of its parties sees them."""
    with tracer.start_as_current_span("reviews.get_for_job") as span:
        span.set_attribute("job.id", str(job_id))
        return await use_case.execute(job_id=job_id, person_id=current_user.id)


@router.get("/jobs/{job_id}/client-reviews", response_model=ReviewPageOut)
async def get_client_reviews_for_job(
    job_id: uuid.UUID,
    limit: int = Query(3, ge=0, le=20),
    current_user: Person = Depends(get_current_user),
    use_case: GetClientReviewsForJobUseCase = Depends(get_client_reviews_for_job_use_case),
) -> ReviewPage:
    """What workers have said about the client who posted this job."""
    with tracer.start_as_current_span("reviews.client_for_job") as span:
        span.set_attribute("job.id", str(job_id))
        return await use_case.execute(job_id=job_id, limit=limit)


@router.get("/workers/{worker_id}/reviews", response_model=ReviewPageOut)
async def list_worker_reviews(
    worker_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListReviewsAboutUseCase = Depends(get_list_reviews_about_use_case),
) -> ReviewPage:
    """Visible client reviews of a worker, newest first, with a summary."""
    with tracer.start_as_current_span("reviews.list_for_worker") as span:
        span.set_attribute("worker.id", str(worker_id))
        page = await use_case.execute(
            subject_id=worker_id,
            direction=ReviewDirectionEnum.BUYER_TO_WORKER,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        span.set_attribute("reviews.count", page.summary.count)
        return page


@router.get("/clients/{buyer_id}/reviews", response_model=ReviewPageOut)
async def list_client_reviews(
    buyer_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListReviewsAboutUseCase = Depends(get_list_reviews_about_use_case),
) -> ReviewPage:
    """Visible worker reviews of a client (an employer seeing their own, or a
    worker after booking)."""
    with tracer.start_as_current_span("reviews.list_for_client") as span:
        span.set_attribute("client.id", str(buyer_id))
        return await use_case.execute(
            subject_id=buyer_id,
            direction=ReviewDirectionEnum.WORKER_TO_BUYER,
            limit=pagination.limit,
            offset=pagination.offset,
        )


@router.post("/reviews/{review_id}/reply", response_model=ReviewOut)
async def reply_to_review(
    review_id: uuid.UUID,
    payload: ReplyCreate,
    current_user: Person = Depends(get_current_user),
    use_case: ReplyToReviewUseCase = Depends(get_reply_to_review_use_case),
) -> Review:
    """The person reviewed answers once, publicly."""
    with tracer.start_as_current_span("reviews.reply") as span:
        span.set_attribute("review.id", str(review_id))
        review = await use_case.execute(
            review_id=review_id, person_id=current_user.id, reply=payload.reply
        )
        logger.info(f"Review replied review_id={review_id}")
        return review


@router.post("/reviews/{review_id}/report", response_model=ReviewOut)
async def report_review(
    review_id: uuid.UUID,
    payload: ReportCreate,
    current_user: Person = Depends(get_current_user),
    use_case: ReportReviewUseCase = Depends(get_report_review_use_case),
) -> Review:
    """The person reviewed flags a review for OPS. It stays up until OPS decides."""
    with tracer.start_as_current_span("reviews.report") as span:
        span.set_attribute("review.id", str(review_id))
        review = await use_case.execute(
            review_id=review_id, person_id=current_user.id, reason=payload.reason
        )
        logger.info(
            f"Review reported review_id={review_id}",
            extra={
                "audit": {
                    "event": "review_reported",
                    "review_id": str(review_id),
                    "reported_by": str(current_user.id),
                }
            },
        )
        return review


@ops_router.get("/reported", response_model=list[ReportedReviewOut])
async def list_reported_reviews(
    current_user: Person = Depends(RequireRole([RoleEnum.OPS])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListReportedReviewsUseCase = Depends(get_list_reported_reviews_use_case),
) -> Sequence[ReportedReviewOut]:
    with tracer.start_as_current_span("ops.reviews.list_reported") as span:
        rows = await use_case.execute(limit=pagination.limit, offset=pagination.offset)
        span.set_attribute("reviews.reported_count", len(rows))
        return [
            ReportedReviewOut(
                review_id=row.review.id,
                job_id=row.review.job_id,
                direction=row.review.direction,
                rating=row.review.rating,
                comment=row.review.comment,
                reply=row.review.reply,
                report_reason=row.review.report_reason,
                reported_at=row.review.reported_at,
                subject_name=row.subject_name,
                author_name=row.author_name,
            )
            for row in rows
        ]


@ops_router.post("/{review_id}/moderate", response_model=ReviewOut)
async def moderate_review(
    review_id: uuid.UUID,
    payload: ModerationCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.OPS])),
    use_case: ModerateReviewUseCase = Depends(get_moderate_review_use_case),
) -> Review:
    """Keep a reported review, or remove it from view and from the rating."""
    with tracer.start_as_current_span("ops.reviews.moderate") as span:
        span.set_attribute("review.id", str(review_id))
        span.set_attribute("review.decision", payload.decision)
        review = await use_case.execute(
            review_id=review_id,
            moderator_id=current_user.id,
            remove=payload.decision == "REMOVE",
        )
        logger.info(
            f"Review moderated review_id={review_id} decision={payload.decision}",
            extra={
                "audit": {
                    "event": "review_moderated",
                    "review_id": str(review_id),
                    "moderator_id": str(current_user.id),
                    "decision": payload.decision,
                }
            },
        )
        return review
