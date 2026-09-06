from fastapi import FastAPI, status, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
import time

from app.telemetry import setup_telemetry, logger
from app.database import get_db_session
from app.redis import get_redis_client

app = FastAPI(title="Maricho Backend API")

# Initialize telemetry
setup_telemetry(app, "maricho-api")

@app.get("/health/live", status_code=status.HTTP_200_OK)
def liveness_probe():
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
):
    """
    Readiness probe to verify downstream dependencies (PostgreSQL, Redis).
    """
    health_status = "UP"
    details = {}
    
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

from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token, get_current_user, RequireRole
from app.models import Person, RoleEnum
from sqlalchemy import select

@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Mock login endpoint for development. 
    In production, this would use WhatsApp OTP verification.
    """
    stmt = select(Person).where(Person.phone == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        # Create a mock user for testing if they don't exist
        user = Person(phone=form_data.username, role=RoleEnum.BUYER)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    access_token = create_access_token(data={"sub": user.phone})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: Person = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "phone": current_user.phone,
        "role": current_user.role
    }

@app.get("/ops/dashboard")
async def read_ops_dashboard(
    current_user: Person = Depends(RequireRole([RoleEnum.OPS]))
):
    """Protected endpoint requiring OPS role."""
    return {"message": f"Welcome to Ops Dashboard, {current_user.phone}!"}
