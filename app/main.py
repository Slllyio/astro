"""FastAPI app entrypoint with daemon lifespan, auth, and rate limiting."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth_routes import auth_router
from app.api.routes import chart_router, profile_router
from app.core.auth import limiter
from app.core.config import settings
from app.core.database import init_db
from app.daemon.transit_worker import NadiTransitDaemon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_db()

    daemon: NadiTransitDaemon | None = None
    daemon_task: asyncio.Task | None = None
    if settings.DAEMON_ENABLED:
        daemon = NadiTransitDaemon()
        daemon_task = asyncio.create_task(daemon.start(), name="nadi-transit-daemon")

    try:
        yield
    finally:
        if daemon is not None and daemon_task is not None:
            daemon.stop()
            try:
                await asyncio.wait_for(daemon_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Daemon did not stop within 5s; cancelling")
                daemon_task.cancel()
                try:
                    await daemon_task
                except (asyncio.CancelledError, Exception):
                    pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-fidelity Vedic and Nadi astrology application API",
    version="0.3.0",
    lifespan=lifespan,
)

# Authlib's OAuth client stores the CSRF state and PKCE verifier in a signed
# session cookie across the redirect to Google. SessionMiddleware is the
# Starlette primitive that backs that cookie. Reuses SECRET_KEY for signing.
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Rate-limit plumbing: register the limiter on app.state so @limiter.limit
# decorators on routes can find it, and install slowapi's 429 error handler.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router)
app.include_router(chart_router, prefix="/chart", tags=["Astrology Engine"])
app.include_router(profile_router, tags=["Profiles & Transits"])


# Vendored Flask portal at /portal/. Lazy-imported so tests/CI (with
# PORTAL_ENABLED=false) don't pay the skyfield ephemeris-load cost.
# The portal is the original astro-web-portal "probability engine" — a
# DOB-only matrix-based reader complementing this app's precise natal-chart
# engine. See `portal/app.py` for its routes.
if settings.PORTAL_ENABLED:
    from starlette.middleware.wsgi import WSGIMiddleware
    from portal.app import app as _portal_flask_app  # heavy import: ephemeris
    app.mount("/portal", WSGIMiddleware(_portal_flask_app))
    logger.info("Vendored Flask portal mounted at /portal/")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to the Vedic & Nadi Astrology Engine"}
