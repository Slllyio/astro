"""HTTP endpoints for the per-chart doctrine reader (Round 10 pivot).

After Round-9 retired the population-statistics doctrine claim,
the per-chart reading is the natural next surface: take ONE chart,
let an LLM with RAG access produce a multi-section reading with
doctrine citations.

Endpoints:

  POST /medini/reading              JSON reading for a birth chart
  GET  /medini/reading/page         HTML form + reading viewer
"""
from __future__ import annotations

import asyncio
import dataclasses
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from app.core.ephemeris_engine import calculate_all_charts
from app.medini.services.chart_reader import Reading, read_chart
from app.medini.services.framework_reader import (
    master_reading_to_dict,
    read_chart_master,
    read_chart_via_framework,
    reading_to_dict as framework_reading_to_dict,
)
from app.models.schemas import BirthDataInput

logger = logging.getLogger(__name__)

reading_router = APIRouter(
    prefix="/medini/reading",
    tags=["Chart Reader (Round 10)"],
)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "medini" / "templates"


def _reading_to_dict(r: Reading) -> dict:
    """Frozen dataclass → JSON-safe dict. Recursively unwraps nested
    dataclasses (sections + citations)."""
    return {
        "chart_summary": r.chart_summary,
        "sections": [
            {
                "title": s.title,
                "text": s.text,
                "citations": [dataclasses.asdict(c) for c in s.citations],
            }
            for s in r.sections
        ],
        "source": r.source,
        "model": r.model,
        "n_citations_total": r.n_citations_total,
    }


@reading_router.post("")
async def post_reading(birth_data: BirthDataInput) -> dict:
    """Synthesize a doctrine-grounded reading from a birth chart.

    The chart computation + RAG retrieval + LLM synthesis can take
    20-60s depending on (a) cold RAG-model load, (b) number of LLM
    calls (one per section, ~5 sections), (c) which LLM is configured.
    We offload to a worker thread so the event loop stays responsive.
    """
    def _compute_sync() -> Reading:
        chart = calculate_all_charts(
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
        return read_chart(chart)

    try:
        reading = await asyncio.to_thread(_compute_sync)
    except Exception as exc:  # noqa: BLE001 - top of route, surface as 500
        logger.exception("chart reading failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"chart reading failed: {exc}",
        ) from exc
    return _reading_to_dict(reading)


@reading_router.post("/prashna")
async def post_prashna_reading(payload: dict) -> dict:
    """Prashna route — answer a natural-language question via the framework.

    Body: ``{"question": "...", "birth_data": {...BirthDataInput}}``.

    Returns the routed bhava + structured framework verdict for that bhava
    + matched keywords + confidence. The full framework Reading is also
    included so the UI can show context.
    """
    from app.core.prashna import route_question

    question = (payload.get("question") or "").strip()
    birth_payload = payload.get("birth_data") or {}
    if not question:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="question field required",
        )
    try:
        birth_data = BirthDataInput(**birth_payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"birth_data validation failed: {exc}",
        ) from exc

    def _compute_sync() -> dict:
        chart = calculate_all_charts(
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
        reading = read_chart_via_framework(chart)
        match = route_question(question)
        bhava_claim = reading.bhava_claims.get(match.bhava)
        framework_dict = framework_reading_to_dict(reading)
        return {
            "question": question,
            "routed_bhava": match.bhava,
            "routing_confidence": match.confidence,
            "matched_keywords": list(match.matched_keywords),
            "candidates_considered": [
                {"bhava": b, "score": s} for b, s in match.candidates_considered
            ],
            "primary_claim": framework_dict["bhava_claims"][str(match.bhava)] if bhava_claim else None,
            "reading": framework_dict,
        }

    try:
        return await asyncio.to_thread(_compute_sync)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("prashna reading failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"prashna reading failed: {exc}",
        ) from exc


@reading_router.post("/master")
async def post_master_reading(payload: dict) -> dict:
    """Master 13-layer reading endpoint — full classical toolkit.

    Body shape:
      {
        "birth_data": { ...BirthDataInput },
        "atmakaraka": "Mercury" | null,             # optional
        "atmakaraka_d9_sign": 1..12 | null,           # optional
        "moon_nakshatra_index": 0..26 | null,         # optional
        "target_nakshatra_index": 0..26 | null,       # optional for Tara
        "day_of_week": 0..6 | null,                   # optional for Maandi
        "is_day_birth": bool | null,                  # optional for Maandi
        "varga_pillar_scores": {bhava: float} | null  # optional for Gap B
      }

    Returns the base framework reading PLUS a "master_layers" object
    containing Ashtakavarga / varga confirmations / Arudhas / Karakamsa /
    sensitive points / Avastha / Vimsopaka / Bhāvāt Bhāvam / Yogini /
    Ashtottari / Tara / prescribed remedies.

    All optional inputs degrade gracefully; missing → layer field is null.
    """
    birth_payload = payload.get("birth_data") or {}
    try:
        birth_data = BirthDataInput(**birth_payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"birth_data validation failed: {exc}",
        ) from exc

    def _compute_sync() -> dict:
        chart_dict = calculate_all_charts(
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
        master = read_chart_master(
            chart_dict,
            atmakaraka=payload.get("atmakaraka"),
            atmakaraka_d9_sign=payload.get("atmakaraka_d9_sign"),
            moon_nakshatra_index=payload.get("moon_nakshatra_index"),
            target_nakshatra_index=payload.get("target_nakshatra_index"),
            day_of_week=payload.get("day_of_week"),
            is_day_birth=payload.get("is_day_birth"),
            varga_pillar_scores=payload.get("varga_pillar_scores"),
        )
        return master_reading_to_dict(master)

    try:
        return await asyncio.to_thread(_compute_sync)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("master reading failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"master reading failed: {exc}",
        ) from exc


@reading_router.post("/framework")
async def post_framework_reading(birth_data: BirthDataInput) -> dict:
    """Astrologer's-lens framework reading (Phases 1-9, doctrine-faithful).

    Distinct from POST /medini/reading (RAG + LLM narrative) — this
    endpoint returns the STRUCTURED framework verdict per bhava with
    classical citations, no LLM call required. Fast (~50ms per chart).
    """
    def _compute_sync() -> dict:
        chart = calculate_all_charts(
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
        reading = read_chart_via_framework(chart)
        return framework_reading_to_dict(reading)

    try:
        return await asyncio.to_thread(_compute_sync)
    except Exception as exc:  # noqa: BLE001
        logger.exception("framework reading failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"framework reading failed: {exc}",
        ) from exc


def _walk_md_ad_to_target(
    moon_longitude: float, birth_jd: float, target_jd: float,
) -> tuple[str, str | None]:
    """Walk the Vimshottari dasha chain from birth forward to target_jd.

    Returns ``(md_lord_at_target, ad_lord_at_target)``. For a target at
    birth itself, this is the natal MD/AD. For a target years later,
    this is the dasha lord ACTIVE at that date — which is what the pandit
    reading is FOR (the framework was generating natal-time MDs even when
    asked about today, which collapsed AD to be MD-itself).
    """
    from app.core.ephemeris_engine import DASHA_LORDS, DAYS_PER_VEDIC_YEAR

    nak_span = 360.0 / 27.0
    nak_idx = int(moon_longitude // nak_span)
    lord_idx_start = nak_idx % 9
    frac_into_nak = (moon_longitude % nak_span) / nak_span
    md_lord_birth, md_total_birth = DASHA_LORDS[lord_idx_start]
    md_start_jd = birth_jd - frac_into_nak * md_total_birth * DAYS_PER_VEDIC_YEAR

    # Walk forward through MDs until we cover target_jd
    cur_jd = md_start_jd
    cur_idx = lord_idx_start
    for _ in range(9):
        lord, yrs = DASHA_LORDS[cur_idx]
        end_jd = cur_jd + yrs * DAYS_PER_VEDIC_YEAR
        if cur_jd <= target_jd <= end_jd:
            md_lord, md_yrs, md_start_active = lord, yrs, cur_jd
            md_end_active = end_jd
            break
        cur_jd = end_jd
        cur_idx = (cur_idx + 1) % 9
    else:
        # target_jd beyond one full cycle — use the last MD
        md_lord, md_yrs, md_start_active = lord, yrs, cur_jd - yrs * DAYS_PER_VEDIC_YEAR
        md_end_active = cur_jd

    # AD walk within the active MD
    md_lord_idx = next(
        i for i, (n, _) in enumerate(DASHA_LORDS) if n == md_lord
    )
    ad_cursor = md_start_active
    ad_lord_result: str | None = None
    for off in range(9):
        al, ay = DASHA_LORDS[(md_lord_idx + off) % 9]
        ad_dur_yrs = md_yrs * ay / 120.0
        ad_end = ad_cursor + ad_dur_yrs * DAYS_PER_VEDIC_YEAR
        if ad_cursor <= target_jd <= ad_end:
            ad_lord_result = al
            break
        ad_cursor = ad_end

    return md_lord, ad_lord_result


def _fingerprint_from_chart_dict(chart_dict: dict, target_jd: float | None = None):
    """Derive a ChartFingerprint from the calculate_all_charts() output.

    Computes Atmakaraka via strict 7-karaka Jaimini (Rahu/Ketu excluded per
    CLAUDE.md 2026-06-01 lock), Karakamsa = AK's D9 sign, Lagna lord from
    BPHS Ch.3, MD/AD from the dasha chain walked to ``target_jd`` (defaults
    to ``chart_dict["birth_jd"]`` for a natal-time fingerprint).
    """
    from app.llm.pandit_retriever import ChartFingerprint

    asc = chart_dict["ascendant"]
    d1 = chart_dict["d1"]
    asc_sign = int(asc["sign"])
    birth_jd = float(chart_dict["birth_jd"])
    if target_jd is None:
        target_jd = birth_jd

    # Lagna lord per BPHS Ch.3
    sign_to_lord = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
        7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn",
        12: "Jupiter",
    }
    lagna_lord = sign_to_lord[asc_sign]
    lagna_lord_house = int(d1[lagna_lord]["house"])

    # Strict 7-karaka Atmakaraka — highest degree-in-sign among 7 visibles
    candidates = []
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        lon = float(d1[p]["longitude"])
        sign = int(d1[p]["sign"])
        deg = lon - (sign - 1) * 30.0
        candidates.append((p, deg, sign, lon))
    candidates.sort(key=lambda t: -t[1])
    ak_planet, _, ak_sign, ak_full_lon = candidates[0]

    # Karakamsa = AK's D9 sign (sign-type-aware navamsa start)
    nav_offset = int((ak_full_lon % 30.0) / (30.0 / 9.0))
    if ak_sign in (1, 4, 7, 10):     # movable
        nav_start = ak_sign
    elif ak_sign in (2, 5, 8, 11):    # fixed
        nav_start = ((ak_sign - 1 + 8) % 12) + 1
    else:                              # dual
        nav_start = ((ak_sign - 1 + 4) % 12) + 1
    karakamsa_sign = ((nav_start - 1 + nav_offset) % 12) + 1

    # Moon nakshatra
    moon_lon = float(d1["Moon"]["longitude"])
    moon_nakshatra = int(moon_lon // (360.0 / 27.0))
    moon_sign = int(d1["Moon"]["sign"])

    # MD/AD walked forward to target_jd (not just natal)
    md_lord, ad_lord = _walk_md_ad_to_target(moon_lon, birth_jd, target_jd)

    # Active yoga names
    yogas = chart_dict.get("yogas") or []
    yoga_names: list[str] = []
    for y in yogas:
        name = (
            y.get("name") if isinstance(y, dict) else
            getattr(y, "name", None) or getattr(y, "yoga_name", None)
        )
        if name and name not in yoga_names:
            yoga_names.append(name)

    return ChartFingerprint(
        asc_sign=asc_sign,
        asc_lord_house=lagna_lord_house,
        asc_lord_planet=lagna_lord,
        moon_nakshatra=moon_nakshatra,
        moon_sign=moon_sign,
        atmakaraka=ak_planet,
        karakamsa_sign=karakamsa_sign,
        md_lord=md_lord,
        ad_lord=ad_lord,
        active_yoga_names=tuple(yoga_names),
    )


@reading_router.post("/pandit")
async def post_pandit_reading(payload: dict) -> dict:
    """Pandit-grade reading via 8-axis RAG retrieval + Sonnet 4.6 synthesis.

    Body shape:
      {
        "birth_data": { ...BirthDataInput },
        "focal_themes": ["marriage", "career", ...] | null,
        "model": "claude-sonnet-4-6" | null      # optional override
      }

    Pulls 30-60 classical passages across 8 doctrinal axes (Lagna,
    Lagna-lord, Moon nakshatra, AK, MD, MD×AD, yogas, domain) from the
    18,061-rule shloka corpus + 27 DKP TranslationRecords + 1,737 Nadi
    records, injects them into a Sonnet 4.6 prompt with [Ref N] citation
    anchors, and returns the synthesized narrative.

    Requires ANTHROPIC_API_KEY in env. Returns 503 if the LLM is
    unreachable. Wall-clock: 25-50s for a typical chart (one LLM call,
    ~5-15K input tokens, ~3-8K output tokens).
    """
    birth_payload = payload.get("birth_data") or {}
    try:
        birth_data = BirthDataInput(**birth_payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"birth_data validation failed: {exc}",
        ) from exc

    focal_themes = tuple(payload.get("focal_themes") or ())
    model = payload.get("model") or "claude-sonnet-4-6"
    # Optional target date for the reading — defaults to today so MD/AD
    # reflect the active dasha at reading-time, not natal time.
    target_date = payload.get("target_date")  # "YYYY-MM-DD" or None

    def _compute_sync() -> dict:
        import swisseph as swe
        from app.llm.client import AnthropicClient, AnthropicUnavailable
        from app.llm.pandit_retriever import retrieve_for_chart
        from app.llm.pandit_synthesizer import PanditSynthesizer

        chart = calculate_all_charts(
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
        # Resolve target_jd: caller-supplied "YYYY-MM-DD" → JD at noon UT,
        # else default to today_jd
        if target_date:
            ty, tm, td = (int(x) for x in target_date.split("-"))
            target_jd = swe.julday(ty, tm, td, 12.0, swe.GREG_CAL)
        else:
            import datetime as _dt
            now = _dt.datetime.now(_dt.timezone.utc)
            target_jd = swe.julday(
                now.year, now.month, now.day,
                now.hour + now.minute / 60.0,
                swe.GREG_CAL,
            )
        fingerprint = _fingerprint_from_chart_dict(chart, target_jd=target_jd)
        bundle = retrieve_for_chart(fingerprint)
        synth = PanditSynthesizer(llm=AnthropicClient(model=model))
        reading = synth.synthesize(bundle, focal_themes=focal_themes)
        return {
            "narrative": reading.narrative,
            "model": reading.model,
            "focal_themes": list(reading.focal_themes),
            "prompt_token_estimate": reading.prompt_token_estimate,
            "citations_used": [
                {
                    "ref_id": p.ref_id, "axis": p.axis,
                    "source": p.source, "chapter": p.chapter,
                    "text": p.text[:300],
                }
                for p in reading.citations_used
            ],
            "n_passages_retrieved": len(bundle.passages),
            "n_dkp_records": len(bundle.dkp_translations),
            "nadi_found": bool(bundle.nadi_match and bundle.nadi_match.found),
            "fingerprint": {
                "asc_sign": fingerprint.asc_sign,
                "atmakaraka": fingerprint.atmakaraka,
                "karakamsa_sign": fingerprint.karakamsa_sign,
                "md_lord": fingerprint.md_lord,
                "ad_lord": fingerprint.ad_lord,
                "active_yogas": list(fingerprint.active_yoga_names),
            },
        }

    try:
        return await asyncio.to_thread(_compute_sync)
    except Exception as exc:
        # AnthropicUnavailable is a specific 503 — bubble it up that way
        from app.llm.client import AnthropicUnavailable
        if isinstance(exc, AnthropicUnavailable):
            logger.warning("pandit reading: Anthropic unavailable: %s", exc)
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM unavailable: {exc}",
            ) from exc
        logger.exception("pandit reading failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"pandit reading failed: {exc}",
        ) from exc


@reading_router.get("/page", response_class=HTMLResponse)
async def reading_page() -> HTMLResponse:
    """Birth-data form + rendered reading viewer."""
    html_path = _TEMPLATES_DIR / "reading.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reading template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
