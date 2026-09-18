from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.payments.domain.services import (
    GetGatewayConfigUseCase,
    RecordWebhookCallbackUseCase,
    SetGatewayConfigUseCase,
)
from app.apps.payments.infrastructure.ecocash_gateway import EcoCashGateway
from app.apps.payments.infrastructure.repositories import (
    SqlAlchemyEcoCashCallbackLogRepository,
    SqlAlchemyPaymentGatewayConfigRepository,
)
from app.core.database import get_db_session
from app.core.unit_of_work import SqlAlchemyUnitOfWork, get_unit_of_work


def get_payment_gateway_config_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyPaymentGatewayConfigRepository:
    """Also implements the shared_kernel.ports.PaymentCollectionPort
    dependency chain (via EcoCashGateway below) — other apps' factories
    build an EcoCashGateway the same way (see apps/jobs, apps/crews)."""
    return SqlAlchemyPaymentGatewayConfigRepository(db)


def get_ecocash_callback_log_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyEcoCashCallbackLogRepository:
    return SqlAlchemyEcoCashCallbackLogRepository(db)


def get_ecocash_gateway(
    configs: SqlAlchemyPaymentGatewayConfigRepository = Depends(
        get_payment_gateway_config_repository
    ),
) -> EcoCashGateway:
    return EcoCashGateway(configs)


def get_gateway_config_use_case(
    configs: SqlAlchemyPaymentGatewayConfigRepository = Depends(
        get_payment_gateway_config_repository
    ),
) -> GetGatewayConfigUseCase:
    return GetGatewayConfigUseCase(configs)


def get_set_gateway_config_use_case(
    configs: SqlAlchemyPaymentGatewayConfigRepository = Depends(
        get_payment_gateway_config_repository
    ),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> SetGatewayConfigUseCase:
    return SetGatewayConfigUseCase(configs, uow)


def get_record_webhook_callback_use_case(
    logs: SqlAlchemyEcoCashCallbackLogRepository = Depends(get_ecocash_callback_log_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> RecordWebhookCallbackUseCase:
    return RecordWebhookCallbackUseCase(logs, uow)
