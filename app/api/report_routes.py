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

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

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
    # Selected once on the birth-details page, carried on every subsequent call (explain,
    # insights, ask, ai-interpret, feedback questions) so the whole session stays in one
    # language. "en" is the only language with full deterministic-report coverage; "hi"
    # covers the UI chrome + every LLM-narrated surface (see PROCESS_AND_METHODOLOGY.md).
    lang: Literal["en", "hi"] = "en"
    # Reading LENGTH — a rendering choice, never a different computation. "full" is the
    # default and stays the default: nothing is hidden unless a reader asks for the gist.
    # "short" re-renders the SAME built report through `short_reading`, so a caller can ask
    # for either without re-casting, and the JSON payload always carries both.
    reading: Literal["full", "short"] = "full"


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
        out: dict = {"ayanamsa": req.ayanamsa, "format": req.fmt,
                     "reading": req.reading, "summary": _summary(r)}
        if req.fmt == "json":
            out["report"] = to_report_dict(r)           # the structured grounding contract
            # chart-specific feedback questions ride along with the JSON report so the
            # frontend never has to re-cast the chart just to ask them (Part E).
            from app.raman_saab.feedback_questions import build_feedback_questions
            out["feedback_questions"] = build_feedback_questions(out["report"], lang=req.lang)
        elif req.reading == "short":
            from app.raman_saab import short_reading as sr_mod
            short = sr_mod.build_short_reading(to_report_dict(r))
            if short is None:
                raise ValueError("this chart is too sparse for a short reading")
            out["report"] = (sr_mod.to_html(short, lang=req.lang, title=req.name)
                             if req.fmt == "html"
                             else sr_mod.to_markdown(short, lang=req.lang))
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


def _make_client(system: str, *, model: str | None = None, timeout: float | None = None):
    """A backend-selected LLM client carrying `system`, or None when unavailable.

    REPORT_LLM_BACKEND decides the provider: "ollama" (default) builds a LOCAL client —
    zero per-call cost, no Anthropic key in the loop — with the system prompt prepended
    per prompt (Ollama's generate API has no system kwarg); "anthropic" restores the
    Claude client. Either way the same refusal_reason guard vets the output downstream.

    `model` overrides `settings.OLLAMA_MODEL` and `timeout` overrides
    `settings.OLLAMA_TIMEOUT_SECONDS` for this one client (both ignored on the anthropic
    backend) — used by `_translation_client` to route Hindi translation through a different,
    more general (and often slower) local model than the narrow fine-tuned analyst.
    """
    from app.core.config import settings
    if settings.REPORT_LLM_BACKEND == "ollama":
        from app.llm.client import OllamaClient, SystemPromptWrapper
        # REPORT_LLM_MODEL (a stock 12B by default) overrides the fast global OLLAMA_MODEL for
        # these narrative surfaces only — see its config comment for the measured comparison.
        # num_ctx/think are required for a large reasoning model to answer at all.
        return SystemPromptWrapper(
            OllamaClient(settings.OLLAMA_HOST,
                         model or settings.REPORT_LLM_MODEL or settings.OLLAMA_MODEL,
                         timeout if timeout is not None
                         else settings.REPORT_LLM_TIMEOUT_SECONDS,
                         num_ctx=settings.REPORT_LLM_NUM_CTX,
                         think=settings.REPORT_LLM_THINK),
            system,
        )
    from app.llm.client import AnthropicClient, AnthropicUnavailable
    try:
        return AnthropicClient(system=system)
    except AnthropicUnavailable:
        return None


def _explainer_client():
    """The grounded-explainer LLM client, or None when disabled/unavailable (-> fallback)."""
    from app.core.config import settings
    if not settings.REPORT_LLM_ENABLED:
        return None
    from app.llm.report_explainer import EXPLAINER_SYSTEM
    return _make_client(EXPLAINER_SYSTEM)


def _translation_client():
    """A client bound to NO system prompt — unlike ``_explainer_client``'s EXPLAINER_SYSTEM,
    the translation instruction lives entirely inside ``translate_to_hindi``'s own prompt text.
    Reusing the explainer's bound client for translation would stack a "write grounded chart
    analysis" system prompt underneath a "translate this to Hindi" instruction; caught live
    2026-07-29 against the real local model: it followed the stronger, fine-tuned-on analysis
    instruction and produced MORE English instead of a translation, one that still happened to
    carry the same [Fact N] markers so the count-based safety net didn't catch it either (see
    ``_looks_like_hindi`` in report_explainer.py for the language-check that now does).

    Even with that fixed, live-testing showed the narrow astro-analyst LoRA (1.5B, fine-tuned
    only on English chart analysis) simply cannot produce Hindi at all — a capability gap, not
    a prompt bug. `OLLAMA_MODEL_TRANSLATE` lets this ONE call use a different, more general
    local model (e.g. a larger stock Ollama model that still handles Hindi well) while the main
    explainer keeps using the fast fine-tuned model for everything else. Empty (default) falls
    through to `OLLAMA_MODEL` — same behavior as before this setting existed. Also uses the
    longer `OLLAMA_TRANSLATE_TIMEOUT_SECONDS` — live-tested 2026-07-29: the default 30s timeout
    clipped a real full-paragraph translation on a larger, slower model mid-generation."""
    from app.core.config import settings
    if not settings.REPORT_LLM_ENABLED:
        return None
    return _make_client("", model=settings.OLLAMA_MODEL_TRANSLATE or None,
                        timeout=settings.OLLAMA_TRANSLATE_TIMEOUT_SECONDS)


def _critic_client():
    """The honesty-tuned adversarial critic client (own system prompt), or None when the critic is
    disabled / the LLM is unavailable — in which case the explainer runs without a critique pass."""
    from app.core.config import settings
    if not (settings.REPORT_LLM_ENABLED and settings.REPORT_LLM_CRITIC_ENABLED):
        return None
    from app.llm.report_explainer import CRITIC_SYSTEM
    return _make_client(CRITIC_SYSTEM)


_PROSE_SLOTS = ("opening", "headline", "sentence", "woven", "narrative", "summary",
                "essence", "frame", "closing", "note", "caveat")


def _section_prose(sec) -> str:
    """The section's own prose, assembled truthfully from whatever shape it has."""
    if sec is None:
        return "The engine does not compute that section for this chart."
    if isinstance(sec, str):
        return sec
    if isinstance(sec, list):
        parts = [_section_prose(x) for x in sec[:12]]
        return "\n".join(p for p in parts if p)
    if isinstance(sec, dict):
        parts = [str(sec[k]) for k in _PROSE_SLOTS if isinstance(sec.get(k), str) and sec[k]]
        if parts:
            return "\n\n".join(parts)
        flat = [f"{k}: {v}" for k, v in sec.items()
                if isinstance(v, (str, int, float)) and v != ""]
        return "; ".join(flat) if flat else str(sec)
    return str(sec)


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
    elif scope.startswith("section:") and scope.split(":", 1)[1] in R:
        # generic section fallback (2026-08-17 reframe: the explain pill now reaches
        # every heading, so an unknown-to-this-branch section must answer with its
        # OWN content, not the nichod essence). Prose slots first; else a flat dump
        # of the section's scalar fields — truthful, never invented.
        sec = R[scope.split(":", 1)[1]]
        text = _section_prose(sec)
    else:
        text = R["nichod"].get("essence", "")
    return {"text": text, "source": "fallback", "grounding_ratio": 1.0,
            "anchors_used": [], "forbidden_moves": [], "honesty_note": _HONESTY_NOTE,
            "note": "The grounded LLM explainer is disabled or unavailable; this is the "
                    "engine's own deterministic plain-language text for this scope."}


#: Shown whenever lang="hi" was requested but the served text is still English — either
#: translate_to_hindi's marker-count or language-detection safety net rejected the attempt, or
#: the underlying model genuinely can't produce Hindi (the report completeness rule in
#: CLAUDE.md — "no silent approximation" — requires this be disclosed, not silently absorbed).
_HINDI_UNAVAILABLE_NOTE = " (Hindi translation wasn't available for this answer — showing English.)"


def _translate_and_note(fb_or_dict: dict, text_key: str, client) -> None:
    """Translate `fb_or_dict[text_key]` to Hindi in place; if translate_to_hindi's safety
    nets rejected the attempt (the text comes back unchanged), append an honest note saying so
    rather than silently serving English with no indication Hindi was ever requested."""
    from app.llm.report_explainer import translate_to_hindi
    original = fb_or_dict[text_key]
    translated = translate_to_hindi(original, client)
    fb_or_dict[text_key] = translated
    if translated == original:
        fb_or_dict["note"] = fb_or_dict.get("note", "") + _HINDI_UNAVAILABLE_NOTE


async def _grounded(req, question: Optional[str]) -> dict:
    from app.core.config import settings
    from app.llm.client import AnthropicUnavailable
    from app.llm.report_explainer import (
        build_evidence,
        explain,
        explain_with_critic,
        refusal_reason,
    )

    lang = getattr(req, "lang", "en")

    def _work() -> dict:
        birth = BirthData(name=req.name, year=req.year, month=req.month, day=req.day,
                          hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                          latitude=req.latitude, longitude=req.longitude)
        r = build_detailed_report(birth, ayanamsa=req.ayanamsa,
                                  years_back=req.years_back, years_forward=req.years_forward)
        scope = getattr(req, "scope", "summary")
        # The WHOLE LLM path — client construction, critic construction, and the actual
        # completion call — is one fallback boundary: any unexpected failure anywhere in it
        # (not just a network error inside .complete()) must degrade to the engine's own
        # deterministic prose, never surface as a 500. A booby-trapped client factory in
        # tests exposed that construction failures used to slip past this guard.
        try:
            client = _explainer_client()
            if client is None:
                fb = _fallback_answer(r, scope)
                if lang == "hi":
                    fb["note"] += " (Hindi needs the LLM enabled — showing English.)"
                return fb
            ev = build_evidence(to_report_dict(r), scope)
            # sanitize client-supplied history: only 'user'/'assistant' turns, never a forged
            # 'system' line — the client controls both role and text (prompt-injection defence).
            hist = tuple((role, text) for role, text in getattr(req, "history", [])
                         if role in ("user", "assistant"))
            critic = _critic_client()              # None unless the critic flag is on + LLM available
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
            if lang == "hi":
                # Translation-only, of engine-authored deterministic text that never needed
                # refusal_reason in the first place. Uses a system-prompt-free client (not the
                # bound explainer `client`) — see _translation_client's docstring for why.
                _translate_and_note(fb, "text", _translation_client())
            return fb
        result = {"text": ans.text, "source": ans.source, "model": ans.model,
                  "grounding_ratio": ans.grounding_ratio, "anchors_used": list(ans.anchors_used),
                  "honesty_note": _HONESTY_NOTE,
                  "evidence": [{"n": f.n, "text": f.text, "cite": f.cite} for f in ev.facts]}
        if lang == "hi":
            # Translation happens ONLY after refusal_reason has already approved this exact
            # English text — see translate_to_hindi's docstring for why that ordering matters.
            _translate_and_note(result, "text", _translation_client())
        return result

    try:
        return await asyncio.to_thread(_work)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("grounded explainer failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"grounded explainer failed: {exc}") from exc


async def _deterministic_scope(req, scope: str) -> dict:
    """Build the report and serve the engine's own deterministic prose for `scope` — no model
    call at all. This IS the product path for /report/explain and /report/insights since the
    share-the-app cost cut: the synthesis ranking and section prose are engine output already,
    so a model added cost, latency, and a refusal path without adding information."""
    def _work() -> dict:
        birth = BirthData(name=req.name, year=req.year, month=req.month, day=req.day,
                          hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                          latitude=req.latitude, longitude=req.longitude)
        r = build_detailed_report(birth, ayanamsa=req.ayanamsa,
                                  years_back=req.years_back, years_forward=req.years_forward)
        out = _fallback_answer(r, scope)
        out["note"] = ("Deterministic engine prose — this endpoint makes no model call; "
                       "the ranking and wording are the engine's own.")
        return out

    try:
        return await asyncio.to_thread(_work)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("deterministic scope prose failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"scope prose failed: {exc}") from exc


@report_router.post("/explain")
async def post_explain(req: ExplainRequest) -> dict:
    """A grounded, plain-language explanation of a scope of the report ('summary', 'house:N',
    'section:<key>'), written for a common reader with no astrology background. Every factual
    sentence is anchored to a computed finding; the answer is never a new verdict or a
    prediction. Runs on the LOCAL model (2026-07-29: re-enabled now that serving is $0/free —
    the earlier deterministic-only cost cut was about Anthropic API cost, which no longer
    applies once the app's own fine-tuned model serves for free). Falls back to the report's
    own deterministic prose when the LLM is disabled/unavailable."""
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unsupported ayanamsa")
    return await _grounded(req, question=None)


@report_router.post("/insights")
async def post_insights(req: InsightsRequest) -> dict:
    """The prioritized whole-chart synthesis — the engine's ranked 'what matters most' narrated
    in plain, common-reader language, most important first. The RANKING is the engine's
    (deterministic); the LLM only orders and connects it into flowing prose, anchoring every
    claim and predicting nothing. Runs on the LOCAL model (free — see post_explain's docstring
    for why this is no longer deterministic-only). Falls back to the engine's own ranked digest
    as prose when the LLM is disabled/unavailable."""
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


# ── the WALLED AI-interpretation panel (labeled LLM speculation, NOT the engine) ─────────

class AiInterpretRequest(ReportRequest):
    # Aliased because a plain `register` field shadows ABCMeta.register through
    # pydantic's metaclass and warns on import; wire contract stays `register`.
    register_: Literal["gentle", "bold"] = Field("gentle", alias="register")


@report_router.post("/ai-interpret")
async def post_ai_interpret(req: AiInterpretRequest) -> dict:
    """Labeled AI speculation over the chart's computed facts — explicitly NOT the engine,
    not Raman, not validated (the `disclaimer` field ships on every response and the frontend
    banners it). Registers: 'gentle' (default) or 'bold'. Death / lifespan / serious-illness /
    self-harm are excluded in code regardless of register. Runs on the configured local
    backend; when the model is off/unreachable the panel reports itself unavailable — there
    is NO deterministic fallback here, because the engine must never author speculation."""
    from app.llm.ai_interpret import (
        AI_INTERP_SYSTEM,
        DISCLAIMER,
        TOPIC_DEFERRAL,
        build_interp_prompt,
        excluded_topic,
    )
    from app.llm.report_explainer import build_evidence
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unsupported ayanamsa")

    def _work() -> dict:
        base = {"register": req.register_, "disclaimer": DISCLAIMER, "source": "ai"}
        client = _make_client(AI_INTERP_SYSTEM) if _ai_enabled() else None
        if client is None:
            return {**base, "text": None, "unavailable": True,
                    "note": "The AI-interpretation model is disabled or unavailable."}
        birth = BirthData(name=req.name, year=req.year, month=req.month, day=req.day,
                          hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                          latitude=req.latitude, longitude=req.longitude)
        r = build_detailed_report(birth, ayanamsa=req.ayanamsa,
                                  years_back=req.years_back, years_forward=req.years_forward)
        ev = build_evidence(to_report_dict(r), "digest")
        prompt = build_interp_prompt(ev, req.register_)
        try:
            text = client.complete(prompt)
        except Exception:  # noqa: BLE001 — any model failure -> unavailable, never engine text
            logger.warning("ai-interpret model failed; panel reports unavailable")
            return {**base, "text": None, "unavailable": True,
                    "note": "The AI-interpretation model did not answer."}
        hit = excluded_topic(text)
        if hit is not None:
            # the code-enforced category wall: the whole answer is replaced, never trimmed
            logger.warning("ai-interpret output touched excluded topic (%s); deferred", hit)
            return {**base, "text": TOPIC_DEFERRAL, "deferred": True,
                    "model": getattr(client, "model", "unknown")}
        return {**base, "text": text, "model": getattr(client, "model", "unknown")}

    try:
        return await asyncio.to_thread(_work)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("ai-interpret failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"ai-interpret failed: {exc}") from exc


def _ai_enabled() -> bool:
    """The walled panel rides the same master switch as the report LLM features."""
    from app.core.config import settings
    return settings.REPORT_LLM_ENABLED


# ── chart-specific feedback (Part E: "ask some questions based on his or her chart") ─────

def _chart_key(req: "ReportRequest") -> str:
    """Deterministic grouping key for one nativity — built server-side from the validated
    birth fields (never client-supplied), so anonymous submissions for the same chart
    aggregate without sign-in."""
    return (f"{req.year:04d}-{req.month:02d}-{req.day:02d}"
            f"T{req.hour:02d}:{req.minute:02d}{req.tz_offset:+.2f}"
            f"@{req.latitude:.4f},{req.longitude:.4f}")


class FeedbackAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qid: str = Field(..., min_length=1, max_length=80)
    question_text: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., max_length=20)
    free_text: Optional[str] = Field(None, max_length=2000)


class FeedbackRequest(ReportRequest):
    answers: list[FeedbackAnswer] = Field(..., min_length=1, max_length=10)


@report_router.post("/feedback/questions")
async def post_feedback_questions(req: ReportRequest) -> dict:
    """The chart-specific feedback questions for this nativity — a deterministic re-read of
    the report's own ranked digest (no LLM). The interactive page gets these for free inside
    POST /report?format=json; this endpoint serves API callers who only want the questions."""
    from app.raman_saab.feedback_questions import build_feedback_questions
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unsupported ayanamsa")

    def _build() -> dict:
        birth = BirthData(name=req.name, year=req.year, month=req.month, day=req.day,
                          hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                          latitude=req.latitude, longitude=req.longitude)
        r = build_detailed_report(birth, ayanamsa=req.ayanamsa,
                                  years_back=req.years_back, years_forward=req.years_forward)
        return {"chart_key": _chart_key(req),
                "questions": build_feedback_questions(to_report_dict(r), lang=req.lang)}

    try:
        return await asyncio.to_thread(_build)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


class InstrumentAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qid: str = Field(..., min_length=1, max_length=80)
    answer: Optional[str] = Field(None, max_length=40)
    free_text: Optional[str] = Field(None, max_length=4000)


class InstrumentFeedbackRequest(ReportRequest):
    #: The four-part instrument runs to ~56 questions and several carry a confidence rating,
    #: so the older flow's cap of 10 would truncate a completed form. Still bounded.
    answers: list[InstrumentAnswer] = Field(..., min_length=1, max_length=200)
    #: Whether Part A was answered BEFORE the reading was read. This is the difference between
    #: evidence and a satisfaction survey, and it is recorded rather than assumed: a reader who
    #: answers after reading has been told what the chart says and can no longer report what
    #: they would have said on their own. Stored as its own row so a query can split the two.
    context: Literal["before_reading", "after_reading"] = "after_reading"


@report_router.post("/feedback/instrument")
async def post_feedback_instrument(request: Request, req: InstrumentFeedbackRequest,
                                   db: AsyncSession = Depends(get_db)) -> dict:
    """Persist answers to the four-part feedback instrument.

    The instrument is deterministic for a chart, so the server REBUILDS it and validates every
    qid and every option value against what it would itself have asked. Nothing the client says
    about a question — not its text, not its options — reaches storage: the question text is
    taken from the rebuilt instrument. A client cannot invent a question, and cannot relabel one
    it was asked.

    The answer key is not consulted here and is not returned. Scoring is a separate, deliberate
    step (`feedback_instrument.instrument_key`); an endpoint that told the submitter how they
    scored would turn the instrument into a quiz and poison every later submission for the chart.
    """
    from app.models.domain import Account, ChartFeedback
    from app.raman_saab.feedback_instrument import (
        build_feedback_instrument, validate_instrument_answers)

    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unsupported ayanamsa")

    def _instrument() -> dict:
        birth = BirthData(name=req.name, year=req.year, month=req.month, day=req.day,
                          hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                          latitude=req.latitude, longitude=req.longitude)
        r = build_detailed_report(birth, ayanamsa=req.ayanamsa,
                                  years_back=req.years_back, years_forward=req.years_forward)
        return to_report_dict(r)

    try:
        report = await asyncio.to_thread(_instrument)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    payload = [{"qid": a.qid, "answer": a.answer} for a in req.answers if a.answer is not None]
    problems = validate_instrument_answers(report, payload)
    if problems:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="; ".join(problems[:5]))

    inst = build_feedback_instrument(report)
    text_by_qid = {q["qid"]: q["text_en"]
                   for part in inst["parts"] for q in part["questions"]}

    account_id: Optional[int] = None
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        try:
            from app.core.auth import decode_access_token
            candidate = int(decode_access_token(
                auth.removeprefix("Bearer ").strip()).get("sub", ""))
            if await db.get(Account, candidate) is not None:
                account_id = candidate
        except (HTTPException, ValueError):
            account_id = None                          # bad token -> anonymous, not an error

    key = _chart_key(req)
    rows = []
    for a in req.answers:
        if a.answer is None and not (a.free_text or "").strip():
            continue                                   # an untouched question is not an answer
        base = a.qid.removesuffix(".confidence")
        text = text_by_qid.get(base, base)
        if a.qid.endswith(".confidence"):
            text = f"[confidence] {text}"
        rows.append(ChartFeedback(chart_key=key, account_id=account_id, question_id=a.qid,
                                  question_text=text[:500], answer=(a.answer or "")[:40],
                                  free_text=(a.free_text or None)))
    if not rows:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="no answers to store")

    # The reading-order context is a row of its own rather than a column: the schema is created
    # with `create_all` and has no migration path, so an added column would exist on a fresh
    # database and be missing on every deployed one.
    rows.append(ChartFeedback(
        chart_key=key, account_id=account_id,
        question_id=f"inst.{inst['version']}.meta.context",
        question_text="Was Part A answered before the reading was read?",
        answer=req.context, free_text=None))

    db.add_all(rows)
    await db.commit()
    logger.info("instrument feedback stored: %d row(s) for %s (%s)",
                len(rows), key, req.context)
    return {"stored": len(rows), "chart_key": key, "context": req.context,
            "note": "Thank you — stored for honest calibration. Your answers are not scored "
                    "back to you: knowing which option the chart took would change how the "
                    "next person answers."}


@report_router.post("/feedback")
async def post_feedback(request: Request, req: FeedbackRequest,
                        db: AsyncSession = Depends(get_db)) -> dict:
    """Persist a person's answers to their chart-specific feedback questions. Anonymous-
    friendly (no sign-in required — the quick-share flow); when a valid Bearer token IS
    present the row is attributed to the account. Answers are validated against the fixed
    scale; free text is size-capped by the request model."""
    from app.models.domain import Account, ChartFeedback
    from app.raman_saab.feedback_questions import ANSWER_OPTIONS

    for a in req.answers:
        if a.answer not in ANSWER_OPTIONS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                detail=f"answer must be one of {ANSWER_OPTIONS}")

    # Optional identity: decode a Bearer token if one rode along (same inline pattern as
    # the rate-limit key), but NEVER require it — anonymous feedback is the primary flow.
    account_id: Optional[int] = None
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        try:
            from app.core.auth import decode_access_token
            payload = decode_access_token(auth.removeprefix("Bearer ").strip())
            candidate = int(payload.get("sub", ""))
            if await db.get(Account, candidate) is not None:
                account_id = candidate
        except (HTTPException, ValueError):
            account_id = None                          # bad token -> anonymous, not an error

    key = _chart_key(req)
    rows = [ChartFeedback(chart_key=key, account_id=account_id, question_id=a.qid,
                          question_text=a.question_text, answer=a.answer,
                          free_text=(a.free_text or None))
            for a in req.answers]
    db.add_all(rows)
    await db.commit()
    logger.info("chart feedback stored: %d answer(s) for %s", len(rows), key)
    return {"stored": len(rows), "chart_key": key,
            "note": "Thank you — answers are stored for honest calibration of the reading."}
