"""Slim FastAPI entry point that serves ONLY the V1.5 reading UI.

This is what the Android app's backend deployment (`Dockerfile`) runs. It mounts
just the reading engine's web routes — not the auth / RAG / mundane-forecast
routers that ``app.main`` also includes — so the container needs only the
reading engine and its dependencies. Everything the reading needs is
self-contained in ``app.api.reading_v15_routes`` (its own ``Jinja2Templates``);
no app-level static mount is required (the page inlines its CSS/JS and pulls
Bootstrap from a CDN).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.reading_v15_routes import router as reading_v15_router

app = FastAPI(title="Kundli — Jyotish Reading", docs_url=None, redoc_url=None)
app.include_router(reading_v15_router)


@app.get("/")
def _root() -> RedirectResponse:
    """Send the bare domain to the chart-entry form."""
    return RedirectResponse(url="/reading/v15/")


@app.get("/healthz")
def _health() -> dict[str, str]:
    return {"status": "ok"}
