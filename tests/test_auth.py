"""Auth coverage: JWT round-trip, 401 paths, IDOR, OAuth-not-configured, upsert."""
from __future__ import annotations

import datetime as dt

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.auth import decode_access_token, issue_access_token
from app.core.config import settings
from app.models.domain import Account

from _helpers import sample_profile_payload  # tests/ on sys.path via pyproject


# ---------- JWT round-trip / decode failure modes ----------

def test_jwt_round_trip() -> None:
    token = issue_access_token(account_id=42, email="alice@example.com")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["email"] == "alice@example.com"
    assert payload["exp"] > payload["iat"]


def test_decode_expired_token_raises_401() -> None:
    """A token whose `exp` is in the past must be rejected, even if the signature checks out."""
    past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)
    expired = jwt.encode(
        {"sub": "1", "email": "x@y.z", "iat": int(past.timestamp()) - 60,
         "exp": int(past.timestamp())},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(Exception) as exc:
        decode_access_token(expired)
    assert "401" in str(exc.value) or "expired" in str(exc.value).lower()


def test_decode_invalid_signature_raises_401() -> None:
    """A token signed with the wrong secret must be rejected."""
    bad = jwt.encode(
        {"sub": "1", "email": "x@y.z",
         "iat": int(dt.datetime.now(dt.timezone.utc).timestamp()),
         "exp": int(dt.datetime.now(dt.timezone.utc).timestamp()) + 3600},
        "wrong-secret-" + "x" * 32,  # >=32 bytes silences InsecureKeyLengthWarning
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(Exception):
        decode_access_token(bad)


# ---------- /auth/me ----------

async def test_auth_me_returns_account(authed_client: AsyncClient, seeded_account) -> None:
    response = await authed_client.get("/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == seeded_account.id
    assert body["email"] == seeded_account.email
    assert body["name"] == seeded_account.name


async def test_auth_me_401_without_token(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code in (401, 403)  # FastAPI's HTTPBearer auto-error sends 403


async def test_auth_me_401_with_garbage_token(client: AsyncClient) -> None:
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"}
    )
    assert response.status_code == 401


# ---------- Auth required on /profiles routes ----------

async def test_post_profile_401_without_token(client: AsyncClient) -> None:
    response = await client.post("/profiles", json=sample_profile_payload())
    assert response.status_code in (401, 403)


async def test_get_transits_401_without_token(client: AsyncClient) -> None:
    response = await client.get("/profiles/1/transits")
    assert response.status_code in (401, 403)


# ---------- IDOR ----------

@pytest_asyncio.fixture
async def second_authed_client(db_engine: AsyncEngine) -> AsyncClient:
    """Second account with its own JWT, used for cross-account IDOR tests."""
    from app.core.database import get_db
    from app.main import app
    sm = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sm() as session:
        account = Account(
            google_sub="other-sub-99999",
            email="other@example.com",
            name="Other User",
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        token = issue_access_token(account.id, account.email)

    async def override_get_db():
        async with sm() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    client = AsyncClient(transport=transport, base_url="http://test", headers=headers)
    yield client
    await client.aclose()
    app.dependency_overrides.clear()


async def test_idor_cross_account_returns_404(
    authed_client: AsyncClient, second_authed_client: AsyncClient
) -> None:
    """Account A creates a profile; Account B asking for Account A's transits
    must get 404 (not 403, to avoid leaking existence of other accounts' profiles).
    """
    # Account A creates profile.
    create_resp = await authed_client.post("/profiles", json=sample_profile_payload())
    assert create_resp.status_code == 201
    user_id_a = create_resp.json()["id"]

    # Account B tries to read Account A's transits.
    response = await second_authed_client.get(f"/profiles/{user_id_a}/transits")
    assert response.status_code == 404, (
        "expected 404 to avoid leaking that the profile exists across accounts"
    )


# ---------- OAuth-not-configured fail-fast ----------

async def test_oauth_login_503_when_credentials_blank(client: AsyncClient) -> None:
    """In test/CI environments GOOGLE_CLIENT_ID/SECRET are blank.
    /auth/google/login must short-circuit to 503 instead of redirecting."""
    response = await client.get("/auth/google/login", follow_redirects=False)
    assert response.status_code == 503


async def test_oauth_callback_503_when_credentials_blank(client: AsyncClient) -> None:
    response = await client.get("/auth/google/callback?code=fake&state=fake")
    assert response.status_code == 503


# ---------- _upsert_account behavior ----------

async def test_upsert_account_creates_then_updates(db_session: AsyncSession) -> None:
    """First call inserts; second call with same google_sub updates email/name/last_login."""
    from app.api.auth_routes import _upsert_account

    initial = await _upsert_account(
        db_session,
        google_sub="upsert-sub",
        email="initial@example.com",
        name="Initial Name",
        picture=None,
    )
    initial_id = initial.id
    initial_last_login = initial.last_login_at

    # Second call: email and name changed (e.g., user updated their Google profile).
    updated = await _upsert_account(
        db_session,
        google_sub="upsert-sub",
        email="changed@example.com",
        name="Changed Name",
        picture="https://example.com/pic.jpg",
    )

    assert updated.id == initial_id, "same google_sub must reuse the same row"
    assert updated.email == "changed@example.com"
    assert updated.name == "Changed Name"
    assert updated.picture == "https://example.com/pic.jpg"
    assert updated.last_login_at >= initial_last_login

    # Confirm only one row exists.
    rows = (await db_session.execute(
        select(Account).where(Account.google_sub == "upsert-sub")
    )).scalars().all()
    assert len(rows) == 1
