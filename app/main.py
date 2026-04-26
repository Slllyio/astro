"""FastAPI app entrypoint with daemon lifespan."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routes import chart_router, profile_router
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
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(chart_router, prefix="/chart", tags=["Astrology Engine"])
app.include_router(profile_router, tags=["Profiles & Transits"])


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to the Vedic & Nadi Astrology Engine"}
