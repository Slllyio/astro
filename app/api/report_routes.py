"""HTTP endpoint for the full detailed reading (`app.raman_saab.detailed_report`).

Wraps ``build_detailed_report`` — the whole engine's answer for one chart: every contracted
section (Chart signature, Ruler of the nativity, House-by-house with per-house Conclusions,
the strength cross-check, Preponderance of testimonies, Longevity, the Life-narrative and its
companions, the Life-chapters, Gochara, the divisional deep-reads, Soul & destiny, Pitru
dosha, Integrated insights and the Nichod capstone), rendered as Markdown or a standalone HTML
document, plus a compact structured ``summary`` of the highest-signal synthesis fields.

DOCTRINE NOTE (surfaced to callers): the reading answers "what would Raman say", faithfully to
his texts — it is NOT a validated predictor of a life. The population-calibration overlay
(EMPIRICAL_ASTRODATABANK) discloses each reading's information content, never a real-outcome
claim; see the report's own "Information content" and "Measured Truth" framing.

Endpoints:
    POST /report            JSON birth (+ format, window) -> the full reading + summary.
    GET  /report/sections   the section contract (id, heading, since-version) — what a report
                            contains, in document order.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (
    SECTION_CONTRACT,
    build_detailed_report,
    to_markdown,
)
from app.raman_saab.doctrine import sources
from app.raman_saab.report_html import standalone_html
from app.raman_saab.report_json import to_report_dict

logger = logging.getLogger(__name__)

report_router = APIRouter(prefix="/report", tags=["Detailed Reading"])

_SUPPORTED_AYANAMSAS: tuple[str, ...] = ("raman", "lahiri")
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "medini" / "templates"


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    year: int = Field(..., ge=1800, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    tz_offset: float = Field(..., ge=-12.0, le=14.0)
    name: str = Field("api", max_length=120)
    ayanamsa: Literal["raman", "lahiri"] = "lahiri"
    fmt: Literal["markdown", "html", "json"] = Field("markdown", alias="format")
    years_back: int = Field(10, ge=0, le=120)
    years_forward: int = Field(20, ge=0, le=120)


def _summary(r) -> dict:
    """The highest-signal synthesis fields, all JSON-primitive — structured hooks for callers
    who do not want to parse the rendered prose. Every value is read, never re-judged."""
    ru, pr = r.ruler, r.preponderance
    return {
        "lagna": r.synthesis.lagna,
        "ruler_of_nativity": {
            "lagna_lord": ru.lagna_lord,
            "strongest_planet": ru.strongest,
            "strongest_rupas": (round(ru.strongest_rupas, 2)
                                if ru.strongest_rupas is not None else None),
            "coincide": ru.coincide,
        },
        "longevity": {"class": r.longevity_class, "years": r.longevity_years},
        "running_period": {"md": r.synthesis.running_md, "ad": r.synthesis.running_ad},
        "preponderance": {
            "most_corroborated_favourable": pr.most_corroborated_favourable,
            "most_corroborated_afflicted": pr.most_corroborated_afflicted,
            "most_contested": pr.most_contested,
        },
        "plain_opening": r.plain_reading.opening,
        "essence": r.nichod.essence,
    }


@report_router.get("/sections")
async def sections() -> dict:
    """The report's section contract in document order — each section's id, its Markdown
    heading (None for HTML-only sections), and the version that introduced it. Mirrors
    ``detailed_report.SECTION_CONTRACT`` (the append-only template ratchet)."""
    return {
        "count": len(SECTION_CONTRACT),
        "sections": [
            {"id": s.section_id, "heading": s.md_marker, "since": s.since}
            for s in SECTION_CONTRACT
        ],
    }


@report_router.get("/page", response_class=HTMLResponse)
async def report_page() -> HTMLResponse:
    """The interactive detailed-reading page: a birth form that POSTs to /report?format=json
    and renders the structured report client-side with per-section drill-down and
    click-any-citation-to-source."""
    html_path = _TEMPLATES_DIR / "report.html"
    if not html_path.exists():
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Report template missing at {html_path}")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@report_router.get("/source")
async def source(cite: str, context: int = 0) -> dict:
    """The verbatim source lines a citation token points to — the click-to-source backend.

    `cite` is a citation token as it appears in the report (e.g. ``HTJAH-I:468-478``,
    ``3HC:7289``, ``GBB-9:32-34``). Returns the exact lines from the corpus. CLASSICAL_NONCITABLE
    works (BPHS / Praśna Mārga) are deliberately NOT resolved (the divergence firewall) — they
    return ``resolved: false`` with a truthful note, not the verse text."""
    if not 0 <= context <= 20:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="context must be 0..20")
    p = sources.passage(cite, context=context)
    if p is None:
        return {"cite": cite, "resolved": False,
                "note": "This citation is outside Raman's citable canon (classical "
                        "corroboration such as BPHS or Praśna Mārga), or the token is "
                        "malformed / not vendored on this machine — the verse text is not "
                        "shown here."}
    return {"cite": cite, "resolved": True, **p}


@report_router.post("")
async def post_report(req: ReportRequest) -> dict:
    """Cast the nativity and return its full detailed reading in the requested format, plus a
    compact structured summary. The build (ephemeris + full composition) is offloaded to a
    worker thread."""
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail=f"unsupported ayanamsa {req.ayanamsa!r}; "
                                   f"use one of {_SUPPORTED_AYANAMSAS}")

    def _build() -> dict:
        birth = BirthData(name=req.name, year=req.year, month=req.month, day=req.day,
                          hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                          latitude=req.latitude, longitude=req.longitude)
        r = build_detailed_report(birth, ayanamsa=req.ayanamsa,
                                  years_back=req.years_back, years_forward=req.years_forward)
        out: dict = {"ayanamsa": req.ayanamsa, "format": req.fmt, "summary": _summary(r)}
        if req.fmt == "json":
            out["report"] = to_report_dict(r)           # the structured grounding contract
        else:
            out["report"] = standalone_html(r) if req.fmt == "html" else to_markdown(r)
        return out

    try:
        return await asyncio.to_thread(_build)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("detailed reading failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"detailed reading failed: {exc}") from exc


# ── grounded LLM explainer + Q&A (Phase 3) ──────────────────────────────────────

_HONESTY_NOTE = ("This is a plain-language explanation of what the engine computed — it answers "
                 "'what would Raman say', faithfully to his texts, and is NOT a validated "
                 "prediction about a life.")


class ExplainRequest(ReportRequest):
    scope: str = Field("summary", description="'summary', 'house:5', or 'section:<key>'")


class AskRequest(ReportRequest):
    question: str = Field(..., min_length=1, max_length=500)
    scope: str = Field("whole", description="evidence scope; 'whole' grounds in the full chart")
    history: list[tuple[str, str]] = Field(default_factory=list, max_length=20)


class InsightsRequest(ReportRequest):
    scope: str = Field("digest", description="fixed to the engine's ranked 'what matters most'")


def _explainer_client():
    """The grounded-explainer LLM client, or None when disabled/unavailable (-> fallback)."""
    from app.core.config import settings
    if not settings.REPORT_LLM_ENABLED:
        return None
    from app.llm.client import AnthropicClient, AnthropicUnavailable
    from app.llm.report_explainer import EXPLAINER_SYSTEM
    try:
        return AnthropicClient(system=EXPLAINER_SYSTEM)
    except AnthropicUnavailable:
        return None


def _critic_client():
    """The honesty-tuned adversarial critic client (own system prompt), or None when the critic is
    disabled / the LLM is unavailable — in which case the explainer runs without a critique pass."""
    from app.core.config import settings
    if not (settings.REPORT_LLM_ENABLED and settings.REPORT_LLM_CRITIC_ENABLED):
        return None
    from app.llm.client import AnthropicClient, AnthropicUnavailable
    from app.llm.report_explainer import CRITIC_SYSTEM
    try:
        return AnthropicClient(system=CRITIC_SYSTEM)
    except AnthropicUnavailable:
        return None


def _fallback_answer(r, scope: str) -> dict:
    """Deterministic, truthful fallback when the LLM is disabled/unavailable — the report's own
    plain prose for the scope, never an invented explanation."""
    from app.raman_saab.report_json import to_report_dict
    R = to_report_dict(r)
    if scope == "digest":
        dg = R.get("digest", {}) or {}
        lines = [dg.get("headline", "")]
        lines += [f"{it['title']}. {it['detail']}" for it in dg.get("items", [])]
        text = "\n\n".join(filter(None, lines))
    elif scope == "summary" or scope.startswith("section:plain"):
        pr = R["plain_reading"]
        text = " ".join(filter(None, [pr.get("opening"), pr.get("now"), pr.get("notable")]))
    elif scope.startswith("house:"):
        h = int(scope.split(":", 1)[1])
        pf = next((p for p in R["proformas"] if p["house"] == h), None)
        text = (f"House {h} reads {pf['rollup']} (lord {pf['lord']}); "
                + ", ".join(f"{s['signification']} {s['verdict']}" for s in pf["significations"])
                + ".") if pf else "The engine does not compute that."
    else:
        text = R["nichod"].get("essence", "")
    return {"text": text, "source": "fallback", "grounding_ratio": 1.0,
            "anchors_used": [], "forbidden_moves": [], "honesty_note": _HONESTY_NOTE,
            "note": "The grounded LLM explainer is disabled or unavailable; this is the "
                    "engine's own deterministic plain-language text for this scope."}


async def _grounded(req, question: Optional[str]) -> dict:
    from app.core.config import settings
    from app.llm.client import AnthropicUnavailable
    from app.llm.report_explainer import (
        build_evidence,
        explain,
        explain_with_critic,
        refusal_reason,
    )

    def _work() -> dict:
        birth = BirthData(name=req.name, year=req.year, month=req.month, day=req.day,
                          hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                          latitude=req.latitude, longitude=req.longitude)
        r = build_detailed_report(birth, ayanamsa=req.ayanamsa,
                                  years_back=req.years_back, years_forward=req.years_forward)
        scope = getattr(req, "scope", "summary")
        client = _explainer_client()
        if client is None:
            return _fallback_answer(r, scope)
        ev = build_evidence(to_report_dict(r), scope)
        # sanitize client-supplied history: only 'user'/'assistant' turns, never a forged
        # 'system' line — the client controls both role and text (prompt-injection defence).
        hist = tuple((role, text) for role, text in getattr(req, "history", [])
                     if role in ("user", "assistant"))
        critic = _critic_client()                 # None unless the critic flag is on + LLM available
        try:
            if critic is not None:
                ans = explain_with_critic(ev, question, client, history=hist, critic_client=critic)
            else:
                ans = explain(ev, question, client, history=hist)
        except (AnthropicUnavailable, Exception):  # noqa: BLE001 — any LLM failure -> fallback
            logger.warning("explainer LLM failed; serving deterministic fallback")
            return _fallback_answer(r, scope)
        # REFUSE (serve the deterministic fallback, discard the LLM text) on ANY hard guard —
        # a misbehaving or prompt-injected model must never reach the user as Raman's ruling.
        reason = refusal_reason(ans, settings.REPORT_LLM_GROUNDING_MIN)
        if reason is not None:
            logger.warning("explainer answer refused (%s); serving deterministic fallback", reason)
            fb = _fallback_answer(r, scope)
            fb["refused_llm"] = True
            fb["refusal_reason"] = reason
            return fb
        return {"text": ans.text, "source": ans.source, "model": ans.model,
                "grounding_ratio": ans.grounding_ratio, "anchors_used": list(ans.anchors_used),
                "honesty_note": _HONESTY_NOTE,
                "evidence": [{"n": f.n, "text": f.text, "cite": f.cite} for f in ev.facts]}

    try:
        return await asyncio.to_thread(_work)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("grounded explainer failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"grounded explainer failed: {exc}") from exc


@report_router.post("/explain")
async def post_explain(req: ExplainRequest) -> dict:
    """A grounded, plain-language explanation of a scope of the report ('summary', 'house:N',
    'section:<key>'). Every factual sentence is anchored to a computed finding; the answer is
    never a new verdict or a prediction. Falls back to the report's own deterministic prose
    when the LLM is disabled/unavailable."""
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unsupported ayanamsa")
    return await _grounded(req, question=None)


@report_router.post("/insights")
async def post_insights(req: InsightsRequest) -> dict:
    """The prioritized whole-chart synthesis — the engine's ranked 'what matters most' narrated in
    plain language, most important first. The RANKING is the engine's (deterministic); the LLM only
    orders and connects it, anchoring every claim and predicting nothing. Falls back to the engine's
    own ranked digest as prose when the LLM is disabled/unavailable."""
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unsupported ayanamsa")
    return await _grounded(req, question=None)


@report_router.post("/ask")
async def post_ask(req: AskRequest) -> dict:
    """A grounded Q&A turn about the chart — answered ONLY from the engine's computed, cited
    findings, deferring ('the engine does not compute that') out of scope, never predicting.
    `history` carries prior turns for multi-turn context (the client holds the conversation)."""
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unsupported ayanamsa")
    return await _grounded(req, question=req.question)
