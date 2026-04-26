"""Authentication core: JWT issuance/verification, OAuth client, current-account dependency.

The OAuth client is built lazily so the app can boot in environments (CI,
tests) where Google credentials aren't configured. The /auth/google/* routes
fail loudly if hit without credentials; everything else still works.
"""
from __future__ import annotations

import datetime as dt
from typing import Annotated

import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.domain import Account


_bearer = HTTPBearer(auto_error=True)


# ---------- JWT issuance / verification ----------

def issue_access_token(account_id: int, email: str) -> str:
    """Sign a JWT for an authenticated account. Subject is the account id (str)."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(account_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(seconds=settings.JWT_TTL_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Verify signature + expiry. Raises HTTPException(401) on any failure."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


# ---------- FastAPI dependency: resolve Account from Bearer ----------

async def get_current_account(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: AsyncSession = Depends(get_db),
) -> Account:
    payload = decode_access_token(credentials.credentials)
    account_id_str = payload.get("sub")
    if not account_id_str:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
    try:
        account_id = int(account_id_str)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from None

    account = await db.get(Account, account_id)
    if account is None:
        # Token references an account that no longer exists (deleted, rotated DB, etc.)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Account not found")
    return account


CurrentAccount = Annotated[Account, Depends(get_current_account)]


# ---------- slowapi key function: per-account when authed, per-IP otherwise ----------

def rate_limit_account_key(request: Request) -> str:
    """slowapi key_func that buckets authenticated requests by account_id and
    falls back to client IP for unauthenticated calls. Decodes the JWT inline
    (HMAC verify, no DB hit) so it can run before FastAPI's Depends layer.
    A tampered/expired token silently degrades to per-IP rather than raising,
    because raising from a key_func crashes slowapi's middleware path."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            sub = payload.get("sub")
            if sub:
                return f"account:{sub}"
        except jwt.InvalidTokenError:
            pass
    return f"ip:{get_remote_address(request)}"


# Single shared Limiter instance. Imported by main.py (for app.state +
# error handler wiring) and by route modules (for @limiter.limit decorators).
# Defined here so route files can import it without creating a circular dep
# through main.py.
limiter = Limiter(key_func=rate_limit_account_key)


# ---------- Google OAuth client (lazy; works without credentials in tests) ----------

oauth = OAuth()
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        # Discovery URL handles all of Google's endpoint URLs and JWKS for
        # ID-token verification. Avoids hand-coding token_url, authorize_url, etc.
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
