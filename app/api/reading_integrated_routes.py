"""HTTP routes exposing the integration adapters at /reading/integrated/*.

A minimal FastAPI router over the ``app.integration`` package. Routes:

    GET  /reading/integrated/info              — adapter metadata + counts
    POST /reading/integrated/enhance           — DKP translation enhancer
    POST /reading/integrated/modulate          — DKP modulator
    POST /reading/integrated/compare-chara     — Chara Dasha cross-engine diff
    GET  /reading/integrated/compare-functional?lagna_sign=N
                                              — D-7 functional cross-engine diff
    POST /reading/integrated/generate-and-enhance
                                              — run Track A + enhance in one shot

All routes return JSON. Compute work is sync (Pydantic + dataclass shuffling)
and fast — most routes complete in <100ms. The generate-and-enhance route
calls Track A's pipeline which is heavier; offloaded to a worker thread.

NO route modifies either Track A or Track B engines. The router is purely
a thin HTTP veneer over the existing ``app.integration`` library API.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pathlib import Path

from fastapi import APIRouter, Body, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.core.dkp_modulation import DKPContext
from app.integration import (
    CharaComparisonReport,
    DkpModulatedReading,
    FunctionalComparisonReport,
    IntegratedReadingOutput,
    build_dkp_context_from_reading,
    compare_chara_dasha,
    compare_functional_roles,
    enhance,
    modulate_all_domains,
)
from app.integration.dkp_enhancer import registry_size
from app.reading.sequences.chara_dasha import CharaDashaResult, run_sequence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reading/integrated", tags=["reading-integrated"])

# Jinja2 templates dir (shared with reading_v15_routes).
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


# ---------------------------------------------------------------------------
# Request/response envelopes
# ---------------------------------------------------------------------------

class InfoResponse(BaseModel):
    """Metadata about the integration layer; exposed for clients to feature-detect."""

    integration_version: str = "1.0.0"
    adapters: list[str] = Field(
        default_factory=lambda: [
            "enhance",
            "modulate_all_domains",
            "annotate_with_gap_modules",
            "compare_chara_dasha",
            "compare_functional_roles",
            "compare_vimshottari_current_md",
            "compare_yoga_detection",
            "compare_shadbala",
            "compare_d9_signs",
            "compare_argala_drishti",
            "narrate_and_verify",
            "enhance_with_corpus_rag",
            "run_benchmark",
        ]
    )
    dkp_translation_registry_size: int
    cli_modes: list[str] = Field(
        default_factory=lambda: [
            "enhance",
            "compare",
            "generate-and-enhance",
        ]
    )
    notes: list[str] = Field(
        default_factory=lambda: [
            "All adapters are read-only over app/reading/* and app/core/*.",
            "Track B's Chara Dasha has a documented uniform-12y bug; see "
            "docs/integration/doctrine-divergence-chara-dasha-2026-05-31.md",
        ]
    )


class EnhanceRequest(BaseModel):
    """Body for POST /reading/integrated/enhance."""

    reading: dict[str, Any] = Field(
        description="A Track-A ReadingOutput-shaped dict (e.g. from app.reading.cli)"
    )


class ModulateRequest(BaseModel):
    """Body for POST /reading/integrated/modulate.

    ``dkp_context_overrides`` lets the client supply any subset of the 12
    DKPContext fields. Fields the client doesn't supply are extracted from
    the reading or left None."""

    reading: dict[str, Any]
    dkp_context_overrides: dict[str, Any] = Field(default_factory=dict)


class CompareCharaRequest(BaseModel):
    """Body for POST /reading/integrated/compare-chara.

    ``track_a_chara_dasha`` is the ``sequences.chara_dasha`` block from a
    Track-A reading (a ``CharaDashaResult``-shaped dict)."""

    track_a_chara_dasha: dict[str, Any]
    lagna_sign: int = Field(ge=1, le=12)
    birth_jd: float
    target_jd: float | None = None


class GenerateAndEnhanceRequest(BaseModel):
    """Body for POST /reading/integrated/generate-and-enhance.

    Runs Track A's full ``compute()`` pipeline then enhances the output.
    All inputs match Track A's CLI flags."""

    dob: str = Field(description="YYYY-MM-DD")
    time: str = Field(description="HH:MM (24-hour)")
    tz: str = Field(description='Timezone offset, e.g. "+05:30"')
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    enrich: bool = Field(
        default=False,
        description="If True, run Tier-3 enrichments (slower, ~3-5s).",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

_SIGN_NAMES = [
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_STATUS_TO_COLOR = {"shipped": "positive", "flagged": "neutral", "rejected": "negative"}


@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse)
async def integrated_form_route(request: Request) -> HTMLResponse:
    """GET /reading/integrated/ — chart-input form."""
    return _templates.TemplateResponse(
        request,
        "reading_integrated_form.html",
        {},
    )


def _build_view_context(
    request: Request,
    *,
    reading: dict[str, Any],
    integrated: dict[str, Any] | None,
    modulated: dict[str, Any] | None,
    gap_annotated: dict[str, Any] | None,
    comparator_results: list[dict[str, Any]],
    narrative_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """Project the integrated payload into Jinja-friendly context."""
    import json as _json

    chart_block = reading.get("chart", {})
    cusps = chart_block.get("cusps", {})
    asc_sign = int(cusps.get("sign", 0) or 0)
    asc_sign_name = _SIGN_NAMES[asc_sign] if 1 <= asc_sign <= 12 else "?"
    extras = chart_block.get("extras") or {}
    current_md = (extras.get("current_mahadasha") or {}).get("mahadasha_lord", "?")

    # Domains
    domains_block = reading.get("domains") or {}
    DOMAIN_BHAVA = {"career": 10, "marriage": 7, "children": 5, "wealth": 2, "health": 6, "education": 4}
    domains_view: list[dict[str, Any]] = []
    for name, bhava in DOMAIN_BHAVA.items():
        d = domains_block.get(name)
        if not isinstance(d, dict):
            continue
        overall = d.get("overall_verdict") or {}
        domains_view.append({
            "name": name,
            "bhava": bhava,
            "direction": overall.get("direction", "neutral"),
        })

    # DKP translations summary
    dkp_summary = None
    if integrated:
        summary = (integrated.get("dkp_translations_summary") or {})
        records = summary.get("records") or {}
        if records:
            dkp_summary = {
                "total_attached": summary.get("total_records_attached", 0),
                "unique_count": len(records),
                "record_keys": list(records.keys())[:10],
                "shlokas": {
                    k: (v.get("shloka") or "")[:200]
                    for k, v in list(records.items())[:10]
                    if isinstance(v, dict)
                },
            }

    # Gap modules summary
    gap_summary = None
    if gap_annotated:
        gap_summary = {
            "available_count": gap_annotated.get("available_count", 0),
            "modules": gap_annotated.get("gap_modules", {}),
        }

    # Narrative
    narrative_view = None
    if narrative_result:
        narrative_view = {
            "overall_summary": narrative_result.get("overall_summary", ""),
            "survival_threshold": narrative_result.get("survival_threshold", 3),
            "shipped_count": len(narrative_result.get("domains_shipped", []) or []),
            "flagged_count": len(narrative_result.get("domains_flagged", []) or []),
            "rejected_count": len(narrative_result.get("domains_rejected", []) or []),
            "per_domain": [
                {
                    "domain": pd.get("domain"),
                    "paragraph": (pd.get("narrative") or {}).get("paragraph", ""),
                    "confirm_count": pd.get("confirm_count", 0),
                    "status": pd.get("status", "flagged"),
                    "status_color": _STATUS_TO_COLOR.get(pd.get("status", "flagged"), "neutral"),
                }
                for pd in narrative_result.get("per_domain", []) or []
            ],
        }

    raw = {
        "core": reading,
        "integrated": integrated,
        "modulated": modulated,
        "gap_annotated": gap_annotated,
        "comparators": comparator_results,
        "narrative": narrative_result,
    }
    raw_json = _json.dumps(raw, indent=2, default=str)[:50000]  # cap for browser

    return {
        "request": request,
        "chart_summary": f"Lagna {asc_sign_name}",
        "asc_sign": asc_sign,
        "asc_sign_name": asc_sign_name,
        "schema_version": (reading.get("meta") or {}).get("schema_version", "?"),
        "integration_version": (integrated or {}).get("integration_version", "0.7.0"),
        "current_md_lord": current_md,
        "domains": domains_view,
        "dkp_summary": dkp_summary,
        "gap_summary": gap_summary,
        "comparators": comparator_results,
        "narrative": narrative_view,
        "raw_json": raw_json,
    }


@router.post("/generate", response_class=HTMLResponse)
async def integrated_generate_route(
    request: Request,
    dob: str = Form(...),
    time: str = Form(...),
    tz: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    layer_dkp: str | None = Form(default=None),
    layer_gap: str | None = Form(default=None),
    layer_comparators: str | None = Form(default=None),
    layer_narrative: str | None = Form(default=None),
    layer_corpus: str | None = Form(default=None),
) -> HTMLResponse:
    """POST /reading/integrated/generate — form submission renders the
    integrated view template."""

    def _do_work():
        from app.reading.proforma import compute as track_a_compute
        from app.reading.schema import ChartInput
        ci = ChartInput(dob=dob, time=time, tz=tz, lat=lat, lon=lon)
        reading = track_a_compute(ci, enrich=False)

        integrated_payload = None
        if layer_dkp:
            from app.integration import enhance
            integrated_payload = enhance(reading).model_dump(mode="json")
            reading = integrated_payload["reading"]

        modulated_payload = None
        if layer_dkp:
            from app.integration import build_dkp_context_from_reading, modulate_all_domains
            ctx = build_dkp_context_from_reading(reading)
            modulated_payload = modulate_all_domains(reading, dkp_context=ctx).model_dump(mode="json")

        gap_payload = None
        if layer_gap:
            from app.integration import annotate_with_gap_modules
            gap_payload = annotate_with_gap_modules(reading).model_dump(mode="json")

        comp_results: list[dict[str, Any]] = []
        if layer_comparators:
            try:
                from app.integration import compare_functional_roles
                fr = compare_functional_roles(int((reading.get("chart") or {}).get("cusps", {}).get("sign", 1)))
                comp_results.append({"name": "functional_roles", "verdict": fr.verdict_summary})
            except Exception:
                pass
            try:
                from app.integration import compare_yoga_detection
                yc = compare_yoga_detection(reading)
                comp_results.append({"name": "yoga_detection", "verdict": yc.verdict_summary})
            except Exception:
                pass

        narrative_payload = None
        if layer_narrative:
            from app.integration import narrate_and_verify
            narrative_payload = narrate_and_verify(
                reading, integrated=integrated_payload,
            ).model_dump(mode="json")

        return reading, integrated_payload, modulated_payload, gap_payload, comp_results, narrative_payload

    try:
        reading, integrated, modulated, gap_annotated, comp_results, narrative_result = (
            await asyncio.to_thread(_do_work)
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("integrated generate route failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {exc}",
        ) from exc

    context = _build_view_context(
        request,
        reading=reading,
        integrated=integrated,
        modulated=modulated,
        gap_annotated=gap_annotated,
        comparator_results=comp_results,
        narrative_result=narrative_result,
    )
    return _templates.TemplateResponse(request, "reading_integrated_view.html", context)


@router.get("/cache-stats")
async def cache_stats_route() -> dict[str, Any]:
    """Return the default ReadingCache statistics (size, hit rate, etc.).

    Useful for production observability — surface cache effectiveness
    over time."""
    from app.integration.production import default_cache
    return default_cache().stats().model_dump(mode="json")


@router.post("/cache-clear")
async def cache_clear_route() -> dict[str, Any]:
    """Clear the default ReadingCache. Returns the post-clear stats."""
    from app.integration.production import default_cache
    cache = default_cache()
    cache.clear()
    return cache.stats().model_dump(mode="json")


@router.get("/info", response_model=InfoResponse)
async def info_route() -> InfoResponse:
    """Return integration-layer metadata + version + adapter list.

    Useful for feature-detection by clients before calling the heavier
    adapter routes."""
    return InfoResponse(
        dkp_translation_registry_size=registry_size(),
    )


@router.post("/enhance")
async def enhance_route(body: EnhanceRequest = Body(...)) -> dict[str, Any]:
    """Annotate a Track-A reading with DKP translations.

    Returns the ``IntegratedReadingOutput`` envelope (reading +
    dkp_translations_summary). The input reading dict is mutated in place
    inside the adapter (per-finding sidecars added) — clients who need to
    preserve the original should deep-copy first."""
    try:
        result: IntegratedReadingOutput = enhance(body.reading)
    except Exception as exc:
        logger.exception("DKP enhancer failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DKP enhancer failed: {exc}",
        ) from exc
    return result.model_dump(mode="json")


@router.post("/modulate")
async def modulate_route(body: ModulateRequest = Body(...)) -> dict[str, Any]:
    """Modulate a Track-A reading via Track-B's DKP layer.

    Extracts a DKPContext from the reading (lat/lon/dob/active_md_lord),
    applies any client-supplied overrides, then runs each domain through
    ``apply_dkp_modulation``. Returns a ``DkpModulatedReading`` with one
    ``ModulatedDomainReading`` per non-null Track-A domain."""
    try:
        ctx = build_dkp_context_from_reading(
            body.reading, **body.dkp_context_overrides
        )
        result: DkpModulatedReading = modulate_all_domains(body.reading, dkp_context=ctx)
    except TypeError as exc:
        # Unknown DKPContext field name in overrides — surface as 400.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dkp_context_overrides: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("DKP modulator failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DKP modulator failed: {exc}",
        ) from exc
    return result.model_dump(mode="json")


@router.post("/compare-chara")
async def compare_chara_route(body: CompareCharaRequest = Body(...)) -> dict[str, Any]:
    """Cross-engine Chara Dasha comparison.

    Reconstructs a ``CharaDashaResult`` from the supplied dict (typically
    pulled from a Track-A reading's ``sequences.chara_dasha`` block), then
    diffs against Track B's ``chara_windows_jd`` for the same lagna + birth_jd."""
    try:
        a_result: CharaDashaResult = CharaDashaResult.model_validate(
            body.track_a_chara_dasha
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"track_a_chara_dasha is not a valid CharaDashaResult shape: {exc}",
        ) from exc
    try:
        report: CharaComparisonReport = compare_chara_dasha(
            a_result,
            lagna_sign=body.lagna_sign,
            birth_jd=body.birth_jd,
            target_jd=body.target_jd,
        )
    except Exception as exc:
        logger.exception("Chara comparator failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chara comparator failed: {exc}",
        ) from exc
    return report.model_dump(mode="json")


@router.get("/compare-functional")
async def compare_functional_route(
    lagna_sign: int = Query(ge=1, le=12, description="Natal Lagna sign 1..12"),
) -> dict[str, Any]:
    """Cross-engine functional benefic/malefic comparison.

    Runs both Track A's D-7 PVR classification and Track B's
    ``functional_roles()`` for the supplied lagna sign and returns the
    per-planet agreement matrix."""
    try:
        report: FunctionalComparisonReport = compare_functional_roles(lagna_sign)
    except Exception as exc:
        logger.exception("Functional comparator failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Functional comparator failed: {exc}",
        ) from exc
    return report.model_dump(mode="json")


@router.post("/corpus-rag")
async def corpus_rag_route(body: dict = Body(...)) -> dict[str, Any]:
    """Attach full 6.28M-word doctrine-corpus RAG citations to a reading.

    Body: {"reading": {...}, "top_k"?: int, "max_findings"?: int}.
    Returns CorpusRAGEnhancedReading. Falls back gracefully when the RAG
    index isn't available on the host."""
    reading = body.get("reading")
    if not isinstance(reading, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="body.reading must be a Track-A ReadingOutput dict",
        )
    top_k = int(body.get("top_k", 3))
    max_findings = body.get("max_findings")

    def _do_work():
        from app.integration.corpus_rag_enhancer import enhance_with_corpus_rag
        return enhance_with_corpus_rag(
            reading, top_k=top_k,
            max_findings=int(max_findings) if max_findings is not None else None,
        )

    try:
        result = await asyncio.to_thread(_do_work)
    except Exception as exc:
        logger.exception("corpus-rag route failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"corpus-rag failed: {exc}",
        ) from exc
    return result.model_dump(mode="json")


@router.get("/benchmark")
async def benchmark_route(
    chart_name: str | None = Query(default=None, description="Optional filter to one chart"),
) -> dict[str, Any]:
    """Run the famous-chart accuracy benchmark.

    Without ``chart_name`` filter: 24 events across 6 charts, ~3-5s.
    With filter: just that chart's events, ~0.6s for one chart.
    """
    def _do_work():
        from app.integration.benchmark import FAMOUS_EVENTS, run_benchmark
        events = FAMOUS_EVENTS
        if chart_name:
            events = [e for e in FAMOUS_EVENTS if e.chart_name == chart_name]
            if not events:
                raise ValueError(f"no events for chart {chart_name!r}")
        return run_benchmark(events=events)

    try:
        result = await asyncio.to_thread(_do_work)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("benchmark route failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"benchmark failed: {exc}",
        ) from exc
    return result.model_dump(mode="json")


@router.post("/master-reading")
async def master_reading_route(body: dict = Body(...)) -> dict[str, Any]:
    """Generate the v1.1.0 master reading (deterministic, template-based).

    Body: {"reading": {...}}  # Track-A ReadingOutput dict
    Returns MasterReading with chart basics + dasha triple + Arudha +
    6 domain paragraphs synthesised from M1-M7.
    """
    reading = body.get("reading")
    if not isinstance(reading, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="body.reading must be a Track-A ReadingOutput dict",
        )

    def _do_work():
        from app.integration import compose_master_reading
        return compose_master_reading(reading)

    try:
        result = await asyncio.to_thread(_do_work)
    except Exception as exc:
        logger.exception("master_reading route failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"master_reading failed: {exc}",
        ) from exc
    return result.model_dump(mode="json")


@router.post("/master-polish")
async def master_polish_route(body: dict = Body(...)) -> dict[str, Any]:
    """v1.2.0 — LLM-polished master reading.

    Body: {
      "reading": {...},                  # Track-A ReadingOutput dict
      "ollama_host"?: "http://localhost:11434",
      "ollama_model"?: "llama3.1",
      "polish_domains"?: true,
      "polish_dasha_triple"?: true,
      "polish_arudha"?: true,
      "polish_upapada"?: true,
      "include_overview"?: true
    }

    If ``ollama_host`` + ``ollama_model`` are supplied, uses OllamaClient.
    Otherwise falls back to StubClient (offline) — polished_paragraph
    will equal the stub canned response and the template_paragraph
    preserves the M8 deterministic output."""
    reading = body.get("reading")
    if not isinstance(reading, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="body.reading must be a Track-A ReadingOutput dict",
        )

    ollama_host = body.get("ollama_host")
    ollama_model = body.get("ollama_model")

    def _do_work():
        from app.integration import compose_master_reading, llm_polish_master_reading
        from app.llm.client import OllamaClient

        master = compose_master_reading(reading)
        llm = None
        if ollama_host and ollama_model:
            llm = OllamaClient(host=str(ollama_host), model=str(ollama_model))
        return llm_polish_master_reading(
            master, llm=llm,
            polish_domains=bool(body.get("polish_domains", True)),
            polish_dasha_triple=bool(body.get("polish_dasha_triple", True)),
            polish_arudha=bool(body.get("polish_arudha", True)),
            polish_upapada=bool(body.get("polish_upapada", True)),
            include_overview=bool(body.get("include_overview", True)),
        )

    try:
        result = await asyncio.to_thread(_do_work)
    except Exception as exc:
        logger.exception("master_polish route failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"master_polish failed: {exc}",
        ) from exc
    return result.model_dump(mode="json")


@router.post("/narrate")
async def narrate_route(body: dict = Body(...)) -> dict[str, Any]:
    """LLM narrative + 4-critic adversarial verification.

    Body shape:
      {
        "reading": {...},  // Track-A ReadingOutput dict
        "integrated": {...}  // optional IntegratedReadingOutput dict for DKP citations
      }

    Returns a VerifiedNarrative envelope: per-domain narrative paragraphs +
    4 critic verdicts each + survival status (shipped/flagged/rejected).
    Uses the StubClient fallback if no LLM is configured — replace with a
    real client (OllamaClient / future OpenAIClient) by injecting via DI."""
    reading = body.get("reading")
    if not isinstance(reading, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="body.reading must be a Track-A ReadingOutput dict",
        )
    integrated = body.get("integrated") if isinstance(body.get("integrated"), dict) else None

    def _do_work():
        from app.integration.narrative import narrate_and_verify
        return narrate_and_verify(reading, integrated=integrated)

    try:
        result = await asyncio.to_thread(_do_work)
    except Exception as exc:
        logger.exception("narrate route failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"narrate failed: {exc}",
        ) from exc
    return result.model_dump(mode="json")


@router.post("/stream-generate")
async def stream_generate_route(body: GenerateAndEnhanceRequest = Body(...)):
    """Streaming variant of generate-and-enhance.

    Emits Server-Sent Events (SSE) so the client sees progressive output:

        event: layer
        data: {"layer": "core", "status": "running"}

        event: layer
        data: {"layer": "core", "status": "complete", "elapsed_ms": 612}

        event: layer
        data: {"layer": "dkp", "status": "running"}
        ...
        event: complete
        data: {"layers_completed": [...], "total_elapsed_ms": 4321}

    Each layer is a separate event; the response stays open until the
    pipeline completes or errors.
    """
    import time

    async def _event_generator():
        from app.integration import (
            annotate_with_gap_modules, enhance,
            build_dkp_context_from_reading, modulate_all_domains,
        )
        from app.reading.proforma import compute as track_a_compute
        from app.reading.schema import ChartInput

        def _emit(event: str, payload: dict[str, Any]) -> str:
            import json as _json
            return f"event: {event}\ndata: {_json.dumps(payload)}\n\n"

        layers_completed: list[str] = []
        t0 = time.time()

        # Layer 1: core reading
        yield _emit("layer", {"layer": "core", "status": "running"})
        t_layer = time.time()
        try:
            ci = ChartInput(
                dob=body.dob, time=body.time, tz=body.tz,
                lat=body.lat, lon=body.lon,
            )
            reading = await asyncio.to_thread(track_a_compute, ci, enrich=body.enrich)
        except Exception as exc:
            yield _emit("error", {"layer": "core", "detail": str(exc)})
            return
        layer_ms = int((time.time() - t_layer) * 1000)
        layers_completed.append("core")
        yield _emit("layer", {
            "layer": "core", "status": "complete", "elapsed_ms": layer_ms,
            "schema_version": (reading.get("meta") or {}).get("schema_version"),
        })

        # Layer 2: DKP enhance
        yield _emit("layer", {"layer": "dkp_enhance", "status": "running"})
        t_layer = time.time()
        try:
            integrated = enhance(reading)
            reading = integrated.reading
        except Exception as exc:
            yield _emit("error", {"layer": "dkp_enhance", "detail": str(exc)})
            return
        layer_ms = int((time.time() - t_layer) * 1000)
        layers_completed.append("dkp_enhance")
        yield _emit("layer", {
            "layer": "dkp_enhance", "status": "complete", "elapsed_ms": layer_ms,
            "translations_attached": integrated.dkp_translations_summary.total_records_attached,
        })

        # Layer 3: DKP modulate
        yield _emit("layer", {"layer": "dkp_modulate", "status": "running"})
        t_layer = time.time()
        try:
            ctx = build_dkp_context_from_reading(reading)
            modulated = modulate_all_domains(reading, dkp_context=ctx)
        except Exception as exc:
            yield _emit("error", {"layer": "dkp_modulate", "detail": str(exc)})
            return
        layer_ms = int((time.time() - t_layer) * 1000)
        layers_completed.append("dkp_modulate")
        yield _emit("layer", {
            "layer": "dkp_modulate", "status": "complete", "elapsed_ms": layer_ms,
            "domains_modulated": len(modulated.per_domain),
            "context_completeness": modulated.context_completeness,
        })

        # Layer 4: Gap modules
        yield _emit("layer", {"layer": "gap_modules", "status": "running"})
        t_layer = time.time()
        try:
            gap = annotate_with_gap_modules(reading)
        except Exception as exc:
            yield _emit("error", {"layer": "gap_modules", "detail": str(exc)})
            return
        layer_ms = int((time.time() - t_layer) * 1000)
        layers_completed.append("gap_modules")
        yield _emit("layer", {
            "layer": "gap_modules", "status": "complete", "elapsed_ms": layer_ms,
            "available_count": gap.available_count,
            "skipped_count": gap.skipped_count,
        })

        # Done
        total_ms = int((time.time() - t0) * 1000)
        yield _emit("complete", {
            "layers_completed": layers_completed,
            "total_elapsed_ms": total_ms,
        })

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
    )


@router.post("/generate-and-enhance")
async def generate_and_enhance_route(
    body: GenerateAndEnhanceRequest = Body(...),
) -> dict[str, Any]:
    """Run Track A's full pipeline then DKP-enhance in one shot.

    Heavier than ``/enhance`` because it actually computes the reading
    (Tier-0/1/2/sequences/domains). Offloaded to a worker thread so the
    event loop stays responsive."""
    # Lazy import so the routes module starts fast even when this endpoint
    # is unused — proforma.compute pulls in swisseph and is heavy.
    from app.reading.proforma import compute as track_a_compute
    from app.reading.schema import ChartInput

    def _do_work() -> IntegratedReadingOutput:
        chart_input = ChartInput(
            dob=body.dob,
            time=body.time,
            tz=body.tz,
            lat=body.lat,
            lon=body.lon,
        )
        reading_obj = track_a_compute(chart_input, enrich=body.enrich)
        return enhance(reading_obj)

    try:
        result = await asyncio.to_thread(_do_work)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chart input: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("generate-and-enhance pipeline failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {exc}",
        ) from exc
    return result.model_dump(mode="json")
