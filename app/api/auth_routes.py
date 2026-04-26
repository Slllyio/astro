"""Authentication endpoints: Google OAuth login flow + /auth/me.

The callback returns a JSON token rather than redirecting to a frontend
because the project is API-first with no UI yet. When a frontend ships,
the callback will instead redirect to FRONTEND_URL with the token in a
URL fragment or HTTP-only cookie.
"""
from __future__ import annotations

import datetime as dt
import logging

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentAccount, issue_access_token, oauth
from app.core.config import settings
from app.core.database import get_db
from app.models.domain import Account
from app.models.schemas import AccountResponse, TokenResponse

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


def _google_oauth_configured() -> bool:
    """True if Google credentials are populated in settings (and thus
    `oauth.google` was registered in app.core.auth)."""
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


@auth_router.get("/google/login")
async def google_login(request: Request):
    """Kick off Google OAuth: redirect the browser to Google's consent screen.

    Authlib stores the state and PKCE verifier in the session cookie set by
    SessionMiddleware so they survive the round-trip to Google.
    """
    if not _google_oauth_configured():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured (set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)",
        )
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@auth_router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Handle Google's redirect: exchange code for token, fetch userinfo,
    upsert the Account, and issue our own JWT.

    redirect_uri_mismatch from Google means the URI configured here doesn't
    match what's registered in Google Cloud Console for this OAuth client.
    The fix is to add `GOOGLE_REDIRECT_URI` to the client's authorized
    redirect URIs in Console (or create a Web Application client type).
    """
    if not _google_oauth_configured():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured",
        )
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        logger.warning("Google OAuth exchange failed: %s", exc)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth handshake failed: {exc.error}",
        ) from exc

    # OIDC userinfo lives inside the id_token Authlib decodes for us.
    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("sub"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Google response missing userinfo / sub claim",
        )

    google_sub: str = userinfo["sub"]
    email: str = userinfo.get("email", "")
    name: str | None = userinfo.get("name")
    picture: str | None = userinfo.get("picture")

    account = await _upsert_account(
        db=db,
        google_sub=google_sub,
        email=email,
        name=name,
        picture=picture,
    )

    jwt_token = issue_access_token(account.id, account.email)
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        account=AccountResponse.model_validate(account),
    )


@auth_router.get("/me", response_model=AccountResponse)
async def get_me(account: CurrentAccount) -> Account:
    """Return the authenticated account. Auth-gated by CurrentAccount dep."""
    return account


# ---------- internal helpers ----------

async def _upsert_account(
    db: AsyncSession,
    google_sub: str,
    email: str,
    name: str | None,
    picture: str | None,
) -> Account:
    """Look up by google_sub (stable identity); update on hit, insert on miss."""
    existing = (
        await db.execute(select(Account).where(Account.google_sub == google_sub))
    ).scalar_one_or_none()

    now = dt.datetime.now(dt.timezone.utc)
    if existing is not None:
        existing.email = email
        existing.name = name
        existing.picture = picture
        existing.last_login_at = now
        await db.commit()
        await db.refresh(existing)
        return existing

    account = Account(
        google_sub=google_sub,
        email=email,
        name=name,
        picture=picture,
        last_login_at=now,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account
