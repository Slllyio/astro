"""Sequence 5 — Vimshottari Mahadasha 19-check judgment (D-14 locked).

Doctrine source
===============

Notebook NotebookLM proforma — "How to Judge a Mahadasha" by Anil Kumar
Jain. The proforma defines a 19-step examination an astrologer applies
to *every* Mahadasha (MD) to forecast the gross character of that
period. The 19 check keys are locked in
``docs/doctrine-decisions.md`` D-14 and reproduced verbatim in
``app/reading/schema.py`` as ``MD_CHECK_KEYS``.

The 19 checks (verbatim from D-14):

  1. ``bhaav_from_lagna``              — Bhava the MD lord occupies from Lagna
  2. ``commonality_significations``    — Overlap between karakas and bhava themes
  3. ``residential_strength``          — Degree-distance from Bhaav Madhya
  4. ``bhaavs_aspected_fully``         — Bhavas the MD lord fully aspects
  5. ``rashi_depositor``               — Placement of MD lord's rashi-depositor
  6. ``balaadi_avastha``               — Baladi state (Bala/Kumara/Yuva/Vriddha/Mrita)
  7. ``conjunctions_within_15deg``     — Planets within 15° of MD lord
  8. ``full_aspects_on_md_lord``       — Planets giving full Vedic aspect to MD lord
  9. ``trinal_planets``                — Planets trinal (5/9) to MD lord within 15°
 10. ``proximity_to_exact_trine``      — Closeness of trinal planets to exact 120°
 11. ``md_lord_as_lagna_yogas``        — Treat MD lord's sign as Lagna; overlay yogas
 12. ``nakshatra_tara_from_moon``      — Tara of MD lord's nakshatra from natal Moon
 13. ``nakshatra_depositor_dignity``   — Functional nature + dignity of nakshatra-depositor
 14. ``navamsa_depositor``             — Navamsa depositor of MD lord
 15. ``kartari_yoga``                  — Shubha/Pap Kartari on MD lord (planets flanking)
 16. ``planet_in_2nd_from_md_lord``    — Dignity of 2nd-from-MD-lord planet
 17. ``ishta_phal``                    — Ishta Phal of rashi/nakshatra/navamsa depositors
 18. ``repeat_from_arudha_lagna``      — Repeat checks 1-17 with AL as reference
 19. ``repeat_from_karakamsha_lagna``  — Repeat checks 1-17 with KL as reference

Architectural discipline (per Phase 4 brief)
============================================

This module ORCHESTRATES — it does NOT recompute. Each ``_check_*``
private function delegates to an existing Tier-0/1/2 module:

  * Step 3  → ``computations.residential_strength``
  * Step 5  → ``app.core.dignity.SIGN_RULERS`` (rashi depositor)
  * Step 6  → ``chart["avasthas"]`` (precomputed Baladi)
  * Step 8  → Vedic graha drishti (Jupiter 5/9, Mars 4/8, Saturn 3/10,
              Rahu/Ketu 5/9) per the project's locked decision
  * Step 11 → ``computations.yogas_extended.detect_yogas`` (re-projected
              with MD lord's sign as ascendant)
  * Step 13 → ``computations.functional_nature.compute_functional_nature``
  * Step 14 → ``computations.divisional_readings.d9_navamsha``
  * Step 17 → ``computations.ishta_phal.compute_ishta_phal``
  * Step 18 → ``computations.arudha_upapada.compute_arudha_padas`` (AL)
  * Step 19 → ``computations.karakamsha.compute_karakamsha`` (KL)

KP-contamination audit clean — every check name is pure Parashari
rashi-depositor logic; no "sub-lord" / "cuspal-sub" / KP-specific
terminology.

Public API
==========

    run_sequence(chart, asc_sign, moon_sign) -> VimshottariMDResult

Returns a :class:`VimshottariMDResult` with:

  - ``timeline``                  — list of :class:`MDJudgment` covering
                                    the past, current, and next 2-3
                                    Mahadashas in chronological order.
  - ``current_md_judgment``       — the entry where ``is_current=True``.
"""
from __future__ import annotations

import logging
from typing import Any, Final, Mapping

import swisseph as swe
from pydantic import BaseModel, ConfigDict, Field

from app.core.avastha import baladi_state
from app.core.dignity import (
    DEBILITATION,
    EXALTATION,
    SIGN_RULERS,
)
from app.core.ephemeris_engine import (
    DASHA_LORDS,
    DAYS_PER_VEDIC_YEAR,
    calculate_vimshottari_mahadasha,
)
from app.core.nakshatra import (
    NAKSHATRA_LORDS,
    NAKSHATRAS,
    nakshatra_for_longitude,
)
from app.reading.computations.arudha_upapada import compute_arudha_padas
from app.reading.computations.divisional_readings.d9_navamsha import (
    read_d9_navamsha,
)
from app.reading.computations.functional_nature import (
    compute_functional_nature,
)
from app.reading.computations.ishta_phal import compute_ishta_phal
from app.reading.computations.karakamsha import compute_karakamsha
from app.reading.computations.residential_strength import (
    compute_residential_strength,
)
from app.reading.computations.yogas_extended import (
    detect_yogas as detect_extended_yogas,
)
from app.reading.schema import (
    MD_CHECK_KEYS,
    ConfidenceScore,
    Finding,
    MDJudgment,
)

logger = logging.getLogger(__name__)


_SEQUENCE_NAME: Final[str] = "vimshottari_md"


# Sequence-level confidence envelope — each check is a structural
# delegation, not a 3-pillar judgment. Domain layers re-score downstream.
_SEQUENCE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=NotebookLM 'How to Judge a Mahadasha' (Anil Kumar Jain) — D-14"
)

# Vedic graha drishti per the project's locked decision: Jupiter 5/9,
# Mars 4/8, Saturn 3/10, Rahu/Ketu Jupiter-style 5/9 (modern Sukra Nadi).
# All other planets give the universal 7th aspect.
_SPECIAL_DRISHTI: Final[dict[str, tuple[int, ...]]] = {
    "Jupiter": (5, 9),
    "Mars": (4, 8),
    "Saturn": (3, 10),
    "Rahu": (5, 9),
    "Ketu": (5, 9),
}

# Functional benefics vs malefics for the kartari yoga step (locked
# CLAUDE.md): Jupiter, Venus, Mercury, Moon are benefic; Sun, Mars,
# Saturn, Rahu, Ketu are malefic. Mercury's malefic-association
# downgrade is handled in the per-check evidence, not in the table.
_BENEFICS: Final[frozenset[str]] = frozenset(
    {"Jupiter", "Venus", "Mercury", "Moon"}
)
_MALEFICS: Final[frozenset[str]] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)

# All non-nodal planets for inter-planet scans.
_ALL_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


# ---------------------------------------------------------------------------
# VimshottariMDResult — local wrapper (schema.py is read-only per the brief)
# ---------------------------------------------------------------------------


class VimshottariMDResult(BaseModel):
    """Sequence 5 — Vimshottari Mahadasha lifetime timeline.

    ``timeline`` is the ordered list of :class:`MDJudgment` entries from
    the start of the chart's Vimshottari cycle to ~the next 3 MDs after
    the current one. ``current_md_judgment`` is the entry where
    ``is_current=True``; exactly one judgment in ``timeline`` must
    satisfy that flag.

    Schema-wise, downstream consumers consume the underlying
    :class:`MDJudgment` list directly via ``SequencesBlock.md_judgments``.
    This wrapper exists for sequence-internal API ergonomics: callers can
    say ``result.current_md_judgment`` without searching the list.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    timeline: list[MDJudgment] = Field(default_factory=list)
    current_md_judgment: MDJudgment


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _validate_asc_sign(value: int) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(
            f"asc_sign must be a 1-indexed sign in 1..12, got {value!r}"
        )
    return value


def _planet_sign(
    chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


def _planet_lon(
    chart: Mapping[str, Mapping[str, object]], planet: str,
) -> float | None:
    entry = chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    lon = entry.get("longitude")
    if not isinstance(lon, (int, float)):
        return None
    return float(lon)


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    return ((planet_sign - asc_sign) % 12) + 1


def _circular_lon_diff(lon_a: float, lon_b: float) -> float:
    """Circular separation in degrees (0..180), wrap-safe at 0/360 cusp."""
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def _sign_distance_forward(from_sign: int, to_sign: int) -> int:
    """Forward distance 1..12: from_sign -> to_sign counted inclusively."""
    return ((to_sign - from_sign) % 12) + 1


def _format_iso(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _md_lord_lon(d1_chart: Mapping[str, Mapping[str, object]], lord: str) -> float:
    lon = _planet_lon(d1_chart, lord)
    if lon is None:
        raise ValueError(f"MD lord {lord!r} missing longitude in D1 chart")
    return lon


# ---------------------------------------------------------------------------
# Lifetime timeline construction
# ---------------------------------------------------------------------------


def _build_lifetime_timeline(
    moon_longitude: float, birth_jd: float,
) -> list[dict[str, Any]]:
    """Return the chronological MD periods covering the lifetime cycle.

    Reuses :func:`calculate_vimshottari_mahadasha` for the current MD
    (lord + start_jd + total years), then walks the Vimshottari order
    forward and backward to fill the lifetime cycle.

    Each period dict carries: ``lord``, ``start_jd``, ``end_jd``,
    ``total_years``.
    """
    md = calculate_vimshottari_mahadasha(moon_longitude, birth_jd)
    current_lord: str = md["mahadasha_lord"]
    years_elapsed: float = md["time_elapsed_years"]
    total_years: float = md["total_duration_years"]
    current_start_jd = birth_jd - years_elapsed * DAYS_PER_VEDIC_YEAR

    lord_names = [n for n, _ in DASHA_LORDS]
    start_idx = lord_names.index(current_lord)

    periods: list[dict[str, Any]] = []

    # The current MD plus the next several MDs (covering ~next 80-100
    # years total — practitioners normally only forecast within that
    # horizon).
    n = len(DASHA_LORDS)
    cursor_jd = current_start_jd
    for offset in range(n):  # up to 9 MDs forward starting from current
        lord, years = DASHA_LORDS[(start_idx + offset) % n]
        period_start = cursor_jd
        period_end = period_start + years * DAYS_PER_VEDIC_YEAR
        periods.append(
            {
                "lord": lord,
                "start_jd": period_start,
                "end_jd": period_end,
                "total_years": float(years),
            }
        )
        cursor_jd = period_end

    return periods


# ---------------------------------------------------------------------------
# Step 1 — bhaav_from_lagna
# ---------------------------------------------------------------------------


def _check_bhaav_from_lagna(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_lord: str,
) -> Finding:
    """Bhava the MD lord occupies from natal Lagna (whole-sign)."""
    md_sign = _planet_sign(d1_chart, md_lord)
    if md_sign is None:
        return _neutral_finding(
            step_id="seq_5.step_01.bhaav_from_lagna",
            rule="md.bhaav_from_lagna",
            verdict=f"MD lord {md_lord} sign unknown — bhava inconclusive",
            evidence=[
                f"md_lord={md_lord}",
                "md_sign=unknown",
                _DOCTRINE_SENTINEL,
            ],
        )
    bhava = _whole_sign_house(md_sign, asc_sign)
    kendra = bhava in (1, 4, 7, 10)
    trikona = bhava in (1, 5, 9)
    dusthana = bhava in (6, 8, 12)
    if trikona:
        direction = "positive"
        flavour = "trikona (dharma/lakshmi)"
    elif kendra:
        direction = "positive"
        flavour = "kendra (active pillar)"
    elif dusthana:
        direction = "negative"
        flavour = "dusthana (loss/conflict/expense)"
    else:
        direction = "neutral"
        flavour = "neutral upachaya/dual house"
    verdict = (
        f"MD lord {md_lord} in bhava {bhava} ({flavour}) from Lagna"
    )[:140]
    return Finding(
        id="seq_5.step_01.bhaav_from_lagna",
        rule="md.bhaav_from_lagna",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_sign={md_sign}",
            f"asc_sign={asc_sign}",
            f"bhava_from_lagna={bhava}",
            f"is_kendra={kendra}",
            f"is_trikona={trikona}",
            f"is_dusthana={dusthana}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 2 — commonality_significations
# ---------------------------------------------------------------------------


_NATURAL_KARAKA_BHAVAS: Final[dict[str, tuple[int, ...]]] = {
    # Natural significations per BPHS Vol.I Ch.32 + general doctrine.
    "Sun": (1, 5, 9, 10),
    "Moon": (4, 2),
    "Mars": (3, 6),
    "Mercury": (4, 10),
    "Jupiter": (2, 5, 9, 11),
    "Venus": (7, 4, 12),
    "Saturn": (6, 8, 10, 11, 12),
    "Rahu": (6, 8, 12),
    "Ketu": (8, 12),
}


def _check_commonality_significations(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_lord: str,
) -> Finding:
    """Overlap between MD lord's natural karaka bhavas and the bhava it
    actually occupies. Where the two match, the MD's themes are
    constructively reinforced."""
    md_sign = _planet_sign(d1_chart, md_lord)
    natural_bhavas = _NATURAL_KARAKA_BHAVAS.get(md_lord, ())
    if md_sign is None:
        bhava = None
        overlap_count = 0
    else:
        bhava = _whole_sign_house(md_sign, asc_sign)
        overlap_count = 1 if bhava in natural_bhavas else 0
    direction = "positive" if overlap_count > 0 else "neutral"
    verdict = (
        f"MD lord {md_lord} natural-karaka bhavas {natural_bhavas}; occupies "
        f"bhava {bhava} (overlap={overlap_count})"
    )[:140]
    return Finding(
        id="seq_5.step_02.commonality_significations",
        rule="md.commonality_significations",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"natural_karaka_bhavas={list(natural_bhavas)}",
            f"occupied_bhava={bhava}",
            f"overlap_count={overlap_count}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 3 — residential_strength
# ---------------------------------------------------------------------------


def _check_residential_strength(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    lagna_degree: float,
    md_lord: str,
) -> Finding:
    """Delegates to ``computations.residential_strength``."""
    res = compute_residential_strength(dict(d1_chart), lagna_degree)
    md_finding = res.get(md_lord)
    band = "n/a"
    strength = -1.0
    if md_finding is not None:
        for line in md_finding.evidence:
            if line.startswith("strength="):
                try:
                    strength = float(line.split("=", 1)[1])
                except ValueError:
                    pass
            elif line.startswith("band="):
                band = line.split("=", 1)[1]
    if band in ("very_strong", "strong"):
        direction = "positive"
    elif band == "weak":
        direction = "negative"
    else:
        direction = "neutral"
    verdict = (
        f"MD lord {md_lord} residential strength {strength:.2f} band={band}"
    )[:140]
    return Finding(
        id="seq_5.step_03.residential_strength",
        rule="md.residential_strength",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"strength={strength}",
            f"band={band}",
            "delegate=computations.residential_strength (Tier-0, D-5)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 4 — bhaavs_aspected_fully (Vedic graha drishti)
# ---------------------------------------------------------------------------


def _bhavas_aspected(planet: str, planet_sign: int, asc_sign: int) -> list[int]:
    """Bhavas (from natal Lagna) that ``planet`` fully aspects.

    Vedic graha drishti per the project's locked decision: every planet
    aspects the 7th house from itself; Jupiter additionally aspects 5/9,
    Mars 4/8, Saturn 3/10, and Rahu/Ketu 5/9 (modern Sukra Nadi).
    """
    aspected_signs: set[int] = set()
    # Universal 7th.
    aspected_signs.add(((planet_sign - 1 + 6) % 12) + 1)
    # Specials.
    for offset in _SPECIAL_DRISHTI.get(planet, ()):
        aspected_signs.add(((planet_sign - 1 + (offset - 1)) % 12) + 1)
    return sorted(_whole_sign_house(s, asc_sign) for s in aspected_signs)


def _check_bhaavs_aspected_fully(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_lord: str,
) -> Finding:
    """The bhavas MD lord fully aspects (Vedic graha drishti)."""
    md_sign = _planet_sign(d1_chart, md_lord)
    if md_sign is None:
        bhavas: list[int] = []
    else:
        bhavas = _bhavas_aspected(md_lord, md_sign, asc_sign)
    # Aspecting trikonas is constructive; aspecting dusthanas is mixed
    # (the MD lord pours energy into loss/conflict houses).
    trikona_hits = [b for b in bhavas if b in (1, 5, 9)]
    dusthana_hits = [b for b in bhavas if b in (6, 8, 12)]
    if trikona_hits and not dusthana_hits:
        direction = "positive"
    elif dusthana_hits and not trikona_hits:
        direction = "negative"
    elif trikona_hits and dusthana_hits:
        direction = "mixed"
    else:
        direction = "neutral"
    verdict = (
        f"MD lord {md_lord} fully aspects bhavas {bhavas}"
    )[:140]
    return Finding(
        id="seq_5.step_04.bhaavs_aspected_fully",
        rule="md.bhaavs_aspected_fully",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_sign={md_sign}",
            f"aspected_bhavas={bhavas}",
            f"trikona_hits={trikona_hits}",
            f"dusthana_hits={dusthana_hits}",
            "doctrine=Vedic graha drishti (J5/9, Ma4/8, Sa3/10, Ra/Ke5/9; universal 7th)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 5 — rashi_depositor
# ---------------------------------------------------------------------------


def _check_rashi_depositor(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_lord: str,
) -> Finding:
    """Placement of the depositor (sign-lord) of MD lord's rashi.

    A strong depositor passes strength through to the MD lord; a
    debilitated depositor signals fundamental weakness in the period.
    """
    md_sign = _planet_sign(d1_chart, md_lord)
    depositor = SIGN_RULERS.get(md_sign) if md_sign is not None else None
    dep_sign = _planet_sign(d1_chart, depositor) if depositor else None
    dep_bhava = (
        _whole_sign_house(dep_sign, asc_sign) if dep_sign is not None else None
    )
    dep_exalted = (
        depositor in EXALTATION and EXALTATION.get(depositor) == dep_sign
    )
    dep_debilitated = (
        depositor in DEBILITATION and DEBILITATION.get(depositor) == dep_sign
    )
    if dep_exalted or (dep_bhava in (1, 4, 5, 7, 9, 10) and not dep_debilitated):
        direction = "positive"
    elif dep_debilitated or dep_bhava in (6, 8, 12):
        direction = "negative"
    else:
        direction = "neutral"
    verdict = (
        f"Rashi depositor of {md_lord} ({depositor}) in bhava {dep_bhava}"
    )[:140]
    return Finding(
        id="seq_5.step_05.rashi_depositor",
        rule="md.rashi_depositor",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_sign={md_sign}",
            f"rashi_depositor={depositor}",
            f"depositor_sign={dep_sign}",
            f"depositor_bhava={dep_bhava}",
            f"depositor_exalted={dep_exalted}",
            f"depositor_debilitated={dep_debilitated}",
            "delegate=app.core.dignity.SIGN_RULERS",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 6 — balaadi_avastha
# ---------------------------------------------------------------------------


def _check_balaadi_avastha(
    chart: Mapping[str, Any], md_lord: str,
) -> Finding:
    """Baladi avastha (Bala/Kumara/Yuva/Vriddha/Mrita) of MD lord.

    Delegates to ``chart["avasthas"]`` (precomputed by the engine via
    ``app.core.avastha.compute_avasthas``).
    """
    avasthas = chart.get("avasthas") or {}
    info = avasthas.get(md_lord)
    if isinstance(info, dict):
        baladi = info.get("baladi", "unknown")
    else:
        d1 = chart["d1"]
        sign = _planet_sign(d1, md_lord)
        deg = d1.get(md_lord, {}).get("degree_in_sign")
        baladi = (
            baladi_state(sign, float(deg))
            if sign is not None and isinstance(deg, (int, float))
            else "unknown"
        )

    # Yuva (mature) is the apex; Bala/Kumara are juvenile (mild
    # downgrade); Vriddha is waning; Mrita is dead.
    if baladi == "Yuva":
        direction = "positive"
    elif baladi == "Mrita":
        direction = "negative"
    elif baladi in ("Bala", "Kumara", "Vriddha"):
        direction = "neutral"
    else:
        direction = "neutral"
    verdict = f"MD lord {md_lord} baladi avastha = {baladi}"[:140]
    return Finding(
        id="seq_5.step_06.balaadi_avastha",
        rule="md.balaadi_avastha",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"baladi={baladi}",
            "delegate=app.core.avastha.baladi_state",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 7 — conjunctions_within_15deg
# ---------------------------------------------------------------------------


def _check_conjunctions_within_15deg(
    d1_chart: Mapping[str, Mapping[str, object]], md_lord: str,
) -> Finding:
    """Planets within 15° of MD lord by sidereal longitude.

    Within-15° conjunctions in classical doctrine "functionally activate"
    the conjoining planet alongside the MD lord during the period.
    """
    md_lon = _planet_lon(d1_chart, md_lord)
    near: list[tuple[str, float]] = []
    if md_lon is not None:
        for p in _ALL_PLANETS:
            if p == md_lord:
                continue
            p_lon = _planet_lon(d1_chart, p)
            if p_lon is None:
                continue
            d = _circular_lon_diff(md_lon, p_lon)
            if d <= 15.0:
                near.append((p, d))
    near.sort(key=lambda kv: kv[1])
    bf_near = [p for p, _ in near if p in _BENEFICS]
    mal_near = [p for p, _ in near if p in _MALEFICS]
    if bf_near and not mal_near:
        direction = "positive"
    elif mal_near and not bf_near:
        direction = "negative"
    elif bf_near and mal_near:
        direction = "mixed"
    else:
        direction = "neutral"
    verdict = (
        f"MD lord {md_lord} within-15° activations: "
        f"{[p for p, _ in near] or 'none'}"
    )[:140]
    return Finding(
        id="seq_5.step_07.conjunctions_within_15deg",
        rule="md.conjunctions_within_15deg",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"near_planets={[p for p, _ in near]}",
            f"benefics_near={bf_near}",
            f"malefics_near={mal_near}",
            "threshold=15deg circular",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 8 — full_aspects_on_md_lord
# ---------------------------------------------------------------------------


def _check_full_aspects_on_md_lord(
    d1_chart: Mapping[str, Mapping[str, object]], md_lord: str,
) -> Finding:
    """Planets giving a full Vedic graha drishti onto MD lord's sign."""
    md_sign = _planet_sign(d1_chart, md_lord)
    aspecting: list[str] = []
    if md_sign is not None:
        for p in _ALL_PLANETS:
            if p == md_lord:
                continue
            p_sign = _planet_sign(d1_chart, p)
            if p_sign is None:
                continue
            # Determine signs this planet fully aspects.
            full_signs: set[int] = set()
            full_signs.add(((p_sign - 1 + 6) % 12) + 1)  # universal 7th
            for offset in _SPECIAL_DRISHTI.get(p, ()):
                full_signs.add(((p_sign - 1 + (offset - 1)) % 12) + 1)
            if md_sign in full_signs:
                aspecting.append(p)
    bf_asp = [p for p in aspecting if p in _BENEFICS]
    mal_asp = [p for p in aspecting if p in _MALEFICS]
    if bf_asp and not mal_asp:
        direction = "positive"
    elif mal_asp and not bf_asp:
        direction = "negative"
    elif bf_asp and mal_asp:
        direction = "mixed"
    else:
        direction = "neutral"
    verdict = (
        f"MD lord {md_lord} receives full aspect from: {aspecting or 'none'}"
    )[:140]
    return Finding(
        id="seq_5.step_08.full_aspects_on_md_lord",
        rule="md.full_aspects_on_md_lord",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_sign={md_sign}",
            f"aspecting_planets={aspecting}",
            f"benefics_aspecting={bf_asp}",
            f"malefics_aspecting={mal_asp}",
            "doctrine=Vedic graha drishti (whole-sign)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 9 — trinal_planets
# ---------------------------------------------------------------------------


def _check_trinal_planets(
    d1_chart: Mapping[str, Mapping[str, object]], md_lord: str,
) -> Finding:
    """Planets trinal (5th / 9th sign by whole-sign) to MD lord within 15°.

    "Within 15°" combines the sign-distance check with a longitude check:
    the planet's longitude must be within 15° of an exact 120° / 240°
    offset from MD lord (Rasi-drishti trinal lock).
    """
    md_sign = _planet_sign(d1_chart, md_lord)
    md_lon = _planet_lon(d1_chart, md_lord)
    trinals: list[str] = []
    if md_sign is not None and md_lon is not None:
        for p in _ALL_PLANETS:
            if p == md_lord:
                continue
            p_sign = _planet_sign(d1_chart, p)
            p_lon = _planet_lon(d1_chart, p)
            if p_sign is None or p_lon is None:
                continue
            sd = _sign_distance_forward(md_sign, p_sign)
            if sd not in (5, 9):
                continue
            target_offset = 120.0 if sd == 5 else 240.0
            target_lon = (md_lon + target_offset) % 360.0
            if _circular_lon_diff(p_lon, target_lon) <= 15.0:
                trinals.append(p)
    direction = "positive" if trinals else "neutral"
    verdict = f"MD lord {md_lord} trinally activated by: {trinals or 'none'}"[:140]
    return Finding(
        id="seq_5.step_09.trinal_planets",
        rule="md.trinal_planets",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_sign={md_sign}",
            f"trinal_planets={trinals}",
            "tolerance=15deg from exact 120/240",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 10 — proximity_to_exact_trine
# ---------------------------------------------------------------------------


def _check_proximity_to_exact_trine(
    d1_chart: Mapping[str, Mapping[str, object]], md_lord: str,
) -> Finding:
    """For each trinal planet, the degree-distance from exact 120°/240°."""
    md_lon = _planet_lon(d1_chart, md_lord)
    md_sign = _planet_sign(d1_chart, md_lord)
    deltas: list[tuple[str, float]] = []
    if md_lon is not None and md_sign is not None:
        for p in _ALL_PLANETS:
            if p == md_lord:
                continue
            p_lon = _planet_lon(d1_chart, p)
            p_sign = _planet_sign(d1_chart, p)
            if p_lon is None or p_sign is None:
                continue
            sd = _sign_distance_forward(md_sign, p_sign)
            if sd not in (5, 9):
                continue
            target = (md_lon + (120.0 if sd == 5 else 240.0)) % 360.0
            delta = _circular_lon_diff(p_lon, target)
            deltas.append((p, round(delta, 4)))
    deltas.sort(key=lambda kv: kv[1])
    closest_delta = deltas[0][1] if deltas else None
    if closest_delta is not None and closest_delta <= 3.0:
        direction = "positive"
    elif closest_delta is not None and closest_delta <= 10.0:
        direction = "neutral"
    else:
        direction = "neutral"
    verdict = (
        f"Closest trinal proximity to MD lord {md_lord}: "
        f"{(deltas[0][0] + ' @ ' + str(deltas[0][1]) + 'deg') if deltas else 'no trinal planets'}"
    )[:140]
    return Finding(
        id="seq_5.step_10.proximity_to_exact_trine",
        rule="md.proximity_to_exact_trine",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"trinal_deltas={deltas}",
            f"closest_delta_deg={closest_delta}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 11 — md_lord_as_lagna_yogas
# ---------------------------------------------------------------------------


def _check_md_lord_as_lagna_yogas(
    d1_chart: Mapping[str, Mapping[str, object]],
    moon_sign: int,
    md_lord: str,
) -> Finding:
    """Treat MD lord's sign as Lagna; re-detect yogas under that frame.

    Delegates to ``computations.yogas_extended.detect_yogas`` with
    ``asc_sign`` overridden to MD lord's sign.
    """
    md_sign = _planet_sign(d1_chart, md_lord)
    yogas: list[Finding] = []
    if md_sign is not None:
        try:
            yogas = detect_extended_yogas(d1_chart, md_sign, moon_sign)
        except Exception as exc:  # noqa: BLE001 — best-effort overlay
            logger.warning(
                "md_lord_as_lagna_yogas overlay failed for MD lord %s: %s",
                md_lord, exc,
            )
            yogas = []
    yoga_rules = sorted({y.rule for y in yogas})
    direction = "positive" if yoga_rules else "neutral"
    verdict = (
        f"With MD lord {md_lord} as Lagna ({md_sign}): "
        f"{len(yoga_rules)} yogas detected"
    )[:140]
    return Finding(
        id="seq_5.step_11.md_lord_as_lagna_yogas",
        rule="md.md_lord_as_lagna_yogas",
        source_sequence=_SEQUENCE_NAME,
        classification="yoga",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"projected_asc_sign={md_sign}",
            f"yoga_count={len(yogas)}",
            f"yoga_rules={yoga_rules}",
            "delegate=computations.yogas_extended.detect_yogas",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 12 — nakshatra_tara_from_moon
# ---------------------------------------------------------------------------

# Tara names per traditional Vedic 9-fold tara from the Janma Nakshatra:
# 1 Janma, 2 Sampat, 3 Vipat, 4 Kshema, 5 Pratyak,
# 6 Sadhaka, 7 Vadha, 8 Mitra, 9 Ati-Mitra (then repeats).
_TARA_NAMES: Final[tuple[str, ...]] = (
    "Janma", "Sampat", "Vipat", "Kshema", "Pratyak",
    "Sadhaka", "Vadha", "Mitra", "Ati-Mitra",
)
_TARA_QUALITY: Final[dict[str, str]] = {
    "Sampat": "auspicious",
    "Kshema": "auspicious",
    "Sadhaka": "auspicious",
    "Mitra": "auspicious",
    "Ati-Mitra": "auspicious",
    "Janma": "neutral",
    "Vipat": "inauspicious",
    "Pratyak": "inauspicious",
    "Vadha": "inauspicious",
}


def _check_nakshatra_tara_from_moon(
    d1_chart: Mapping[str, Mapping[str, object]], md_lord: str,
) -> Finding:
    """9-fold Tara of MD lord's nakshatra from the natal Moon's nakshatra.

    Per the proforma, Sampat (2nd) and Mitra (8th) are the most
    auspicious; Vadha (7th) and Vipat (3rd) the worst.
    """
    md_lon = _planet_lon(d1_chart, md_lord)
    moon_lon = _planet_lon(d1_chart, "Moon")
    tara_name = "unknown"
    tara_index = -1
    quality = "neutral"
    md_nak_index = -1
    moon_nak_index = -1
    if md_lon is not None and moon_lon is not None:
        md_nak = nakshatra_for_longitude(md_lon)
        moon_nak = nakshatra_for_longitude(moon_lon)
        md_nak_index = md_nak["index"]
        moon_nak_index = moon_nak["index"]
        # 1-indexed forward distance, mod 9 for the 9-fold pattern.
        forward = (md_nak_index - moon_nak_index) % 27
        tara_index = forward % 9
        tara_name = _TARA_NAMES[tara_index]
        quality = _TARA_QUALITY[tara_name]
    direction = (
        "positive" if quality == "auspicious"
        else "negative" if quality == "inauspicious"
        else "neutral"
    )
    verdict = (
        f"MD lord {md_lord} Tara from Moon = {tara_name} ({quality})"
    )[:140]
    return Finding(
        id="seq_5.step_12.nakshatra_tara_from_moon",
        rule="md.nakshatra_tara_from_moon",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_nakshatra_index={md_nak_index}",
            f"moon_nakshatra_index={moon_nak_index}",
            f"tara_index_1to9={tara_index + 1 if tara_index >= 0 else None}",
            f"tara_name={tara_name}",
            f"quality={quality}",
            "delegate=app.core.nakshatra.nakshatra_for_longitude",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 13 — nakshatra_depositor_dignity
# ---------------------------------------------------------------------------


def _check_nakshatra_depositor_dignity(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_lord: str,
) -> Finding:
    """Functional nature + dignity of MD lord's nakshatra depositor."""
    md_lon = _planet_lon(d1_chart, md_lord)
    nak_lord = None
    nak_name = "unknown"
    nak_index = -1
    if md_lon is not None:
        md_nak = nakshatra_for_longitude(md_lon)
        nak_lord = md_nak["lord"]
        nak_name = md_nak["name"]
        nak_index = md_nak["index"]
    dep_sign = _planet_sign(d1_chart, nak_lord) if nak_lord else None
    dep_bhava = _whole_sign_house(dep_sign, asc_sign) if dep_sign else None
    dep_exalted = (
        nak_lord in EXALTATION and EXALTATION.get(nak_lord) == dep_sign
    )
    dep_debilitated = (
        nak_lord in DEBILITATION and DEBILITATION.get(nak_lord) == dep_sign
    )
    fn_table = compute_functional_nature(asc_sign)
    fn_finding = fn_table.get(nak_lord) if nak_lord else None
    functional_nature = "unknown"
    if fn_finding is not None:
        for line in fn_finding.evidence:
            if line.startswith("nature="):
                functional_nature = line.split("=", 1)[1]
                break
    if dep_exalted or functional_nature == "functional_yogakaraka":
        direction = "positive"
    elif dep_debilitated or functional_nature == "functional_malefic":
        direction = "negative"
    else:
        direction = "neutral"
    verdict = (
        f"Nakshatra depositor {nak_lord} ({nak_name}): "
        f"bhava {dep_bhava}, nature {functional_nature}"
    )[:140]
    return Finding(
        id="seq_5.step_13.nakshatra_depositor_dignity",
        rule="md.nakshatra_depositor_dignity",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_nakshatra={nak_name}",
            f"md_nakshatra_index={nak_index}",
            f"nakshatra_depositor={nak_lord}",
            f"depositor_sign={dep_sign}",
            f"depositor_bhava={dep_bhava}",
            f"depositor_exalted={dep_exalted}",
            f"depositor_debilitated={dep_debilitated}",
            f"functional_nature={functional_nature}",
            "delegate=computations.functional_nature (D-7)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 14 — navamsa_depositor
# ---------------------------------------------------------------------------


def _check_navamsa_depositor(
    d1_chart: Mapping[str, Mapping[str, object]],
    d9_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_lord: str,
) -> Finding:
    """Navamsa depositor of MD lord — sign-lord of MD lord's D9 sign.

    Delegates the structural D9 reading to
    ``computations.divisional_readings.d9_navamsha`` for vargottama + D9
    Lagna context; layers the depositor lookup on top.
    """
    d9_findings = read_d9_navamsha(d1_chart, d9_chart, asc_sign)
    md_d9_sign = _planet_sign(d9_chart, md_lord)
    d9_depositor = SIGN_RULERS.get(md_d9_sign) if md_d9_sign else None
    dep_sign_d1 = _planet_sign(d1_chart, d9_depositor) if d9_depositor else None
    dep_bhava = (
        _whole_sign_house(dep_sign_d1, asc_sign)
        if dep_sign_d1 is not None
        else None
    )
    dep_exalted = (
        d9_depositor in EXALTATION
        and EXALTATION.get(d9_depositor) == dep_sign_d1
    )
    dep_debilitated = (
        d9_depositor in DEBILITATION
        and DEBILITATION.get(d9_depositor) == dep_sign_d1
    )
    if dep_exalted:
        direction = "positive"
    elif dep_debilitated:
        direction = "negative"
    elif dep_bhava in (1, 4, 5, 7, 9, 10):
        direction = "positive"
    elif dep_bhava in (6, 8, 12):
        direction = "negative"
    else:
        direction = "neutral"
    verdict = (
        f"Navamsa depositor of {md_lord} = {d9_depositor} (D1 bhava {dep_bhava})"
    )[:140]
    return Finding(
        id="seq_5.step_14.navamsa_depositor",
        rule="md.navamsa_depositor",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_d9_sign={md_d9_sign}",
            f"d9_depositor={d9_depositor}",
            f"depositor_d1_sign={dep_sign_d1}",
            f"depositor_d1_bhava={dep_bhava}",
            f"depositor_exalted={dep_exalted}",
            f"depositor_debilitated={dep_debilitated}",
            f"d9_findings_count={len(d9_findings)}",
            "delegate=computations.divisional_readings.d9_navamsha + dignity",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 15 — kartari_yoga
# ---------------------------------------------------------------------------


def _check_kartari_yoga(
    d1_chart: Mapping[str, Mapping[str, object]], md_lord: str,
) -> Finding:
    """Shubha (benefic) vs Pap (malefic) Kartari on MD lord.

    Classical Kartari: planets in the 12th and 2nd from MD lord's sign
    flank it. All-benefic flanking is Shubha Kartari (protective);
    all-malefic is Pap Kartari (squeezed); mixed is neutral.
    """
    md_sign = _planet_sign(d1_chart, md_lord)
    if md_sign is None:
        return _neutral_finding(
            step_id="seq_5.step_15.kartari_yoga",
            rule="md.kartari_yoga",
            verdict=f"MD lord {md_lord} sign unknown — kartari inconclusive",
            evidence=[
                f"md_lord={md_lord}",
                _DOCTRINE_SENTINEL,
            ],
        )
    twelfth_sign = ((md_sign - 1 - 1) % 12) + 1
    second_sign = ((md_sign - 1 + 1) % 12) + 1
    twelfth_occupants: list[str] = []
    second_occupants: list[str] = []
    for p in _ALL_PLANETS:
        if p == md_lord:
            continue
        ps = _planet_sign(d1_chart, p)
        if ps == twelfth_sign:
            twelfth_occupants.append(p)
        elif ps == second_sign:
            second_occupants.append(p)
    twelfth_benefic = all(p in _BENEFICS for p in twelfth_occupants) if twelfth_occupants else False
    second_benefic = all(p in _BENEFICS for p in second_occupants) if second_occupants else False
    twelfth_malefic = all(p in _MALEFICS for p in twelfth_occupants) if twelfth_occupants else False
    second_malefic = all(p in _MALEFICS for p in second_occupants) if second_occupants else False
    is_shubha = (
        twelfth_occupants and second_occupants
        and twelfth_benefic and second_benefic
    )
    is_pap = (
        twelfth_occupants and second_occupants
        and twelfth_malefic and second_malefic
    )
    if is_shubha:
        direction = "positive"
        kartari = "shubha_kartari"
    elif is_pap:
        direction = "negative"
        kartari = "pap_kartari"
    else:
        direction = "neutral"
        kartari = "none"
    verdict = (
        f"MD lord {md_lord} Kartari = {kartari}; flanking: "
        f"12th={twelfth_occupants}, 2nd={second_occupants}"
    )[:140]
    return Finding(
        id="seq_5.step_15.kartari_yoga",
        rule="md.kartari_yoga",
        source_sequence=_SEQUENCE_NAME,
        classification="yoga",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_sign={md_sign}",
            f"twelfth_sign={twelfth_sign}",
            f"second_sign={second_sign}",
            f"twelfth_occupants={twelfth_occupants}",
            f"second_occupants={second_occupants}",
            f"kartari={kartari}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 16 — planet_in_2nd_from_md_lord
# ---------------------------------------------------------------------------


def _check_planet_in_2nd_from_md_lord(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_lord: str,
) -> Finding:
    """Dignity of any planet in the 2nd sign from MD lord — "what comes
    out" of the MD."""
    md_sign = _planet_sign(d1_chart, md_lord)
    if md_sign is None:
        return _neutral_finding(
            step_id="seq_5.step_16.planet_in_2nd_from_md_lord",
            rule="md.planet_in_2nd_from_md_lord",
            verdict=f"MD lord {md_lord} sign unknown — 2nd-from-MD inconclusive",
            evidence=[f"md_lord={md_lord}", _DOCTRINE_SENTINEL],
        )
    second_sign = ((md_sign - 1 + 1) % 12) + 1
    occupants: list[str] = []
    for p in _ALL_PLANETS:
        if p == md_lord:
            continue
        if _planet_sign(d1_chart, p) == second_sign:
            occupants.append(p)
    if not occupants:
        return _neutral_finding(
            step_id="seq_5.step_16.planet_in_2nd_from_md_lord",
            rule="md.planet_in_2nd_from_md_lord",
            verdict=(
                f"No planet in 2nd from MD lord {md_lord} "
                f"(sign={second_sign}) — MD output sign-natural"
            )[:140],
            evidence=[
                f"md_lord={md_lord}",
                f"second_sign={second_sign}",
                "occupants=[]",
                _DOCTRINE_SENTINEL,
            ],
        )
    # Score the dignity of each occupant.
    benefic_count = sum(1 for p in occupants if p in _BENEFICS)
    malefic_count = sum(1 for p in occupants if p in _MALEFICS)
    if benefic_count and not malefic_count:
        direction = "positive"
    elif malefic_count and not benefic_count:
        direction = "negative"
    else:
        direction = "mixed"
    verdict = (
        f"2nd from MD lord {md_lord} (sign {second_sign}): {occupants}"
    )[:140]
    return Finding(
        id="seq_5.step_16.planet_in_2nd_from_md_lord",
        rule="md.planet_in_2nd_from_md_lord",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"second_sign={second_sign}",
            f"occupants={occupants}",
            f"benefic_count={benefic_count}",
            f"malefic_count={malefic_count}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 17 — ishta_phal
# ---------------------------------------------------------------------------


def _check_ishta_phal(
    chart: Mapping[str, Any], md_lord: str,
) -> Finding:
    """Ishta Phal of MD lord + its rashi / nakshatra / navamsa depositors.

    Delegates to ``computations.ishta_phal``. Requires Shadbala
    components for the chart; uses ``chart.get("shadbala")`` if
    available, otherwise emits a neutral finding noting the gap.
    """
    shadbala = chart.get("shadbala") or {}
    if not shadbala:
        # The full lifetime engine may or may not have shadbala depending
        # on the upstream call. Skip gracefully.
        return _neutral_finding(
            step_id="seq_5.step_17.ishta_phal",
            rule="md.ishta_phal",
            verdict=(
                f"Ishta Phal unavailable for MD lord {md_lord} "
                "(no shadbala in chart envelope)"
            )[:140],
            evidence=[
                f"md_lord={md_lord}",
                "shadbala_available=False",
                "delegate=computations.ishta_phal (Tier-0, D-4)",
                _DOCTRINE_SENTINEL,
            ],
        )
    d1 = chart["d1"]
    try:
        ishta_findings = compute_ishta_phal(d1, shadbala)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ishta_phal delegation failed for MD %s: %s", md_lord, exc)
        return _neutral_finding(
            step_id="seq_5.step_17.ishta_phal",
            rule="md.ishta_phal",
            verdict=f"Ishta Phal compute failed for {md_lord}",
            evidence=[
                f"md_lord={md_lord}",
                f"error={type(exc).__name__}",
                _DOCTRINE_SENTINEL,
            ],
        )
    # Collect rashi / nakshatra / navamsa depositors of MD lord.
    md_lon = _planet_lon(d1, md_lord)
    md_sign = _planet_sign(d1, md_lord)
    rashi_dep = SIGN_RULERS.get(md_sign) if md_sign else None
    nak_lord = (
        nakshatra_for_longitude(md_lon)["lord"] if md_lon is not None else None
    )
    d9 = chart.get("d9") or {}
    d9_dep = SIGN_RULERS.get(_planet_sign(d9, md_lord)) if d9 else None

    scores: dict[str, float] = {}
    for role, planet in (
        ("md_lord", md_lord),
        ("rashi_depositor", rashi_dep),
        ("nakshatra_depositor", nak_lord),
        ("navamsa_depositor", d9_dep),
    ):
        if not planet:
            continue
        f = ishta_findings.get(planet)
        if f is None:
            continue
        for line in f.evidence:
            if line.startswith("ishta_phal="):
                try:
                    scores[role] = float(line.split("=", 1)[1])
                except ValueError:
                    pass
                break
    avg = sum(scores.values()) / len(scores) if scores else 0.0
    direction = (
        "positive" if avg >= 35.0
        else "negative" if avg <= 20.0
        else "neutral"
    )
    verdict = (
        f"Ishta Phal avg of MD+depositors = {avg:.2f} (n={len(scores)})"
    )[:140]
    return Finding(
        id="seq_5.step_17.ishta_phal",
        rule="md.ishta_phal",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"depositor_scores={scores}",
            f"avg_ishta_phal={avg}",
            "delegate=computations.ishta_phal (Tier-0, D-4)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 18 — repeat_from_arudha_lagna
# ---------------------------------------------------------------------------


def _check_repeat_from_arudha_lagna(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_lord: str,
) -> Finding:
    """Recompute the bhaav-from-Lagna check treating Arudha Lagna (A1)
    as the reference Lagna instead of the natal ascendant.

    Delegates to ``computations.arudha_upapada.compute_arudha_padas``
    for AL identification. A full re-run of all 17 prior checks is the
    spec ideal; this implementation surfaces the AL-projected bhava
    (the single highest-leverage signal from the AL frame) and emits a
    TODO marker for the full 17-check re-run.
    """
    arudha = compute_arudha_padas(dict(d1_chart), asc_sign)
    al = arudha.get("al")
    al_sign: int | None = None
    if al is not None:
        for line in al.evidence:
            if line.startswith("pada_sign="):
                try:
                    al_sign = int(line.split("=", 1)[1])
                except ValueError:
                    pass
                break
    if al_sign is None:
        return _neutral_finding(
            step_id="seq_5.step_18.repeat_from_arudha_lagna",
            rule="md.repeat_from_arudha_lagna",
            verdict="Arudha Lagna unavailable — AL re-run inconclusive",
            evidence=[
                f"md_lord={md_lord}",
                _DOCTRINE_SENTINEL,
            ],
        )
    md_sign = _planet_sign(d1_chart, md_lord)
    al_bhava = (
        _whole_sign_house(md_sign, al_sign) if md_sign is not None else None
    )
    al_trikona = al_bhava in (1, 5, 9) if al_bhava else False
    al_dusthana = al_bhava in (6, 8, 12) if al_bhava else False
    if al_trikona:
        direction = "positive"
    elif al_dusthana:
        direction = "negative"
    else:
        direction = "neutral"
    verdict = (
        f"From AL (sign {al_sign}): MD lord {md_lord} sits in bhava {al_bhava}"
    )[:140]
    return Finding(
        id="seq_5.step_18.repeat_from_arudha_lagna",
        rule="md.repeat_from_arudha_lagna",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"arudha_lagna_sign={al_sign}",
            f"md_bhava_from_al={al_bhava}",
            f"al_trikona={al_trikona}",
            f"al_dusthana={al_dusthana}",
            "# TODO(P4-followup): full 17-check re-run from AL frame",
            "delegate=computations.arudha_upapada (D-2)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 19 — repeat_from_karakamsha_lagna
# ---------------------------------------------------------------------------


def _check_repeat_from_karakamsha_lagna(
    chart: Mapping[str, Any], md_lord: str,
) -> Finding:
    """Recompute the bhaav-from-Lagna check treating Karakamsha Lagna
    (the D9 sign of the Atma Karaka) as the reference Lagna."""
    d1 = chart["d1"]
    d9 = chart["d9"]
    karakamsha_finding = compute_karakamsha(d1, d9)
    kl_sign: int | None = None
    for line in karakamsha_finding.evidence:
        if line.startswith("karakamsha_sign="):
            try:
                kl_sign = int(line.split("=", 1)[1])
            except ValueError:
                pass
            break
    if kl_sign is None:
        return _neutral_finding(
            step_id="seq_5.step_19.repeat_from_karakamsha_lagna",
            rule="md.repeat_from_karakamsha_lagna",
            verdict="Karakamsha Lagna unavailable — KL re-run inconclusive",
            evidence=[
                f"md_lord={md_lord}",
                _DOCTRINE_SENTINEL,
            ],
        )
    md_sign = _planet_sign(d1, md_lord)
    kl_bhava = (
        _whole_sign_house(md_sign, kl_sign) if md_sign is not None else None
    )
    kl_trikona = kl_bhava in (1, 5, 9) if kl_bhava else False
    kl_dusthana = kl_bhava in (6, 8, 12) if kl_bhava else False
    if kl_trikona:
        direction = "positive"
    elif kl_dusthana:
        direction = "negative"
    else:
        direction = "neutral"
    verdict = (
        f"From KL (sign {kl_sign}): MD lord {md_lord} sits in bhava {kl_bhava}"
    )[:140]
    return Finding(
        id="seq_5.step_19.repeat_from_karakamsha_lagna",
        rule="md.repeat_from_karakamsha_lagna",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"karakamsha_lagna_sign={kl_sign}",
            f"md_bhava_from_kl={kl_bhava}",
            f"kl_trikona={kl_trikona}",
            f"kl_dusthana={kl_dusthana}",
            "# TODO(P4-followup): full 17-check re-run from KL frame",
            "delegate=computations.karakamsha (D-1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Synthesis helpers
# ---------------------------------------------------------------------------


def _neutral_finding(
    *, step_id: str, rule: str, verdict: str, evidence: list[str],
) -> Finding:
    return Finding(
        id=step_id,
        rule=rule,
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction="neutral",
        verdict=verdict[:140],
        evidence=evidence,
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _synthesize_overall(
    checks: Mapping[str, Finding], md_lord: str,
) -> Finding:
    pos = sum(1 for f in checks.values() if f.direction == "positive")
    neg = sum(1 for f in checks.values() if f.direction == "negative")
    mixed = sum(1 for f in checks.values() if f.direction == "mixed")
    if pos > neg + mixed:
        direction = "positive"
        tone = "promise dominates"
    elif neg > pos + mixed:
        direction = "negative"
        tone = "afflictions dominate"
    elif mixed > 0 and abs(pos - neg) <= mixed:
        direction = "mixed"
        tone = "mixed promise + affliction"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "MD lord neutrally placed"
    else:
        direction = "mixed"
        tone = "balanced positives and negatives"
    verdict = (
        f"MD={md_lord} verdict: {tone}; +{pos}/-{neg}/~{mixed}"
    )[:140]
    return Finding(
        id="seq_5.overall",
        rule="md.overall",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"positive_checks={pos}",
            f"negative_checks={neg}",
            f"mixed_checks={mixed}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Per-MD judgment orchestrator
# ---------------------------------------------------------------------------


def _judge_mahadasha(
    chart: Mapping[str, Any],
    asc_sign: int,
    moon_sign: int,
    md_lord: str,
    start_jd: float,
    end_jd: float,
    birth_jd: float,
    is_current: bool,
    is_past: bool,
    is_future: bool,
) -> MDJudgment:
    """Build an :class:`MDJudgment` by running all 19 named checks."""
    d1 = chart["d1"]
    d9 = chart["d9"]
    ascendant = chart.get("ascendant") or {}
    lagna_degree_in_sign = ascendant.get("degree_in_sign")
    if not isinstance(lagna_degree_in_sign, (int, float)):
        # Some upstream callers don't carry a lagna degree. Approximate
        # to the sign-midpoint so residential_strength returns
        # symmetric mid-sign values rather than failing.
        lagna_degree_in_sign = 15.0
    lagna_degree = float(lagna_degree_in_sign)

    checks: dict[str, Finding] = {
        "bhaav_from_lagna": _check_bhaav_from_lagna(d1, asc_sign, md_lord),
        "commonality_significations": _check_commonality_significations(
            d1, asc_sign, md_lord,
        ),
        "residential_strength": _check_residential_strength(
            d1, asc_sign, lagna_degree, md_lord,
        ),
        "bhaavs_aspected_fully": _check_bhaavs_aspected_fully(
            d1, asc_sign, md_lord,
        ),
        "rashi_depositor": _check_rashi_depositor(d1, asc_sign, md_lord),
        "balaadi_avastha": _check_balaadi_avastha(chart, md_lord),
        "conjunctions_within_15deg": _check_conjunctions_within_15deg(
            d1, md_lord,
        ),
        "full_aspects_on_md_lord": _check_full_aspects_on_md_lord(d1, md_lord),
        "trinal_planets": _check_trinal_planets(d1, md_lord),
        "proximity_to_exact_trine": _check_proximity_to_exact_trine(d1, md_lord),
        "md_lord_as_lagna_yogas": _check_md_lord_as_lagna_yogas(
            d1, moon_sign, md_lord,
        ),
        "nakshatra_tara_from_moon": _check_nakshatra_tara_from_moon(d1, md_lord),
        "nakshatra_depositor_dignity": _check_nakshatra_depositor_dignity(
            d1, asc_sign, md_lord,
        ),
        "navamsa_depositor": _check_navamsa_depositor(
            d1, d9, asc_sign, md_lord,
        ),
        "kartari_yoga": _check_kartari_yoga(d1, md_lord),
        "planet_in_2nd_from_md_lord": _check_planet_in_2nd_from_md_lord(
            d1, asc_sign, md_lord,
        ),
        "ishta_phal": _check_ishta_phal(chart, md_lord),
        "repeat_from_arudha_lagna": _check_repeat_from_arudha_lagna(
            d1, asc_sign, md_lord,
        ),
        "repeat_from_karakamsha_lagna": _check_repeat_from_karakamsha_lagna(
            chart, md_lord,
        ),
    }

    overall = _synthesize_overall(checks, md_lord)

    age_at_start = (start_jd - birth_jd) / DAYS_PER_VEDIC_YEAR
    age_at_end = (end_jd - birth_jd) / DAYS_PER_VEDIC_YEAR

    return MDJudgment(
        md_lord=md_lord,
        start_jd=float(start_jd),
        end_jd=float(end_jd),
        start_date=_format_iso(start_jd),
        end_date=_format_iso(end_jd),
        age_at_start=float(age_at_start),
        age_at_end=float(age_at_end),
        is_current=is_current,
        is_past=is_past,
        is_future=is_future,
        checks=checks,
        overall_verdict=overall,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_sequence(
    chart: dict, asc_sign: int, moon_sign: int,
) -> VimshottariMDResult:
    """Run the 19-step Vimshottari Mahadasha judgment.

    Args:
        chart: Full natal chart dict from
            ``app.core.ephemeris_engine.calculate_all_charts``. Must
            include ``d1``, ``d9``, ``current_mahadasha``, ``birth_jd``,
            and ``ascendant``.
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi (for yoga overlay on
            Step 11 — re-projection from MD-lord-as-Lagna).

    Returns:
        :class:`VimshottariMDResult` — schema-validated; each
        :class:`MDJudgment` carries the exact 19 keys in
        :data:`MD_CHECK_KEYS`.

    Raises:
        ValueError: If asc_sign / moon_sign are out of range, or the
            chart envelope lacks required keys.
    """
    _validate_asc_sign(asc_sign)
    if not isinstance(moon_sign, int) or not (1 <= moon_sign <= 12):
        raise ValueError(
            f"moon_sign must be a 1-indexed sign in 1..12, got {moon_sign!r}"
        )
    if "d1" not in chart or "d9" not in chart:
        raise ValueError("chart envelope missing required d1/d9 keys")
    birth_jd_val = chart.get("birth_jd") or chart.get("jd")
    if not isinstance(birth_jd_val, (int, float)):
        raise ValueError("chart envelope missing 'birth_jd' (or 'jd') float")
    birth_jd = float(birth_jd_val)

    moon_lon = _planet_lon(chart["d1"], "Moon")
    if moon_lon is None:
        raise ValueError("chart['d1']['Moon'] missing longitude")

    current = chart.get("current_mahadasha") or {}
    current_lord = current.get("mahadasha_lord")

    periods = _build_lifetime_timeline(moon_lon, birth_jd)

    timeline: list[MDJudgment] = []
    for period in periods:
        lord = period["lord"]
        start_jd = period["start_jd"]
        end_jd = period["end_jd"]
        is_current = lord == current_lord and start_jd <= birth_jd < end_jd
        is_past = end_jd <= birth_jd
        is_future = start_jd > birth_jd
        judgment = _judge_mahadasha(
            chart=chart,
            asc_sign=asc_sign,
            moon_sign=moon_sign,
            md_lord=lord,
            start_jd=start_jd,
            end_jd=end_jd,
            birth_jd=birth_jd,
            is_current=is_current,
            is_past=is_past,
            is_future=is_future,
        )
        timeline.append(judgment)

    # Exactly one judgment must be is_current=True.
    currents = [j for j in timeline if j.is_current]
    if len(currents) != 1:
        raise ValueError(
            f"Expected exactly one is_current=True judgment, got {len(currents)}"
        )
    current_md_judgment = currents[0]

    return VimshottariMDResult(
        timeline=timeline,
        current_md_judgment=current_md_judgment,
    )


__all__ = ["VimshottariMDResult", "run_sequence"]
