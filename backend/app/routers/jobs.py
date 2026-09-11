import uuid
from collections.abc import Sequence
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RequireRole, get_current_user
from app.database import get_db_session
from app.ledger import sum_ledger_entries
from app.matching import find_top_candidates, is_worker_busy
from app.models import (
    Dispute,
    DisputeStatusEnum,
    Job,
    JobStatusEnum,
    LedgerEntry,
    LedgerEntryTypeEnum,
    Person,
    RecordEntry,
    RoleEnum,
    Skill,
    Suburb,
)
from app.pagination import Pagination, pagination_params
from app.schemas import (
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
from app.standing import recompute_standing

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _require_job_party(job: Job, current_user: Person) -> None:
    is_party_to_job = current_user.id in (job.buyer_id, job.worker_id)
    if not is_party_to_job and current_user.role != RoleEnum.OPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to view this job",
        )


@router.post("/request", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job_request(
    payload: JobRequestCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> Job:
    """Ingest a Quick Hire job request (text, or a voice-note transcript arriving as text)."""
    suburb = await db.get(Suburb, payload.suburb)
    if suburb is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unknown suburb",
        )

    job = Job(
        buyer_id=current_user.id,
        status=JobStatusEnum.REQUESTED,
        trade=payload.trade,
        suburb=payload.suburb,
        address=payload.address,
        problem_description=payload.problem_description,
        problem_photo_url=payload.problem_photo_url,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Job:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    _require_job_party(job, current_user)

    return job


@router.get("/{job_id}/matches", response_model=list[MatchCandidateOut])
async def get_job_matches(
    job_id: uuid.UUID,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> list[MatchCandidateOut]:
    """Run the matching engine and return up to 3 ranked worker candidates.

    The first call on a REQUESTED job transitions it to MATCHED. A job past
    that lifecycle stage (BOOKED or later) no longer accepts new matches.
    """
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to view matches for this job",
        )

    if job.status not in (JobStatusEnum.REQUESTED, JobStatusEnum.MATCHED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is no longer accepting matches",
        )

    candidates = await find_top_candidates(db, job)

    if job.status == JobStatusEnum.REQUESTED:
        job.status = JobStatusEnum.MATCHED
        await db.commit()

    return candidates


@router.post("/{job_id}/book", response_model=JobOut)
async def book_job(
    job_id: uuid.UUID,
    payload: BookingCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> Job:
    """Book a worker for a matched job: holds the deposit and reveals the address.

    The chosen worker must be a registered WORKER with a skill in this job's
    trade and not already tied to another active job.
    """
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to book this job",
        )

    if job.status != JobStatusEnum.MATCHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job must be MATCHED before it can be booked",
        )

    worker = await db.get(Person, payload.worker_id)
    if worker is None or worker.role != RoleEnum.WORKER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="worker_id does not refer to a registered worker",
        )

    skill_stmt = select(Skill).where(
        Skill.worker_id == payload.worker_id, Skill.trade == job.trade
    )
    skill = (await db.execute(skill_stmt)).scalars().first()
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Worker is not skilled in this job's trade",
        )

    if await is_worker_busy(db, payload.worker_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is already committed to another active job",
        )

    job.worker_id = payload.worker_id
    job.status = JobStatusEnum.BOOKED
    db.add(
        LedgerEntry(
            job_id=job.id,
            amount=payload.deposit_amount,
            entry_type=LedgerEntryTypeEnum.DEPOSIT_HELD,
        )
    )
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/{job_id}/quote", response_model=JobOut)
async def submit_quote(
    job_id: uuid.UUID,
    payload: QuoteCreate,
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Job:
    """The assigned worker submits their on-site price assessment.

    Commits the remaining balance (quote minus the deposit already held) and
    moves the job into IN_PROGRESS.
    """
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.worker_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to submit a quote for this job",
        )

    if job.status != JobStatusEnum.BOOKED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job must be BOOKED before a quote can be submitted",
        )

    deposit_total = await sum_ledger_entries(db, job.id, LedgerEntryTypeEnum.DEPOSIT_HELD)
    if payload.quote_amount <= deposit_total:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Quote must exceed the deposit already held",
        )

    job.quote_amount = payload.quote_amount
    job.status = JobStatusEnum.IN_PROGRESS
    db.add(
        LedgerEntry(
            job_id=job.id,
            amount=payload.quote_amount - deposit_total,
            entry_type=LedgerEntryTypeEnum.BALANCE_COMMITTED,
        )
    )
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/{job_id}/complete", response_model=JobOut)
async def complete_job(
    job_id: uuid.UUID,
    payload: CompletionCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> Job:
    """Buyer signs off: writes the immutable record entry and releases the balance."""
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to complete this job",
        )

    if job.status != JobStatusEnum.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job must be IN_PROGRESS before it can be completed",
        )

    db.add(
        RecordEntry(
            job_id=job.id,
            worker_id=job.worker_id,
            what_was_done=payload.what_was_done,
            client_words=payload.client_words,
            before_photo_url=payload.before_photo_url,
            after_photo_url=payload.after_photo_url,
            signed_off_at=datetime.utcnow(),
        )
    )
    db.add(
        LedgerEntry(
            job_id=job.id,
            amount=job.quote_amount,
            entry_type=LedgerEntryTypeEnum.RELEASED,
        )
    )
    job.status = JobStatusEnum.COMPLETED
    assert job.worker_id is not None, "IN_PROGRESS implies a booked worker"
    await recompute_standing(db, job.worker_id)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/{job_id}/dispute", response_model=DisputeOut, status_code=status.HTTP_201_CREATED)
async def raise_dispute(
    job_id: uuid.UUID,
    payload: DisputeCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> Dispute:
    """Buyer raises a concern: money freezes (no further ledger release) and
    the job moves to DISPUTED. The worker must answer before any consequence."""
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to dispute this job",
        )

    if job.status != JobStatusEnum.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job must be IN_PROGRESS before it can be disputed",
        )

    dispute = Dispute(
        job_id=job.id,
        raised_by_id=current_user.id,
        reason=payload.reason,
        status=DisputeStatusEnum.OPEN,
    )
    db.add(dispute)
    job.status = JobStatusEnum.DISPUTED
    assert job.worker_id is not None, "IN_PROGRESS implies a booked worker"
    await recompute_standing(db, job.worker_id)
    await db.commit()
    await db.refresh(dispute)
    return dispute


@router.post("/{job_id}/dispute/respond", response_model=DisputeOut)
async def respond_to_dispute(
    job_id: uuid.UUID,
    payload: DisputeResponseCreate,
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dispute:
    """Assigned worker answers the dispute. Standing was frozen, not dropped,
    while it was open. Default outcome is a return visit, not a refund."""
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.worker_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to respond to this dispute",
        )

    if job.status != JobStatusEnum.DISPUTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is not currently disputed",
        )

    dispute_stmt = (
        select(Dispute)
        .where(Dispute.job_id == job.id, Dispute.status == DisputeStatusEnum.OPEN)
        .order_by(Dispute.created_at.desc())
    )
    dispute = (await db.execute(dispute_stmt)).scalars().first()
    if dispute is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No open dispute for this job"
        )

    dispute.worker_response = payload.response
    dispute.before_photo_url = payload.before_photo_url
    dispute.after_photo_url = payload.after_photo_url
    dispute.status = DisputeStatusEnum.RESOLVED_RETURN_VISIT
    dispute.responded_at = datetime.utcnow()

    job.status = JobStatusEnum.IN_PROGRESS

    await db.commit()
    await db.refresh(dispute)
    return dispute


@router.get("/{job_id}/disputes", response_model=list[DisputeOut])
async def list_job_disputes(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db_session),
) -> Sequence[Dispute]:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    _require_job_party(job, current_user)

    result = await db.execute(
        select(Dispute)
        .where(Dispute.job_id == job_id)
        .order_by(Dispute.created_at)
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    return result.scalars().all()


@router.get("/{job_id}/ledger", response_model=list[LedgerEntryOut])
async def get_job_ledger(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db_session),
) -> Sequence[LedgerEntry]:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    _require_job_party(job, current_user)

    result = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.job_id == job_id)
        .order_by(LedgerEntry.created_at)
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    return result.scalars().all()


@router.get("/{job_id}/record", response_model=RecordEntryOut)
async def get_job_record(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RecordEntry:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    _require_job_party(job, current_user)

    result = await db.execute(select(RecordEntry).where(RecordEntry.job_id == job_id))
    record = result.scalars().first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No record entry yet")

    return record
