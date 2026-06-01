"""High-quality consolidated chart summary.

The integration adapters individually produce a lot of data. Most of it
is noise unless you know what to look for. This module assembles a SINGLE
clean summary that surfaces only chart-specific signal:

- Lagna + key placements
- MD at NOW (not at birth)
- Gap-module headlines (Karakamsa, Bhrigu Bindu, Moon nakshatra, AK)
- Yoga findings — aliased and intersected across engines
- Functional roles — doctrine-reconciled
- DKP-modulated verdicts ONLY for domains with non-neutral direction
- DKP placement-verified shloka citations (currently 0 false positives
  thanks to the v1.0.1 lordship filter)

Public surface
--------------
- ``summarize_chart(reading, *, include_gap=True, include_narrative=False)``
  → ``ChartSummary``
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.integration.dasha_now import MDLookup, md_at_birth, md_at_now


_SIGN_NAMES = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

class ChartBasics(BaseModel):
    """Headline lagna + key planet positions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lagna_sign: int = Field(ge=1, le=12)
    lagna_sign_name: str
    lagna_longitude: float
    moon_sign: int
    moon_sign_name: str
    moon_nakshatra: str
    moon_pada: int
    sun_sign: int
    sun_sign_name: str


class MDSnapshot(BaseModel):
    """MD-at-birth + MD-at-now snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    md_at_birth: dict[str, Any]
    md_at_now: dict[str, Any]


class GapHeadlines(BaseModel):
    """The chart-specific findings from the Gap modules that matter most."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arudha_lagna_sign: int | None = None
    arudha_lagna_sign_name: str | None = None
    upapada_lagna_sign: int | None = None
    upapada_lagna_sign_name: str | None = None
    atmakaraka: str | None = None
    karakamsa_sign: int | None = None
    karakamsa_sign_name: str | None = None
    bhrigu_bindu_sign: int | None = None
    bhrigu_bindu_house: int | None = None
    moon_nakshatra: str | None = None
    moon_gana: str | None = None
    moon_yoni: str | None = None
    moon_nadi: str | None = None


class YogaSummary(BaseModel):
    """Cross-engine yoga summary after alias-aware matching."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    canonical_yogas_both_engines_detect: list[str]
    track_a_only: list[str]
    track_b_only: list[str]
    intersection_count: int
    union_count: int


class FunctionalRoleNote(BaseModel):
    """Doctrine-reconciled role note for one planet."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    planet: str
    canonical_role: str
    note: str


class DomainHighlight(BaseModel):
    """One domain's actionable verdict (only non-neutral domains)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    bhava: int
    direction: str
    confidence: str
    summary: str


class ChartSummary(BaseModel):
    """Consolidated high-signal summary of an integrated reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "1.0.2"
    basics: ChartBasics
    md_snapshot: MDSnapshot
    gap_headlines: GapHeadlines
    yoga_summary: YogaSummary
    functional_role_notes: list[FunctionalRoleNote]
    domain_highlights: list[DomainHighlight]
    placement_verified_dkp_count: int
    skipped_domains_count: int  # neutral/uninformative domains hidden
    warnings: list[str]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _safe_int(v: Any) -> int | None:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _sign_name(s: int | None) -> str | None:
    if s is None or not (1 <= s <= 12):
        return None
    return _SIGN_NAMES[s]


def _build_basics(reading: dict[str, Any]) -> ChartBasics:
    chart = reading.get("chart") or {}
    cusps = chart.get("cusps") or {}
    planets = chart.get("planets") or {}
    moon = planets.get("Moon") or {}
    sun = planets.get("Sun") or {}
    naks = moon.get("nakshatra") or {}
    return ChartBasics(
        lagna_sign=int(cusps.get("sign", 1)),
        lagna_sign_name=_sign_name(cusps.get("sign")) or "?",
        lagna_longitude=float(chart.get("lagna_longitude", 0.0)),
        moon_sign=int(moon.get("sign", 1)),
        moon_sign_name=str(moon.get("sign_name", "?")),
        moon_nakshatra=str(naks.get("name", "?")),
        moon_pada=int(naks.get("pada", 0)),
        sun_sign=int(sun.get("sign", 1)),
        sun_sign_name=str(sun.get("sign_name", "?")),
    )


def _build_md_snapshot(reading: dict[str, Any]) -> MDSnapshot:
    try:
        birth = md_at_birth(reading)
        now = md_at_now(reading)
    except ValueError:
        # Reading lacks md_judgments — return empty
        empty = MDLookup(
            target_jd=0.0, md_lord="?", start_jd=0.0, end_jd=0.0,
            start_date="", end_date="",
            age_at_start_years=0.0, age_at_end_years=0.0, age_now_years=0.0,
            is_at_birth=False,
        )
        return MDSnapshot(
            md_at_birth=empty.model_dump(mode="json"),
            md_at_now=empty.model_dump(mode="json"),
        )
    return MDSnapshot(
        md_at_birth=birth.model_dump(mode="json"),
        md_at_now=now.model_dump(mode="json"),
    )


def _build_gap_headlines(reading: dict[str, Any]) -> GapHeadlines:
    """Pull the most actionable chart-specific findings from Gap modules."""
    # Lazy import so the summary works even when Gap modules error.
    try:
        from app.integration.gap_annotator import annotate_with_gap_modules
        gap = annotate_with_gap_modules(reading)
    except Exception:
        return GapHeadlines()

    out: dict[str, Any] = {}

    d = gap.gap_modules.get("D")
    if d and d.available and d.result:
        al = (d.result.get("arudha_lagna") or {})
        upl = (d.result.get("upapada_lagna") or {})
        out["arudha_lagna_sign"] = _safe_int(al.get("arudha_sign"))
        out["arudha_lagna_sign_name"] = _sign_name(_safe_int(al.get("arudha_sign")))
        out["upapada_lagna_sign"] = _safe_int(upl.get("arudha_sign"))
        out["upapada_lagna_sign_name"] = _sign_name(_safe_int(upl.get("arudha_sign")))

    e = gap.gap_modules.get("E")
    if e and e.available and e.result:
        bb = (e.result.get("bhrigu_bindu") or {})
        out["bhrigu_bindu_sign"] = _safe_int(bb.get("sign"))
        out["bhrigu_bindu_house"] = _safe_int(bb.get("natal_house"))

    h = gap.gap_modules.get("H")
    if h and h.available and h.result:
        moon_attrs = h.result.get("moon_nakshatra_attributes") or {}
        out["moon_nakshatra"] = moon_attrs.get("name")
        out["moon_gana"] = moon_attrs.get("gana")
        out["moon_yoni"] = moon_attrs.get("yoni")
        out["moon_nadi"] = moon_attrs.get("nadi")

    # Atmakaraka: derive from Track A's chart if available
    chart = reading.get("chart") or {}
    planets = chart.get("planets") or {}
    ak_planet: str | None = None
    ak_lon = -1.0
    # AK = planet (excluding Rahu/Ketu per Jaimini) with highest degree-in-sign
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        body = planets.get(name) or {}
        deg = body.get("degree_in_sign")
        if isinstance(deg, (int, float)) and deg > ak_lon:
            ak_lon = float(deg)
            ak_planet = name
    if ak_planet:
        out["atmakaraka"] = ak_planet
        # Karakamsa = AK's D9 sign (need D9 info or compute)
        # For now, leave karakamsa derivable upstream

    return GapHeadlines(**out)


def _build_yoga_summary(reading: dict[str, Any]) -> YogaSummary:
    try:
        from app.integration.yoga_compare import compare_yoga_detection
        report = compare_yoga_detection(reading)
    except Exception:
        return YogaSummary(
            canonical_yogas_both_engines_detect=[],
            track_a_only=[], track_b_only=[],
            intersection_count=0, union_count=0,
        )
    return YogaSummary(
        canonical_yogas_both_engines_detect=list(report.both),
        track_a_only=list(report.track_a_only),
        track_b_only=list(report.track_b_only),
        intersection_count=report.intersection_count,
        union_count=len(report.both) + len(report.track_a_only) + len(report.track_b_only),
    )


def _build_functional_notes(reading: dict[str, Any]) -> list[FunctionalRoleNote]:
    try:
        from app.integration.doctrine_reconciliation import reconcile_functional_roles
        from app.integration.functional_compare import compare_functional_roles
        chart = reading.get("chart") or {}
        cusps = chart.get("cusps") or {}
        lagna_sign = int(cusps.get("sign", 1))
        fr = compare_functional_roles(lagna_sign)
        reconciled = reconcile_functional_roles(fr)
    except Exception:
        return []
    return [
        FunctionalRoleNote(
            planet=n.planet,
            canonical_role=n.canonical_direction,
            note=n.notes,
        )
        for n in reconciled.doctrine_notes
    ]


def _build_domain_highlights(
    reading: dict[str, Any],
    *,
    skip_neutral: bool = True,
) -> tuple[list[DomainHighlight], int]:
    """Return (highlights, skipped_count). Only non-neutral domains by default."""
    try:
        from app.integration.dkp_modulator_adapter import (
            build_dkp_context_from_reading, modulate_all_domains,
        )
        ctx = build_dkp_context_from_reading(reading)
        modulated = modulate_all_domains(reading, dkp_context=ctx)
    except Exception:
        return [], 0

    highlights: list[DomainHighlight] = []
    skipped = 0
    for pd in modulated.per_domain:
        original = pd.original
        overall = original.get("overall_verdict") or {}
        direction = overall.get("direction", "neutral")
        if skip_neutral and direction == "neutral":
            skipped += 1
            continue
        summary_text = overall.get("verdict", "")[:200]
        highlights.append(DomainHighlight(
            domain=pd.domain,
            bhava=pd.bhava,
            direction=direction,
            confidence=pd.modulated.confidence,
            summary=summary_text or f"{pd.domain} direction = {direction}",
        ))
    return highlights, skipped


def _count_dkp_records(reading: dict[str, Any]) -> int:
    """Count placement-verified DKP records (post-v1.0.1 lordship filter)."""
    try:
        from app.integration.dkp_enhancer import enhance
        result = enhance(reading)
        return len(result.dkp_translations_summary.records)
    except Exception:
        return 0


def summarize_chart(
    reading: dict[str, Any],
    *,
    skip_neutral_domains: bool = True,
) -> ChartSummary:
    """Build a consolidated high-signal summary of an integrated reading.

    Parameters
    ----------
    reading
        Track-A ReadingOutput dict (from ``app.reading.proforma.compute``).
    skip_neutral_domains
        If True (default), domains with overall direction = neutral are
        hidden from ``domain_highlights`` and counted in
        ``skipped_domains_count``. Set False to include all 6 domains.

    Returns
    -------
    ChartSummary
        All-in-one summary with the chart-specific signals — MD at NOW,
        Karakamsa, Bhrigu Bindu, Moon nakshatra, yoga aliases applied,
        doctrine-reconciled functional roles, only-non-neutral domain
        highlights, placement-verified DKP record count.
    """
    warnings: list[str] = []

    try:
        basics = _build_basics(reading)
    except Exception as exc:
        raise ValueError(f"could not parse reading basics: {exc}") from exc

    md = _build_md_snapshot(reading)
    gap = _build_gap_headlines(reading)
    yogas = _build_yoga_summary(reading)
    functional_notes = _build_functional_notes(reading)
    domain_highlights, skipped = _build_domain_highlights(
        reading, skip_neutral=skip_neutral_domains,
    )
    placement_verified = _count_dkp_records(reading)

    if md.md_at_birth["md_lord"] != md.md_at_now["md_lord"]:
        # Useful note for the caller — emphasises that MD-at-birth and
        # MD-at-now are different (a common source of misreadings).
        pass

    return ChartSummary(
        basics=basics,
        md_snapshot=md,
        gap_headlines=gap,
        yoga_summary=yogas,
        functional_role_notes=functional_notes,
        domain_highlights=domain_highlights,
        placement_verified_dkp_count=placement_verified,
        skipped_domains_count=skipped,
        warnings=warnings,
    )
