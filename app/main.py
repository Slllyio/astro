"""FastAPI app entrypoint with daemon lifespan, auth, and rate limiting."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth_routes import auth_router
from app.api.forecast_routes import almanac_router, forecast_router
from app.api.interpret_routes import interpret_router
from app.api.knowledge_routes import knowledge_router
from app.api.medini_routes import medini_router
from app.api.reading_routes import reading_router
from app.api.rectification_routes import rectification_router
from app.api.routes import chart_router, profile_router
from app.api.soul_routes import soul_router
from app.api.varga_routes import varga_router
from app.core.auth import limiter
from app.core.config import settings
from app.core.database import init_db
from app.daemon.transit_worker import NadiTransitDaemon

# App-level templates (the unified shell). Module-level Path resolution so the
# location is stable regardless of where uvicorn is launched.
_APP_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

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
app.include_router(medini_router)  # Tab 3: Geo-Astrological Engine (/medini/*)
app.include_router(knowledge_router)  # RAG search over doctrine corpus (/medini/knowledge/*)
app.include_router(forecast_router)  # Phase 2: multi-day Mundane Forecast (/medini/forecast/*)
app.include_router(almanac_router)   # Phase 2: backward-looking Mundane Almanac (/medini/almanac/*)
app.include_router(reading_router)   # Round 10: per-chart RAG-grounded reader (/medini/reading/*)
app.include_router(interpret_router)  # LLM narrative layer (/interpret/*)
app.include_router(rectification_router)  # Birth-time rectification / discovery (/rectify/*)
app.include_router(varga_router)  # Shodasavarga 16-divisional-chart reading (/vargas/*)
app.include_router(soul_router)  # EXPERIMENT: soul-destiny reading (/soul/*) — Jaimini firewall lifted


# Mount static assets at /static/ — serves the Pothi manuscript design
# system (CSS, JS) and any vendored libraries (AstroChart). Required for
# the manuscript-themed templates that reference /static/css/manuscript.css
# and /static/js/manuscript.js. Resolved relative to this module so uvicorn
# can be launched from anywhere without breaking the asset path.
app.mount(
    "/static",
    StaticFiles(directory=_APP_TEMPLATES_DIR / "static"),
    name="static",
)


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


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Unified-tabs shell. Single-page wrapper around the three tabs (Nadi /
    NumeroAstro / Medini) — uses an iframe content area driven by URL hash
    so each existing surface (Medini map pages, Flask portal) keeps its own
    state without rewiring."""
    html_path = _APP_TEMPLATES_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Shell template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
