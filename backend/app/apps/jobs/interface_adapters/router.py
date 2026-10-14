import uuid
from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole, get_current_user
from app.apps.jobs.domain.entities import (
    Dispute,
    Job,
    LedgerEntry,
    MatchCandidate,
    OpenJobCandidate,
    RecordEntry,
)
from app.apps.jobs.domain.services import (
    BookJobUseCase,
    CompleteJobUseCase,
    CreateJobRequestUseCase,
    GetJobLedgerUseCase,
    GetJobMatchesUseCase,
    GetJobRecordUseCase,
    GetJobUseCase,
    ListAssignedJobsUseCase,
    ListJobDisputesUseCase,
    ListMyJobsUseCase,
    ListMyOffersUseCase,
    ListOpenJobsForWorkerUseCase,
    RaiseDisputeUseCase,
    RespondToDisputeUseCase,
    SubmitJobOfferUseCase,
    SubmitQuoteUseCase,
)
from app.apps.jobs.infrastructure.models import JobModel
from app.apps.jobs.infrastructure.review_models import ReviewModel
from app.apps.jobs.interface_adapters.dependencies import (
    get_book_job_use_case,
    get_complete_job_use_case,
    get_create_job_request_use_case,
    get_get_job_ledger_use_case,
    get_get_job_matches_use_case,
    get_get_job_record_use_case,
    get_get_job_use_case,
    get_list_assigned_jobs_use_case,
    get_list_job_disputes_use_case,
    get_list_my_jobs_use_case,
    get_list_my_offers_use_case,
    get_list_open_jobs_use_case,
    get_raise_dispute_use_case,
    get_respond_to_dispute_use_case,
    get_submit_job_offer_use_case,
    get_submit_quote_use_case,
)
from app.apps.jobs.interface_adapters.schemas import (
    BookingCreate,
    CompletionCreate,
    DisputeCreate,
    DisputeOut,
    DisputeResponseCreate,
    JobOfferCreate,
    JobOfferOut,
    JobOut,
    JobRequestCreate,
    LedgerEntryOut,
    MatchCandidateOut,
    MyJobOut,
    MyOfferOut,
    OpenJobOut,
    QuoteCreate,
    RecordEntryOut,
    ReviewCreate,
)
from app.core.database import get_db_session
from app.core.pagination import Pagination, pagination_params
from app.shared_kernel.enums import RoleEnum

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/request", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job_request(
    payload: JobRequestCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: CreateJobRequestUseCase = Depends(get_create_job_request_use_case),
) -> Job:
    """Ingest a Quick Hire job request (text, or a voice-note transcript arriving as text)."""
    return await use_case.execute(
        buyer_id=current_user.id,
        trade=payload.trade,
        suburb=payload.suburb,
        address=payload.address,
        landmark_narrative=payload.landmark_narrative,
        latitude=payload.latitude,
        longitude=payload.longitude,
        problem_description=payload.problem_description,
        problem_photo_url=payload.problem_photo_url,
        budget_amount=payload.budget_amount,
        needed_by=payload.needed_by,
    )


@router.get("/mine", response_model=list[MyJobOut])
async def list_my_jobs(
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListMyJobsUseCase = Depends(get_list_my_jobs_use_case),
) -> list[MyJobOut]:
    """This buyer's own jobs, newest first, each with its offer count.

    Registered BEFORE `/{job_id}` below (same reason as `/open`): the
    generic path would otherwise swallow this route and fail UUID parsing
    on "mine".
    """
    pairs = await use_case.execute(
        current_user.id, limit=pagination.limit, offset=pagination.offset
    )
    return [MyJobOut(**asdict(job), offer_count=count) for job, count in pairs]


@router.get("/open", response_model=list[OpenJobOut])
async def list_open_jobs(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListOpenJobsForWorkerUseCase = Depends(get_list_open_jobs_use_case),
) -> list[OpenJobCandidate]:
    """Jobs across this worker's trades that are still open (REQUESTED or
    MATCHED) and within range of one of their declared service areas —
    the worker-facing reverse view of matching, for submitting a JobOffer.

    Registered BEFORE `/{job_id}` below: the generic path would otherwise
    swallow this route and fail UUID parsing on "open".
    """
    return await use_case.execute(current_user.id, limit=pagination.limit, offset=pagination.offset)


@router.get("/assigned", response_model=list[JobOut])
async def list_assigned_jobs(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListAssignedJobsUseCase = Depends(get_list_assigned_jobs_use_case),
) -> list[Job]:
    """This worker's own jobs (any status), newest first.

    Registered BEFORE `/{job_id}` below: same UUID-swallowing reason as
    `/open` and `/my-offers`.
    """
    return await use_case.execute(current_user.id, limit=pagination.limit, offset=pagination.offset)


@router.get("/my-offers", response_model=list[MyOfferOut])
async def list_my_offers(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: ListMyOffersUseCase = Depends(get_list_my_offers_use_case),
) -> list[MyOfferOut]:
    """This worker's own submitted offers, across all jobs.

    Registered BEFORE `/{job_id}` below: same UUID-swallowing reason as
    `/open` and `/assigned`.
    """
    pairs = await use_case.execute(current_user.id)
    results = []
    for offer, job in pairs:
        assert offer.created_at is not None, "JobOfferModel.created_at has a Python-side default"
        assert offer.updated_at is not None, "JobOfferModel.updated_at has a Python-side default"
        results.append(
            MyOfferOut(
                id=offer.id,
                job_id=offer.job_id,
                quoted_amount=offer.quoted_amount,
                availability_note=offer.availability_note,
                created_at=offer.created_at,
                updated_at=offer.updated_at,
                job_trade=job.trade,
                job_suburb=job.suburb,
                job_status=job.status,
                needed_by=job.needed_by,
            )
        )
    return results


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    use_case: GetJobUseCase = Depends(get_get_job_use_case),
) -> Job:
    job = await use_case.execute(job_id, current_user.id, current_user.role)
    return job


@router.get("/{job_id}/matches", response_model=list[MatchCandidateOut])
async def get_job_matches(
    job_id: uuid.UUID,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: GetJobMatchesUseCase = Depends(get_get_job_matches_use_case),
) -> list[MatchCandidate]:
    """Run the matching engine and return up to 3 ranked worker candidates.

    The first call on a REQUESTED job transitions it to MATCHED. A job past
    that lifecycle stage (BOOKED or later) no longer accepts new matches.
    """
    return await use_case.execute(job_id, current_user.id)


@router.post("/{job_id}/offers", response_model=JobOfferOut, status_code=status.HTTP_201_CREATED)
async def submit_job_offer(
    job_id: uuid.UUID,
    payload: JobOfferCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: SubmitJobOfferUseCase = Depends(get_submit_job_offer_use_case),
) -> dict[str, object]:
    """A worker (not yet booked) attaches their own price + availability to
    a still-open job. Resubmitting revises the existing offer."""
    offer = await use_case.execute(
        job_id=job_id,
        worker_id=current_user.id,
        quoted_amount=payload.quoted_amount,
        availability_note=payload.availability_note,
    )
    return {**asdict(offer), "worker_display_name": current_user.display_name}


@router.post("/{job_id}/book", response_model=JobOut)
async def book_job(
    job_id: uuid.UUID,
    payload: BookingCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: BookJobUseCase = Depends(get_book_job_use_case),
) -> Job:
    """Book a worker for a matched job: holds the deposit and reveals the address.

    The chosen worker must be a registered WORKER with a skill in this job's
    trade and not already tied to another active job.
    """
    return await use_case.execute(
        job_id=job_id,
        buyer_id=current_user.id,
        buyer_phone=current_user.phone,
        worker_id=payload.worker_id,
        deposit_amount=payload.deposit_amount,
        currency=payload.currency,
    )


@router.post("/{job_id}/quote", response_model=JobOut)
async def submit_quote(
    job_id: uuid.UUID,
    payload: QuoteCreate,
    current_user: Person = Depends(get_current_user),
    use_case: SubmitQuoteUseCase = Depends(get_submit_quote_use_case),
) -> Job:
    """The assigned worker submits their on-site price assessment.

    Commits the remaining balance (quote minus the deposit already held) and
    moves the job into IN_PROGRESS.
    """
    return await use_case.execute(
        job_id=job_id,
        worker_id=current_user.id,
        labor_amount=payload.labor_amount,
        materials_amount=payload.materials_amount,
    )


@router.post("/{job_id}/complete", response_model=JobOut)
async def complete_job(
    job_id: uuid.UUID,
    payload: CompletionCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: CompleteJobUseCase = Depends(get_complete_job_use_case),
) -> Job:
    """Buyer signs off: writes the immutable record entry and releases the balance."""
    return await use_case.execute(
        job_id=job_id,
        buyer_id=current_user.id,
        what_was_done=payload.what_was_done,
        client_words=payload.client_words,
        before_photo_url=payload.before_photo_url,
        after_photo_url=payload.after_photo_url,
    )


@router.post("/{job_id}/review", status_code=status.HTTP_201_CREATED)
async def review_completed_job(
    job_id: uuid.UUID,
    payload: ReviewCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    job = await db.get(JobModel, job_id)
    if job is None or job.buyer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status.value != "COMPLETED" or job.worker_id is None:
        raise HTTPException(status_code=409, detail="Job must be completed before review")
    existing = await db.scalar(select(ReviewModel).where(ReviewModel.job_id == job_id))
    if existing:
        raise HTTPException(status_code=409, detail="Job already reviewed")
    review = ReviewModel(
        id=uuid.uuid4(),
        job_id=job_id,
        buyer_id=current_user.id,
        worker_id=job.worker_id,
        rating=payload.rating,
        tags=payload.tags,
        comment=payload.comment,
        created_at=datetime.utcnow(),
    )
    db.add(review)
    await db.commit()
    return {
        "id": str(review.id),
        "job_id": str(job_id),
        "rating": review.rating,
        "tags": [tag.value for tag in review.tags],
        "comment": review.comment,
    }


@router.post("/{job_id}/dispute", response_model=DisputeOut, status_code=status.HTTP_201_CREATED)
async def raise_dispute(
    job_id: uuid.UUID,
    payload: DisputeCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: RaiseDisputeUseCase = Depends(get_raise_dispute_use_case),
) -> Dispute:
    """Buyer raises a concern: money freezes (no further ledger release) and
    the job moves to DISPUTED. The worker must answer before any consequence."""
    return await use_case.execute(job_id=job_id, buyer_id=current_user.id, reason=payload.reason)


@router.post("/{job_id}/dispute/respond", response_model=DisputeOut)
async def respond_to_dispute(
    job_id: uuid.UUID,
    payload: DisputeResponseCreate,
    current_user: Person = Depends(get_current_user),
    use_case: RespondToDisputeUseCase = Depends(get_respond_to_dispute_use_case),
) -> Dispute:
    """Assigned worker answers the dispute. Standing was frozen, not dropped,
    while it was open. Default outcome is a return visit, not a refund."""
    return await use_case.execute(
        job_id=job_id,
        worker_id=current_user.id,
        response=payload.response,
        before_photo_url=payload.before_photo_url,
        after_photo_url=payload.after_photo_url,
    )


@router.get("/{job_id}/disputes", response_model=list[DisputeOut])
async def list_job_disputes(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListJobDisputesUseCase = Depends(get_list_job_disputes_use_case),
) -> Sequence[Dispute]:
    return await use_case.execute(
        job_id, current_user.id, current_user.role, limit=pagination.limit, offset=pagination.offset
    )


@router.get("/{job_id}/ledger", response_model=list[LedgerEntryOut])
async def get_job_ledger(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    use_case: GetJobLedgerUseCase = Depends(get_get_job_ledger_use_case),
) -> Sequence[LedgerEntry]:
    return await use_case.execute(
        job_id, current_user.id, current_user.role, limit=pagination.limit, offset=pagination.offset
    )


@router.get("/{job_id}/record", response_model=RecordEntryOut)
async def get_job_record(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    use_case: GetJobRecordUseCase = Depends(get_get_job_record_use_case),
) -> RecordEntry:
    return await use_case.execute(job_id, current_user.id, current_user.role)
