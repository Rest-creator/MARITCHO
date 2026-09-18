import time
from typing import Any

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole
from app.apps.accounts.interface_adapters.router import router as accounts_router
from app.apps.crews.interface_adapters.router import crew_orders_router, crews_router
from app.apps.jobs.interface_adapters.router import router as jobs_router
from app.apps.payments.interface_adapters.router import router as payment_gateways_router
from app.apps.suburbs.interface_adapters.router import router as suburbs_router
from app.apps.workers.interface_adapters.router import router as workers_router
from app.core.database import get_db_session
from app.core.exceptions import register_exception_handlers
from app.core.redis import get_redis_client
from app.core.telemetry import logger, setup_telemetry
from app.shared_kernel.enums import RoleEnum

app = FastAPI(title="Maricho Backend API")

# Initialize telemetry
setup_telemetry(app, "maricho-api")

register_exception_handlers(app)

app.include_router(accounts_router)
app.include_router(jobs_router)
app.include_router(workers_router)
app.include_router(suburbs_router)
app.include_router(crews_router)
app.include_router(crew_orders_router)
app.include_router(payment_gateways_router)

@app.get("/health/live", status_code=status.HTTP_200_OK)
def liveness_probe() -> dict[str, Any]:
    """Liveness probe to verify process is running."""
    return {
        "status": "UP",
        "timestamp": time.time(),
        "component": "maricho-api"
    }

@app.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_probe(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    redis_client: aioredis.Redis = Depends(get_redis_client)
) -> dict[str, Any]:
    """
    Readiness probe to verify downstream dependencies (PostgreSQL, Redis).
    """
    health_status = "UP"
    details: dict[str, Any] = {}

    # 1. Verify PostgreSQL
    try:
        start_time = time.monotonic()
        await db.execute(text("SELECT 1"))
        details["database"] = {
            "status": "UP",
            "latency_ms": round((time.monotonic() - start_time) * 1000, 2)
        }
    except Exception as exc:
        health_status = "DOWN"
        details["database"] = {"status": "DOWN", "error": str(exc)}
        logger.error(f"Readiness database error: {exc}", exc_info=True)

    # 2. Verify Redis
    try:
        start_time = time.monotonic()
        await redis_client.ping()
        details["redis"] = {
            "status": "UP",
            "latency_ms": round((time.monotonic() - start_time) * 1000, 2)
        }
    except Exception as exc:
        health_status = "DOWN"
        details["redis"] = {"status": "DOWN", "error": str(exc)}
        logger.error(f"Readiness redis error: {exc}", exc_info=True)

    if health_status == "DOWN":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": health_status,
        "timestamp": time.time(),
        "dependencies": details
    }

@app.get("/ops/dashboard")
async def read_ops_dashboard(
    current_user: Person = Depends(RequireRole([RoleEnum.OPS]))
) -> dict[str, Any]:
    """Protected endpoint requiring OPS role."""
    return {"message": f"Welcome to Ops Dashboard, {current_user.phone}!"}
