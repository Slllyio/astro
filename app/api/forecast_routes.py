"""HTTP endpoints for the multi-day Mundane Forecast + Almanac (Phase 2+).

Mounted at ``/medini/forecast/*`` and ``/medini/almanac/*``. Lives in its
own router file rather than extending ``medini_routes.py`` because the
forecast composes several optional enrichment layers (severity, domains,
RAG citations, daily summary) and the route surface warrants a focused
module.

Endpoints:

* GET /medini/forecast            — forward N-day calendar (default 30)
* GET /medini/forecast/page       — HTML calendar UI (forward)
* GET /medini/forecast/domains    — mundane-domain dictionary (tooltips)
* GET /medini/almanac             — BACKWARD N-day view ("what just happened")
* GET /medini/almanac/page        — HTML calendar UI (backward)

Forecast and almanac share the same engine — almanac just sets
``jd_start = now - days_back`` and uses the same enrichments. Citations are
off by default on both because they trigger the ~3s RAG model load on the
first request.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.llm.client import OllamaClient
from app.medini.forecast import DEFAULT_HORIZON_DAYS, multi_day_forecast
from app.medini.forecast_cache import get_daily_summary_cache
from app.medini.forecast_citations import annotate_events as annotate_citations
from app.medini.forecast_daily_summary import annotate_by_day as annotate_daily_summaries
from app.medini.forecast_domains import DOMAINS, annotate_events as annotate_domains
from app.medini.forecast_event_text import annotate_events as annotate_event_texts
from app.medini.forecast_event_text import get_event_text_cache
from app.medini.forecast_severity import annotate_events as annotate_severity

logger = logging.getLogger(__name__)

forecast_router = APIRouter(
    prefix="/medini/forecast",
    tags=["Mundane Forecast (Phase 2)"],
)
almanac_router = APIRouter(
    prefix="/medini/almanac",
    tags=["Mundane Almanac (Phase 2)"],
)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "medini" / "templates"


def _deep_client_or(fast_client: OllamaClient | None) -> OllamaClient | None:
    """Build the 'deep' LLM client (slower, smarter) for event_text.

    Falls through to ``fast_client`` when ``OLLAMA_MODEL_DEEP`` is empty
    (the default) so a single-model deployment keeps working without
    config changes. Uses a longer timeout because deep models like
    gemma4:31b can take 30-60s per synthesis.
    """
    if fast_client is None:
        return None
    deep_model = settings.OLLAMA_MODEL_DEEP.strip()
    if not deep_model or deep_model == settings.OLLAMA_MODEL:
        return fast_client
    return OllamaClient(
        host=settings.OLLAMA_HOST,
        model=deep_model,
        timeout_seconds=settings.OLLAMA_DEEP_TIMEOUT_SECONDS,
    )


# Cap horizon to avoid expensive ephemeris scans bringing the event loop down
# (a 365-day scan = 365 * 9 planet positions for ingress + the same for
# station + (9 choose 2)=36 pair scans = ~10k swe.calc_ut calls). 90 days
# is generous for mundane "this season" planning without abusive cost.
_MAX_HORIZON_DAYS = 90


@forecast_router.get("/cache-stats")
async def cache_stats() -> dict:
    """LRU stats for the daily-summary + event-text caches.

    Cheap. Hit rate climbs from 0 on the first request to ~1.0 once a
    horizon has been seen at least once (events are deterministic for a
    given date so the hash-key match is exact)."""
    return {
        "daily_summary": get_daily_summary_cache().stats(),
        "event_text": get_event_text_cache().stats(),
    }


@forecast_router.post("/cache-clear")
async def cache_clear() -> dict:
    """Drop both forecast caches. Used by the UI's 'Force refresh' button
    so a user can re-run the LLM after editing a prompt or swapping models
    without restarting the server. POST (not GET) because this mutates
    server state and shouldn't be cacheable / prefetchable.
    """
    ds = get_daily_summary_cache()
    et = get_event_text_cache()
    ds_size_before = ds.size
    et_size_before = et.size
    ds.clear()
    et.clear()
    return {
        "cleared": True,
        "daily_summary_entries_dropped": ds_size_before,
        "event_text_entries_dropped": et_size_before,
    }


@forecast_router.get("/domains")
async def list_domains() -> dict:
    """Return the mundane-domain catalog for UI tooltips.

    Cheap, no ephemeris work — clients fetch this once on page load to
    populate hover-cards and the domain filter chips.
    """
    return {
        "domains": [
            {
                "key": d.key, "label": d.label,
                "icon": d.icon, "description": d.description,
            }
            for d in DOMAINS.values()
        ],
        "count": len(DOMAINS),
    }


@forecast_router.get("")
async def forecast(
    jd: float | None = Query(
        None, description="Start JD (UT). Default = now in UT.",
    ),
    horizon_days: int = Query(
        DEFAULT_HORIZON_DAYS, ge=1, le=_MAX_HORIZON_DAYS,
        description="How far forward to scan (1-90 days).",
    ),
    conjunction_orb: float = Query(2.0, ge=0.1, le=10.0),
    include_severity: bool = Query(True),
    include_domains: bool = Query(True),
    include_citations: bool = Query(
        False,
        description="Attach RAG doctrine citations per event. Costs ~3s "
                    "on first call (model warm-up); off by default.",
    ),
    include_daily_summary: bool = Query(
        False,
        description="Generate a prose synthesis per day (LLM when "
                    "OLLAMA_ENABLED, deterministic template otherwise).",
    ),
    include_event_text: bool = Query(
        False,
        description="LLM-synthesize a per-event interpretation from its "
                    "RAG citations. Requires include_citations=true AND "
                    "OLLAMA_ENABLED=true; silent no-op otherwise.",
    ),
) -> dict:
    """Multi-day mundane forecast with optional severity + domain + citation layers.

    Layering is **additive and order-preserving**: severity first (smallest
    payload), domains next, citations last (most expensive). Each layer
    can be turned off independently so the page can fetch a fast view
    initially and re-fetch with citations on demand.
    """
    def _compute_sync() -> dict:
        payload = multi_day_forecast(
            jd_start=jd, horizon_days=horizon_days,
            conjunction_orb=conjunction_orb,
        )
        events = payload["events"]
        if include_severity:
            events = annotate_severity(events)
        if include_domains:
            events = annotate_domains(events)
        if include_citations:
            events = annotate_citations(events)
        payload["events"] = events

        # Rebuild by_day so the calendar groups receive the enriched events
        # (we don't want to leave by_day pointing at the pre-enrichment list)
        by_day: dict[str, list] = {}
        for e in events:
            by_day.setdefault(e["date_utc"], []).append(e)
        payload["by_day"] = by_day

        # Top-N severity events surface a "headlines" strip in the UI
        if include_severity:
            payload["top_events"] = sorted(
                events,
                key=lambda e: (-(e.get("severity") or 0), e["jd"]),
            )[:5]

        # LLM clients. The "fast" client is used by the daily-summary
        # layer (called once per distinct day, latency-sensitive). The
        # "deep" client is used by event_text (called less often, benefits
        # from better reasoning across multi-source citations). When
        # OLLAMA_MODEL_DEEP is empty, deep === fast (same instance).
        llm_client = (
            OllamaClient(
                host=settings.OLLAMA_HOST,
                model=settings.OLLAMA_MODEL,
                timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
            )
            if settings.OLLAMA_ENABLED else None
        )
        deep_client = _deep_client_or(llm_client)

        if include_event_text and include_citations:
            events = annotate_event_texts(events, client=deep_client)
            payload["events"] = events
            by_day_2: dict[str, list] = {}
            for e in events:
                by_day_2.setdefault(e["date_utc"], []).append(e)
            payload["by_day"] = by_day_2

        if include_daily_summary:
            payload["daily_summaries"] = annotate_daily_summaries(
                payload["by_day"], client=llm_client,
            )

        payload["layers_applied"] = {
            "severity": include_severity,
            "domains": include_domains,
            "citations": include_citations,
            "daily_summary": include_daily_summary,
            "event_text": include_event_text and include_citations,
        }
        return payload

    # Scans are sync CPU-bound (lots of swe.calc_ut). Offload so the event
    # loop stays responsive when several clients hit the endpoint at once.
    try:
        return await asyncio.to_thread(_compute_sync)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@forecast_router.get("/page", response_class=HTMLResponse)
async def forecast_page() -> HTMLResponse:
    """Mundane forecast calendar UI — calls /medini/forecast asynchronously."""
    html_path = _TEMPLATES_DIR / "forecast.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Almanac: backward-looking ("what just happened")                              #
# --------------------------------------------------------------------------- #
# Same engine, jd_start = now - days_back. Useful for journaling: "the last
# 30 days had this Jupiter ingress and that Mars-Saturn alignment". Re-uses
# the entire enrichment stack (severity, domains, citations, daily summary).


@almanac_router.get("")
async def almanac(
    days_back: int = Query(
        30, ge=1, le=_MAX_HORIZON_DAYS,
        description="How far backward from now (1-90 days).",
    ),
    conjunction_orb: float = Query(2.0, ge=0.1, le=10.0),
    include_severity: bool = Query(True),
    include_domains: bool = Query(True),
    include_citations: bool = Query(False),
    include_daily_summary: bool = Query(False),
    include_event_text: bool = Query(False),
) -> dict:
    """Past N days of mundane events with the same enrichments as /forecast.

    No ``jd`` param — almanac always anchors to "now" and walks backward.
    For a fixed-window historical view, hit /forecast with a backdated
    ``jd`` instead.
    """
    from app.medini.forecast import current_jd_ut

    jd_now = current_jd_ut()
    jd_start = jd_now - days_back

    def _compute_sync() -> dict:
        payload = multi_day_forecast(
            jd_start=jd_start, horizon_days=days_back,
            conjunction_orb=conjunction_orb,
        )
        events = payload["events"]
        if include_severity:
            events = annotate_severity(events)
        if include_domains:
            events = annotate_domains(events)
        if include_citations:
            events = annotate_citations(events)
        payload["events"] = events
        by_day: dict[str, list] = {}
        for e in events:
            by_day.setdefault(e["date_utc"], []).append(e)
        payload["by_day"] = by_day

        if include_severity:
            payload["top_events"] = sorted(
                events,
                key=lambda e: (-(e.get("severity") or 0), -e["jd"]),  # newest-first tiebreak
            )[:5]

        llm_client = (
            OllamaClient(
                host=settings.OLLAMA_HOST,
                model=settings.OLLAMA_MODEL,
                timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
            )
            if settings.OLLAMA_ENABLED else None
        )
        deep_client = _deep_client_or(llm_client)

        if include_event_text and include_citations:
            events = annotate_event_texts(events, client=deep_client)
            payload["events"] = events
            by_day_2: dict[str, list] = {}
            for e in events:
                by_day_2.setdefault(e["date_utc"], []).append(e)
            payload["by_day"] = by_day_2

        if include_daily_summary:
            payload["daily_summaries"] = annotate_daily_summaries(
                payload["by_day"], client=llm_client,
            )

        # Almanac-specific framing: rename horizon_days -> days_back so
        # clients can dispatch on the envelope shape.
        payload["days_back"] = payload.pop("horizon_days")
        payload["direction"] = "backward"
        payload["layers_applied"] = {
            "severity": include_severity,
            "domains": include_domains,
            "citations": include_citations,
            "daily_summary": include_daily_summary,
            "event_text": include_event_text and include_citations,
        }
        return payload

    try:
        return await asyncio.to_thread(_compute_sync)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@almanac_router.get("/page", response_class=HTMLResponse)
async def almanac_page() -> HTMLResponse:
    """Almanac calendar UI — same shape as /forecast but with reversed
    time direction (newest day first in the calendar)."""
    html_path = _TEMPLATES_DIR / "almanac.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Almanac template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
