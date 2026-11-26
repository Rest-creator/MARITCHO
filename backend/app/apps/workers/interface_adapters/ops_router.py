"""OPS review of identity documents (ADR-010).

Workers submit their ID and Police Clearance photos privately; these
endpoints let OPS staff see what is waiting and approve or reject it. Badges
and the IDENTIFIED grade follow the decision. The ID number typed by the
reviewer is hashed and never logged.
"""

import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends
from opentelemetry import trace

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole
from app.apps.workers.domain.entities import PendingVettingDocument, WorkerVettingView
from app.apps.workers.domain.services import (
    ListPendingVettingUseCase,
    ReviewIdDocumentUseCase,
    ReviewPoliceClearanceUseCase,
)
from app.apps.workers.interface_adapters.dependencies import (
    get_list_pending_vetting_use_case,
    get_review_id_document_use_case,
    get_review_police_clearance_use_case,
)
from app.apps.workers.interface_adapters.schemas import (
    IdReviewCreate,
    PendingVettingDocumentOut,
    PoliceClearanceReviewCreate,
    WorkerVettingOut,
)
from app.core.pagination import Pagination, pagination_params
from app.core.telemetry import logger
from app.shared_kernel.enums import RoleEnum

router = APIRouter(prefix="/ops/vetting", tags=["ops"])
tracer = trace.get_tracer(__name__)


@router.get("/pending", response_model=list[PendingVettingDocumentOut])
async def list_pending_vetting(
    current_user: Person = Depends(RequireRole([RoleEnum.OPS])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListPendingVettingUseCase = Depends(get_list_pending_vetting_use_case),
) -> Sequence[PendingVettingDocument]:
    """Identity documents waiting for review, oldest first."""
    with tracer.start_as_current_span("ops.vetting.list_pending") as span:
        documents = await use_case.execute(limit=pagination.limit, offset=pagination.offset)
        span.set_attribute("vetting.pending_count", len(documents))
        return documents


@router.post("/{worker_id}/id", response_model=WorkerVettingOut)
async def review_id_document(
    worker_id: uuid.UUID,
    payload: IdReviewCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.OPS])),
    use_case: ReviewIdDocumentUseCase = Depends(get_review_id_document_use_case),
) -> WorkerVettingView:
    """Approve (name as printed + ID number) or reject (reason) a worker's ID."""
    with tracer.start_as_current_span("ops.vetting.review_id") as span:
        span.set_attribute("worker.id", str(worker_id))
        span.set_attribute("vetting.decision", payload.decision)
        view = await use_case.execute(
            worker_id=worker_id,
            reviewer_id=current_user.id,
            approve=payload.decision == "APPROVE",
            verified_name=payload.verified_name,
            id_number=payload.id_number,
            rejection_reason=payload.rejection_reason,
        )
        span.set_attribute("worker.grade", view.grade.value)
        logger.info(
            f"ID document reviewed worker={worker_id} decision={payload.decision}",
            extra={
                "audit": {
                    "event": "vetting_id_reviewed",
                    "worker_id": str(worker_id),
                    "reviewer_id": str(current_user.id),
                    "decision": payload.decision,
                }
            },
        )
        return view


@router.post("/{worker_id}/police-clearance", response_model=WorkerVettingOut)
async def review_police_clearance(
    worker_id: uuid.UUID,
    payload: PoliceClearanceReviewCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.OPS])),
    use_case: ReviewPoliceClearanceUseCase = Depends(get_review_police_clearance_use_case),
) -> WorkerVettingView:
    """Approve (issue date) or reject (reason) a Police Clearance certificate."""
    with tracer.start_as_current_span("ops.vetting.review_police_clearance") as span:
        span.set_attribute("worker.id", str(worker_id))
        span.set_attribute("vetting.decision", payload.decision)
        view = await use_case.execute(
            worker_id=worker_id,
            reviewer_id=current_user.id,
            approve=payload.decision == "APPROVE",
            issued_on=payload.issued_on,
            rejection_reason=payload.rejection_reason,
        )
        logger.info(
            f"Police clearance reviewed worker={worker_id} decision={payload.decision}",
            extra={
                "audit": {
                    "event": "vetting_police_clearance_reviewed",
                    "worker_id": str(worker_id),
                    "reviewer_id": str(current_user.id),
                    "decision": payload.decision,
                }
            },
        )
        return view
