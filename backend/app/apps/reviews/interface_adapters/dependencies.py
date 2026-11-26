from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.apps.reviews.infrastructure.repositories import (
    SqlAlchemyJobReviewContextAdapter,
    SqlAlchemyReviewRepository,
)
from app.core.database import get_db_session
from app.core.unit_of_work import SqlAlchemyUnitOfWork, get_unit_of_work


def get_review_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyReviewRepository:
    return SqlAlchemyReviewRepository(db)


def get_job_review_context(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyJobReviewContextAdapter:
    return SqlAlchemyJobReviewContextAdapter(db)


def get_submit_review_use_case(
    reviews: SqlAlchemyReviewRepository = Depends(get_review_repository),
    jobs: SqlAlchemyJobReviewContextAdapter = Depends(get_job_review_context),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> SubmitReviewUseCase:
    return SubmitReviewUseCase(reviews, jobs, uow)


def get_job_reviews_use_case(
    reviews: SqlAlchemyReviewRepository = Depends(get_review_repository),
    jobs: SqlAlchemyJobReviewContextAdapter = Depends(get_job_review_context),
) -> GetJobReviewsUseCase:
    return GetJobReviewsUseCase(reviews, jobs)


def get_list_reviews_about_use_case(
    reviews: SqlAlchemyReviewRepository = Depends(get_review_repository),
) -> ListReviewsAboutUseCase:
    return ListReviewsAboutUseCase(reviews)


def get_client_reviews_for_job_use_case(
    jobs: SqlAlchemyJobReviewContextAdapter = Depends(get_job_review_context),
    list_reviews: ListReviewsAboutUseCase = Depends(get_list_reviews_about_use_case),
) -> GetClientReviewsForJobUseCase:
    return GetClientReviewsForJobUseCase(jobs, list_reviews)


def get_reply_to_review_use_case(
    reviews: SqlAlchemyReviewRepository = Depends(get_review_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> ReplyToReviewUseCase:
    return ReplyToReviewUseCase(reviews, uow)


def get_report_review_use_case(
    reviews: SqlAlchemyReviewRepository = Depends(get_review_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> ReportReviewUseCase:
    return ReportReviewUseCase(reviews, uow)


def get_list_reported_reviews_use_case(
    reviews: SqlAlchemyReviewRepository = Depends(get_review_repository),
) -> ListReportedReviewsUseCase:
    return ListReportedReviewsUseCase(reviews)


def get_moderate_review_use_case(
    reviews: SqlAlchemyReviewRepository = Depends(get_review_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> ModerateReviewUseCase:
    return ModerateReviewUseCase(reviews, uow)
