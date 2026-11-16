"""Framework-level JWT primitives only — zero domain knowledge.

Deliberately does not know about `Person`/roles/the database: resolving a
token's subject into a real domain identity, and role-gating, are the
`accounts` app's concern (`apps/accounts/interface_adapters/dependencies.py`),
which every other app's router imports from. Keeping this module free of
domain imports is what lets `core` sit "under" every app without ever
depending on one — see ADR-007.
"""

import os
from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-maricho-key-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")

# Not passlib: passlib's bcrypt backend self-test trips over bcrypt>=4's
# strict 72-byte enforcement (bcrypt pre-4 used to silently truncate), and
# passlib is no longer maintained to fix it. SignUpIn/SignInIn already cap
# the password at 72 bytes, matching bcrypt's own hard limit.


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError (or a subclass) on any decode failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
