import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, status

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole, get_current_user
from app.apps.jobs.domain.entities import Dispute, Job, LedgerEntry, MatchCandidate, RecordEntry
from app.apps.jobs.domain.services import (
    BookJobUseCase,
    CompleteJobUseCase,
    CreateJobRequestUseCase,
    GetJobLedgerUseCase,
    GetJobMatchesUseCase,
    GetJobRecordUseCase,
    GetJobUseCase,
    ListJobDisputesUseCase,
    RaiseDisputeUseCase,
    RespondToDisputeUseCase,
    SubmitQuoteUseCase,
)
from app.apps.jobs.interface_adapters.dependencies import (
    get_book_job_use_case,
    get_complete_job_use_case,
    get_create_job_request_use_case,
    get_get_job_ledger_use_case,
    get_get_job_matches_use_case,
    get_get_job_record_use_case,
    get_get_job_use_case,
    get_list_job_disputes_use_case,
    get_raise_dispute_use_case,
    get_respond_to_dispute_use_case,
    get_submit_quote_use_case,
)
from app.apps.jobs.interface_adapters.schemas import (
    BookingCreate,
    CompletionCreate,
    DisputeCreate,
    DisputeOut,
    DisputeResponseCreate,
    JobOut,
    JobRequestCreate,
    LedgerEntryOut,
    MatchCandidateOut,
    QuoteCreate,
    RecordEntryOut,
)
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
    )


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    use_case: GetJobUseCase = Depends(get_get_job_use_case),
) -> Job:
    return await use_case.execute(job_id, current_user.id, current_user.role)


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
