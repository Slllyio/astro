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

from fastapi import APIRouter, Body, HTTPException, Query, status
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


# ---------------------------------------------------------------------------
# Request/response envelopes
# ---------------------------------------------------------------------------

class InfoResponse(BaseModel):
    """Metadata about the integration layer; exposed for clients to feature-detect."""

    integration_version: str = "0.5.0"
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
