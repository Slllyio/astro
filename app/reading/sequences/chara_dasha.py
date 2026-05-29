"""Sequence — Chara Dasha (Jaimini sign-based timing).

Doctrine lock: D-17 (Sanjay-Rath / Raghavendra variant per
``docs/doctrine-decisions.md``)

Chara Dasha is Jaimini's **sign-based** dasha system. Unlike Vimshottari
(which is nakshatra-Moon-driven and planet-keyed), Chara Dasha is keyed
on signs (Rashi) and is determined entirely by the natal Lagna. It
complements the V1 Vimshottari engine by giving a sign-frame timing
overlay independent of the Moon's nakshatra.

D-17 rule set (locked)
======================

**Starting MD sign** (per Sanjay-Rath variant):

  - Movable lagna (1/4/7/10): MD cycle starts with the lagna sign itself
  - Fixed lagna   (2/5/8/11): MD cycle starts with the 5th from lagna
  - Dual lagna    (3/6/9/12): MD cycle starts with the 9th from lagna

After the starting sign, the cycle proceeds zodiacally through the
remaining 11 signs.

**Years per sign** (per D-17 formula): ``12 - (number of signs from the
sign being computed to its "co-lord" sign)``, where the co-lord offset
depends on the sign's category:

  - Movable sign → co-lord at the 9th sign from it (1-indexed inclusive)
  - Fixed sign   → co-lord at the 5th sign from it
  - Dual sign    → co-lord = itself (distance = 1)

So:

  - Movable signs: years = 12 - 9 = 3
  - Fixed signs:   years = 12 - 5 = 7
  - Dual signs:    years = 12 - 1 = 11

Total cycle length = 4*3 + 4*7 + 4*11 = **84 years**. This is the
literal Sanjay-Rath / brief-specified formula. The PVR Narasimha Rao
variant differs in both starting-sign rule and years-per-sign rule; see
the D-17 alternatives entry. Disagreement between schools is real and
surfaceable via ``dispute_surfacing.py`` if downstream consumers need to
see alternatives.

Architectural discipline
========================

This module ORCHESTRATES — it does NOT recompute chart math. The judgment
per MD delegates to existing Tier-0/1/2 computations:

  - Karaka identification     → ``computations.karakas.compute_karakas``
  - Jaimini sign drishti      → ``computations.jaimini_drishti.compute_jaimini_drishti``
  - Argala on the MD sign     → ``computations.argala.compute_argala``
  - Sign-lord lookup          → ``app.core.dignity.SIGN_RULERS``

Schema discipline: this module emits its OWN result/period/judgment
dataclasses (``CharaDashaResult``, ``CharaDashaMDPeriod``,
``CharaDashaADPeriod``, ``CharaDashaJudgment``). It does NOT modify
``app.reading.schema`` (per Phase-4-style discipline — Chara Dasha is a
parallel timing system not yet wired into the V1 schema envelope).

The seven named checks per MD judgment are:

  1. ``sign_character``           — movable / fixed / dual
  2. ``sign_lord_placement``      — where the MD sign's rashi-lord sits
  3. ``karaka_in_sign``           — which Jaimini karaka is in the MD sign
  4. ``occupants_of_sign``        — planets sitting in the MD sign
  5. ``argala_on_sign``           — argala detection on the MD sign's bhava
  6. ``drishti_to_sign``          — Jaimini rashi-drishti TO the MD sign
  7. ``atmakaraka_relationship``  — relationship of MD sign to AK sign

Public API
==========

    run_sequence(chart, asc_sign, moon_sign) -> CharaDashaResult

The ``moon_sign`` argument is accepted for API symmetry with
``vimshottari_md.run_sequence`` but is not used by Chara Dasha
calculations (Chara is sign-frame, not Moon-keyed).
"""
from __future__ import annotations

import logging
from typing import Any, Final, Mapping

import swisseph as swe
from pydantic import BaseModel, ConfigDict, Field

from app.core.dignity import SIGN_RULERS
from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
from app.reading.computations.argala import compute_argala
from app.reading.computations.jaimini_drishti import (
    _sign_category,
    _signs_aspected_by,
    compute_jaimini_drishti,
)
from app.reading.computations.karakas import compute_karakas
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_SEQUENCE_NAME: Final[str] = "chara_dasha"


# Each Chara Dasha check is a structural delegation, not a 3-pillar
# judgment — domain layers re-score downstream.
_SEQUENCE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=Jaimini Sutras Adhyaya 2 + Sanjay-Rath Crux Ch.16 — D-17"
)


# The 7 named check keys per MD judgment (locked).
CHARA_DASHA_MD_CHECK_KEYS: Final[tuple[str, ...]] = (
    "sign_character",
    "sign_lord_placement",
    "karaka_in_sign",
    "occupants_of_sign",
    "argala_on_sign",
    "drishti_to_sign",
    "atmakaraka_relationship",
)


# Sign names (1-indexed; 0 unused).
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# Karaka labels in canonical 8-karaka order (matches
# ``computations.karakas`` keys). Used for inverse lookup
# (planet -> karaka role) in the karaka_in_sign check.
_KARAKA_KEYS: Final[tuple[str, ...]] = (
    "atmakaraka", "amatyakaraka", "bhratrikaraka", "matrikaraka",
    "pitrikaraka", "gnatikaraka", "darakaraka", "strikaraka",
)


# All non-nodal + nodal planet names for sign-occupant scans. We keep
# the same scan list the Vimshottari MD sequence uses for symmetry, but
# Chara Dasha is sign-keyed, so Ketu is included here (unlike karaka
# ranking where Ketu is excluded).
_ALL_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury",
    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


# ---------------------------------------------------------------------------
# Local result models (schema.py is intentionally NOT modified for V1.5)
# ---------------------------------------------------------------------------


class CharaDashaMDPeriod(BaseModel):
    """One Chara Dasha mahadasha period (sign-keyed).

    ``md_sign`` is the 1-indexed sign ruling this period. ``start_jd`` /
    ``end_jd`` carry Julian-Day precision; ``start_date`` / ``end_date``
    are ISO-8601 strings for human consumers.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    md_sign: int = Field(ge=1, le=12)
    md_sign_name: str
    sign_category: str  # "movable" / "fixed" / "dual"
    total_years: float
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    age_at_start: float
    age_at_end: float
    is_current: bool
    is_past: bool
    is_future: bool


class CharaDashaADPeriod(BaseModel):
    """One Chara Dasha antardasha sub-period (sign-keyed)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ad_sign: int = Field(ge=1, le=12)
    ad_sign_name: str
    md_sign: int = Field(ge=1, le=12)
    total_years: float
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    is_current: bool


class CharaDashaJudgment(BaseModel):
    """Per-MD judgment from the 7 named checks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    md_sign: int = Field(ge=1, le=12)
    md_sign_name: str
    checks: dict[str, Finding]
    overall_verdict: Finding


class CharaDashaResult(BaseModel):
    """Sequence result — Chara Dasha lifetime timeline + current-MD judgment.

    ``timeline`` contains the 12 MD periods covering one full Chara
    cycle (84 years per D-17). ``current_md_judgment`` is the 7-check
    judgment for whichever MD contains the chart's birth-JD or, if the
    cycle ends before birth, the last MD in the cycle.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    timeline: list[CharaDashaMDPeriod] = Field(default_factory=list)
    current_md_judgment: CharaDashaJudgment
    current_ads: list[CharaDashaADPeriod] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(
            f"{name} must be a 1-indexed sign in 1..12, got {value!r}"
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


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    """Whole-sign house number (1..12) of a planet from a given Lagna."""
    return ((planet_sign - asc_sign) % 12) + 1


def _sign_forward(from_sign: int, offset: int) -> int:
    """Return the sign ``offset`` positions forward from ``from_sign``.

    ``offset=1`` returns the same sign (inclusive 1-indexed count).
    ``offset=9`` returns the 9th sign from ``from_sign``.
    """
    return ((from_sign - 1 + (offset - 1)) % 12) + 1


def _format_iso(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


# ---------------------------------------------------------------------------
# D-17 — starting MD sign + years-per-sign
# ---------------------------------------------------------------------------


def _starting_md_sign(asc_sign: int) -> int:
    """D-17 starting-sign rule.

    Movable lagna -> lagna sign itself.
    Fixed lagna   -> 5th from lagna.
    Dual lagna    -> 9th from lagna.
    """
    category = _sign_category(asc_sign)
    if category == "movable":
        return asc_sign
    if category == "fixed":
        return _sign_forward(asc_sign, 5)
    # dual
    return _sign_forward(asc_sign, 9)


def _years_for_sign(sign: int) -> int:
    """D-17 years-per-sign rule.

    Years = 12 - (distance to co-lord), where co-lord offset is:
      - Movable: 9 (years = 3)
      - Fixed:   5 (years = 7)
      - Dual:    1 (years = 11)
    """
    category = _sign_category(sign)
    if category == "movable":
        return 12 - 9  # 3
    if category == "fixed":
        return 12 - 5  # 7
    # dual
    return 12 - 1  # 11


# ---------------------------------------------------------------------------
# Timeline construction
# ---------------------------------------------------------------------------


def _compute_md_timeline(
    asc_sign: int, birth_jd: float,
) -> list[dict[str, Any]]:
    """Build the 12-MD lifetime timeline from birth.

    Returns list of dicts with keys:
        md_sign, total_years, start_jd, end_jd

    The cycle starts at ``birth_jd`` itself with the D-17 starting sign,
    then proceeds zodiacally for the remaining 11 signs. (Unlike
    Vimshottari, which is "balance of MD at birth" Moon-driven, Chara
    Dasha by D-17 spec begins at birth with a full first MD.)
    """
    start_sign = _starting_md_sign(asc_sign)
    periods: list[dict[str, Any]] = []
    cursor_jd = float(birth_jd)
    for offset in range(12):
        sign = _sign_forward(start_sign, offset + 1)
        years = _years_for_sign(sign)
        end_jd = cursor_jd + years * DAYS_PER_VEDIC_YEAR
        periods.append(
            {
                "md_sign": sign,
                "total_years": float(years),
                "start_jd": cursor_jd,
                "end_jd": end_jd,
            }
        )
        cursor_jd = end_jd
    return periods


def _compute_ads_for_md(
    md_sign: int, md_start_jd: float, md_total_years: float,
) -> list[CharaDashaADPeriod]:
    """Sub-divide one MD into 12 ADs, each proportional to its own
    sign's years-per-sign weight.

    The MD's 12 ADs are the 12 signs starting with the MD sign itself,
    in zodiacal order. Each AD length = MD total years × (AD sign's
    weight / sum of all 12 weights).
    """
    weights = [float(_years_for_sign(_sign_forward(md_sign, k + 1)))
               for k in range(12)]
    total_weight = sum(weights)
    cursor_jd = float(md_start_jd)
    md_total_days = md_total_years * DAYS_PER_VEDIC_YEAR
    ads: list[CharaDashaADPeriod] = []
    for k in range(12):
        ad_sign = _sign_forward(md_sign, k + 1)
        ad_years = md_total_years * (weights[k] / total_weight)
        ad_days = md_total_days * (weights[k] / total_weight)
        ad_end_jd = cursor_jd + ad_days
        ads.append(
            CharaDashaADPeriod(
                ad_sign=ad_sign,
                ad_sign_name=_SIGN_NAMES[ad_sign],
                md_sign=md_sign,
                total_years=float(ad_years),
                start_jd=float(cursor_jd),
                end_jd=float(ad_end_jd),
                start_date=_format_iso(cursor_jd),
                end_date=_format_iso(ad_end_jd),
                is_current=False,  # set by caller
            )
        )
        cursor_jd = ad_end_jd
    return ads


# ---------------------------------------------------------------------------
# Per-MD named checks
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


def _check_sign_character(md_sign: int) -> Finding:
    """Movable / fixed / dual character of the MD sign."""
    category = _sign_category(md_sign)
    # Movable: action, change, initiative.
    # Fixed: stability, slow grind, consolidation.
    # Dual: flux, learning, adaptive intelligence.
    direction = "neutral"
    flavour = {
        "movable": "kinetic / initiating",
        "fixed": "stabilising / consolidating",
        "dual": "adaptive / mutable",
    }[category]
    verdict = (
        f"MD sign {_SIGN_NAMES[md_sign]} is {category} ({flavour})"
    )[:140]
    return Finding(
        id="seq_chara.step_01.sign_character",
        rule="chara.sign_character",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_sign={md_sign}",
            f"md_sign_name={_SIGN_NAMES[md_sign]}",
            f"category={category}",
            f"years_per_sign={_years_for_sign(md_sign)}",
            "delegate=computations.jaimini_drishti._sign_category",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_sign_lord_placement(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_sign: int,
) -> Finding:
    """Bhava (from natal Lagna) the MD sign's rashi-lord occupies."""
    lord = SIGN_RULERS.get(md_sign)
    if lord is None:
        return _neutral_finding(
            step_id="seq_chara.step_02.sign_lord_placement",
            rule="chara.sign_lord_placement",
            verdict=f"MD sign {md_sign} rashi-lord unknown",
            evidence=[f"md_sign={md_sign}", _DOCTRINE_SENTINEL],
        )
    lord_sign = _planet_sign(d1_chart, lord)
    if lord_sign is None:
        return _neutral_finding(
            step_id="seq_chara.step_02.sign_lord_placement",
            rule="chara.sign_lord_placement",
            verdict=f"MD sign lord {lord} not in chart",
            evidence=[
                f"md_sign={md_sign}",
                f"lord={lord}",
                _DOCTRINE_SENTINEL,
            ],
        )
    bhava = _whole_sign_house(lord_sign, asc_sign)
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
        f"MD sign {_SIGN_NAMES[md_sign]} lord {lord} in bhava {bhava} "
        f"({flavour})"
    )[:140]
    return Finding(
        id="seq_chara.step_02.sign_lord_placement",
        rule="chara.sign_lord_placement",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_sign={md_sign}",
            f"sign_lord={lord}",
            f"lord_sign={lord_sign}",
            f"bhava_from_lagna={bhava}",
            f"is_kendra={kendra}",
            f"is_trikona={trikona}",
            f"is_dusthana={dusthana}",
            "delegate=app.core.dignity.SIGN_RULERS",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_karaka_in_sign(
    d1_chart: Mapping[str, Mapping[str, object]], md_sign: int,
) -> Finding:
    """Which Jaimini karaka(s) reside in the MD sign.

    Delegates to ``computations.karakas.compute_karakas`` and inverts
    the karaka_key -> planet mapping by inspecting each finding's
    evidence for the ``planet=`` line.
    """
    try:
        karakas = compute_karakas(dict(d1_chart), karaka_mode=8)
    except Exception as exc:  # noqa: BLE001
        logger.warning("compute_karakas failed for chara MD %s: %s", md_sign, exc)
        return _neutral_finding(
            step_id="seq_chara.step_03.karaka_in_sign",
            rule="chara.karaka_in_sign",
            verdict=f"karaka computation failed for MD sign {md_sign}",
            evidence=[
                f"md_sign={md_sign}",
                f"error={type(exc).__name__}",
                _DOCTRINE_SENTINEL,
            ],
        )
    # Invert: collect (karaka_key, planet) pairs.
    karaka_to_planet: dict[str, str] = {}
    for k_key in _KARAKA_KEYS:
        finding = karakas.get(k_key)
        if finding is None:
            continue
        for line in finding.evidence:
            if line.startswith("planet="):
                karaka_to_planet[k_key] = line.split("=", 1)[1]
                break
    karakas_in_sign: list[str] = []
    for k_key, planet in karaka_to_planet.items():
        p_sign = _planet_sign(d1_chart, planet)
        if p_sign == md_sign:
            karakas_in_sign.append(f"{k_key}={planet}")
    direction = "positive" if karakas_in_sign else "neutral"
    verdict = (
        f"MD sign {_SIGN_NAMES[md_sign]} hosts karakas: "
        f"{karakas_in_sign or 'none'}"
    )[:140]
    return Finding(
        id="seq_chara.step_03.karaka_in_sign",
        rule="chara.karaka_in_sign",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_sign={md_sign}",
            f"karakas_present={karakas_in_sign}",
            "delegate=computations.karakas.compute_karakas (D-1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_occupants_of_sign(
    d1_chart: Mapping[str, Mapping[str, object]], md_sign: int,
) -> Finding:
    """Planets sitting in the MD sign (sign-occupancy)."""
    occupants: list[str] = []
    for p in _ALL_PLANETS:
        if _planet_sign(d1_chart, p) == md_sign:
            occupants.append(p)
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    bf = [p for p in occupants if p in benefics]
    mal = [p for p in occupants if p in malefics]
    if bf and not mal:
        direction = "positive"
    elif mal and not bf:
        direction = "negative"
    elif bf and mal:
        direction = "mixed"
    else:
        direction = "neutral"
    verdict = (
        f"MD sign {_SIGN_NAMES[md_sign]} occupants: {occupants or 'empty'}"
    )[:140]
    return Finding(
        id="seq_chara.step_04.occupants_of_sign",
        rule="chara.occupants_of_sign",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_sign={md_sign}",
            f"occupants={occupants}",
            f"benefic_occupants={bf}",
            f"malefic_occupants={mal}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_argala_on_sign(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_sign: int,
) -> Finding:
    """Argala (intervention) on the MD sign's bhava from natal Lagna.

    Delegates to ``computations.argala.compute_argala``. We compute the
    MD sign's bhava number from natal Lagna and look up the Argala
    finding for that bhava.
    """
    bhava = _whole_sign_house(md_sign, asc_sign)
    try:
        argala = compute_argala(dict(d1_chart), asc_sign)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "compute_argala failed for chara MD %s: %s", md_sign, exc,
        )
        return _neutral_finding(
            step_id="seq_chara.step_05.argala_on_sign",
            rule="chara.argala_on_sign",
            verdict=f"argala computation failed for MD sign {md_sign}",
            evidence=[
                f"md_sign={md_sign}",
                f"bhava={bhava}",
                f"error={type(exc).__name__}",
                _DOCTRINE_SENTINEL,
            ],
        )
    bhava_finding = argala.get(bhava)
    if bhava_finding is None:
        return _neutral_finding(
            step_id="seq_chara.step_05.argala_on_sign",
            rule="chara.argala_on_sign",
            verdict=f"no argala finding for bhava {bhava}",
            evidence=[
                f"md_sign={md_sign}",
                f"bhava={bhava}",
                _DOCTRINE_SENTINEL,
            ],
        )
    direction = bhava_finding.direction
    verdict = (
        f"Argala on MD sign {_SIGN_NAMES[md_sign]} (bhava {bhava}): "
        f"{direction}"
    )[:140]
    return Finding(
        id="seq_chara.step_05.argala_on_sign",
        rule="chara.argala_on_sign",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_sign={md_sign}",
            f"bhava_from_lagna={bhava}",
            f"argala_direction={direction}",
            f"argala_verdict={bhava_finding.verdict}",
            "delegate=computations.argala.compute_argala",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_drishti_to_sign(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_sign: int,
) -> Finding:
    """Jaimini rashi-drishti TO the MD sign.

    A sign X aspects MD sign iff md_sign is in ``_signs_aspected_by(X)``.
    We collect the set of signs aspecting MD sign and tag their
    occupants for the verdict.
    """
    # Pre-compute the per-sign aspect map (delegates to the foundation
    # module's pure helper; no chart input needed there).
    try:
        # We call the public API for completeness (validates asc_sign);
        # the per-sign aspect set is computed via the pure helper.
        compute_jaimini_drishti(dict(d1_chart), asc_sign)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "compute_jaimini_drishti pre-check failed for chara MD %s: %s",
            md_sign, exc,
        )
    aspecting_signs: list[int] = []
    for src in range(1, 13):
        if md_sign in _signs_aspected_by(src):
            aspecting_signs.append(src)
    # Collect planets in those aspecting signs.
    aspecting_planets: list[str] = []
    for p in _ALL_PLANETS:
        ps = _planet_sign(d1_chart, p)
        if ps in aspecting_signs:
            aspecting_planets.append(p)
    direction = "positive" if aspecting_planets else "neutral"
    verdict = (
        f"MD sign {_SIGN_NAMES[md_sign]} receives Jaimini drishti from "
        f"signs {aspecting_signs}"
    )[:140]
    return Finding(
        id="seq_chara.step_06.drishti_to_sign",
        rule="chara.drishti_to_sign",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_sign={md_sign}",
            f"aspecting_signs={aspecting_signs}",
            f"aspecting_planets={aspecting_planets}",
            "delegate=computations.jaimini_drishti (Tier-1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_atmakaraka_relationship(
    d1_chart: Mapping[str, Mapping[str, object]], md_sign: int,
) -> Finding:
    """Relationship between the MD sign and the Atmakaraka's sign.

    Strong / classical relationships:
      - Same sign as AK -> identity (powerful soul-period)
      - Trine (5/9 from AK) -> dharmic alignment
      - Kendra (4/7/10 from AK) -> action alignment
      - 6/8/12 from AK -> friction
    """
    try:
        karakas = compute_karakas(dict(d1_chart), karaka_mode=8)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "compute_karakas failed for chara AK check, MD %s: %s",
            md_sign, exc,
        )
        return _neutral_finding(
            step_id="seq_chara.step_07.atmakaraka_relationship",
            rule="chara.atmakaraka_relationship",
            verdict=f"AK computation failed for MD sign {md_sign}",
            evidence=[
                f"md_sign={md_sign}",
                f"error={type(exc).__name__}",
                _DOCTRINE_SENTINEL,
            ],
        )
    ak_finding = karakas.get("atmakaraka")
    if ak_finding is None:
        return _neutral_finding(
            step_id="seq_chara.step_07.atmakaraka_relationship",
            rule="chara.atmakaraka_relationship",
            verdict=f"AK not identified for MD sign {md_sign}",
            evidence=[
                f"md_sign={md_sign}",
                _DOCTRINE_SENTINEL,
            ],
        )
    ak_planet: str | None = None
    for line in ak_finding.evidence:
        if line.startswith("planet="):
            ak_planet = line.split("=", 1)[1]
            break
    ak_sign = _planet_sign(d1_chart, ak_planet) if ak_planet else None
    if ak_sign is None:
        return _neutral_finding(
            step_id="seq_chara.step_07.atmakaraka_relationship",
            rule="chara.atmakaraka_relationship",
            verdict=f"AK sign unknown for MD sign {md_sign}",
            evidence=[
                f"md_sign={md_sign}",
                f"ak_planet={ak_planet}",
                _DOCTRINE_SENTINEL,
            ],
        )
    # Distance from AK to MD (whole-sign house count, 1-indexed inclusive).
    distance_from_ak = _whole_sign_house(md_sign, ak_sign)
    if distance_from_ak == 1:
        relationship = "identity_with_ak"
        direction = "positive"
    elif distance_from_ak in (5, 9):
        relationship = "trine_to_ak"
        direction = "positive"
    elif distance_from_ak in (4, 7, 10):
        relationship = "kendra_to_ak"
        direction = "positive"
    elif distance_from_ak in (6, 8, 12):
        relationship = "dusthana_to_ak"
        direction = "negative"
    else:
        relationship = "neutral_to_ak"
        direction = "neutral"
    verdict = (
        f"MD sign {_SIGN_NAMES[md_sign]} is {relationship} "
        f"(AK={ak_planet}, AK sign={_SIGN_NAMES[ak_sign]})"
    )[:140]
    return Finding(
        id="seq_chara.step_07.atmakaraka_relationship",
        rule="chara.atmakaraka_relationship",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_sign={md_sign}",
            f"ak_planet={ak_planet}",
            f"ak_sign={ak_sign}",
            f"distance_from_ak={distance_from_ak}",
            f"relationship={relationship}",
            "delegate=computations.karakas (D-1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------


def _synthesize_overall(
    checks: Mapping[str, Finding], md_sign: int,
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
        tone = "MD sign neutrally placed"
    else:
        direction = "mixed"
        tone = "balanced positives and negatives"
    verdict = (
        f"Chara MD={_SIGN_NAMES[md_sign]} verdict: {tone}; "
        f"+{pos}/-{neg}/~{mixed}"
    )[:140]
    return Finding(
        id="seq_chara.overall",
        rule="chara.overall",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_sign={md_sign}",
            f"positive_checks={pos}",
            f"negative_checks={neg}",
            f"mixed_checks={mixed}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Per-MD orchestrator
# ---------------------------------------------------------------------------


def _judge_md(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    md_sign: int,
) -> CharaDashaJudgment:
    """Build a :class:`CharaDashaJudgment` by running all 7 named checks."""
    checks: dict[str, Finding] = {
        "sign_character": _check_sign_character(md_sign),
        "sign_lord_placement": _check_sign_lord_placement(
            d1_chart, asc_sign, md_sign,
        ),
        "karaka_in_sign": _check_karaka_in_sign(d1_chart, md_sign),
        "occupants_of_sign": _check_occupants_of_sign(d1_chart, md_sign),
        "argala_on_sign": _check_argala_on_sign(
            d1_chart, asc_sign, md_sign,
        ),
        "drishti_to_sign": _check_drishti_to_sign(
            d1_chart, asc_sign, md_sign,
        ),
        "atmakaraka_relationship": _check_atmakaraka_relationship(
            d1_chart, md_sign,
        ),
    }
    # Schema discipline: assert all expected keys are present (no extras).
    expected = set(CHARA_DASHA_MD_CHECK_KEYS)
    got = set(checks.keys())
    if got != expected:
        raise ValueError(
            f"CharaDashaJudgment.checks key mismatch: "
            f"missing={sorted(expected - got)} extra={sorted(got - expected)}"
        )
    overall = _synthesize_overall(checks, md_sign)
    return CharaDashaJudgment(
        md_sign=md_sign,
        md_sign_name=_SIGN_NAMES[md_sign],
        checks=checks,
        overall_verdict=overall,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_sequence(
    chart: dict, asc_sign: int, moon_sign: int,
) -> CharaDashaResult:
    """Run the Chara Dasha (Jaimini sign-based) sequence per D-17.

    Args:
        chart: Full natal chart dict from
            ``app.core.ephemeris_engine.calculate_all_charts``. Must
            include ``d1`` and ``birth_jd`` (or ``jd``).
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: Accepted for API symmetry with
            ``vimshottari_md.run_sequence`` but unused — Chara Dasha is
            sign-frame, not Moon-keyed.

    Returns:
        :class:`CharaDashaResult` with the 12-MD lifetime ``timeline``,
        the 7-check ``current_md_judgment``, and the 12 AD sub-periods
        of the current MD.

    Raises:
        ValueError: if asc_sign/moon_sign are out of range, or chart
            envelope is missing required keys.
    """
    _validate_sign(asc_sign, "asc_sign")
    _validate_sign(moon_sign, "moon_sign")  # validated for API symmetry
    _ = moon_sign  # explicitly unused — D-17 is sign-frame

    if "d1" not in chart:
        raise ValueError("chart envelope missing required 'd1' key")
    birth_jd_val = chart.get("birth_jd") or chart.get("jd")
    if not isinstance(birth_jd_val, (int, float)):
        raise ValueError("chart envelope missing 'birth_jd' (or 'jd') float")
    birth_jd = float(birth_jd_val)

    d1 = chart["d1"]

    periods = _compute_md_timeline(asc_sign, birth_jd)

    timeline: list[CharaDashaMDPeriod] = []
    current_idx: int | None = None
    for idx, period in enumerate(periods):
        md_sign = period["md_sign"]
        start_jd = period["start_jd"]
        end_jd = period["end_jd"]
        # The cycle starts at birth_jd, so the FIRST MD is always
        # is_current=True at birth (start_jd == birth_jd). Across the
        # lifetime, exactly one MD contains the birth moment — that one
        # is is_current.
        is_current = start_jd <= birth_jd < end_jd
        is_past = end_jd <= birth_jd
        is_future = start_jd > birth_jd
        if is_current:
            current_idx = idx
        age_at_start = (start_jd - birth_jd) / DAYS_PER_VEDIC_YEAR
        age_at_end = (end_jd - birth_jd) / DAYS_PER_VEDIC_YEAR
        timeline.append(
            CharaDashaMDPeriod(
                md_sign=md_sign,
                md_sign_name=_SIGN_NAMES[md_sign],
                sign_category=_sign_category(md_sign),
                total_years=float(period["total_years"]),
                start_jd=float(start_jd),
                end_jd=float(end_jd),
                start_date=_format_iso(start_jd),
                end_date=_format_iso(end_jd),
                age_at_start=float(age_at_start),
                age_at_end=float(age_at_end),
                is_current=is_current,
                is_past=is_past,
                is_future=is_future,
            )
        )

    if current_idx is None:
        # Cycle ends before birth (shouldn't happen since cycle starts at
        # birth); defensively fall through to the first MD.
        logger.warning(
            "Chara Dasha cycle has no MD containing birth_jd — defaulting "
            "to first MD as current"
        )
        current_idx = 0
        # Re-emit the first period with is_current=True for schema
        # consistency.
        first = timeline[0]
        timeline[0] = CharaDashaMDPeriod(
            md_sign=first.md_sign,
            md_sign_name=first.md_sign_name,
            sign_category=first.sign_category,
            total_years=first.total_years,
            start_jd=first.start_jd,
            end_jd=first.end_jd,
            start_date=first.start_date,
            end_date=first.end_date,
            age_at_start=first.age_at_start,
            age_at_end=first.age_at_end,
            is_current=True,
            is_past=False,
            is_future=False,
        )

    current_period = timeline[current_idx]
    current_md_judgment = _judge_md(d1, asc_sign, current_period.md_sign)

    # Compute the 12 ADs for the current MD; flag the one containing
    # birth_jd as is_current.
    raw_ads = _compute_ads_for_md(
        current_period.md_sign,
        current_period.start_jd,
        current_period.total_years,
    )
    current_ads: list[CharaDashaADPeriod] = []
    for ad in raw_ads:
        is_current_ad = ad.start_jd <= birth_jd < ad.end_jd
        current_ads.append(
            CharaDashaADPeriod(
                ad_sign=ad.ad_sign,
                ad_sign_name=ad.ad_sign_name,
                md_sign=ad.md_sign,
                total_years=ad.total_years,
                start_jd=ad.start_jd,
                end_jd=ad.end_jd,
                start_date=ad.start_date,
                end_date=ad.end_date,
                is_current=is_current_ad,
            )
        )

    return CharaDashaResult(
        timeline=timeline,
        current_md_judgment=current_md_judgment,
        current_ads=current_ads,
    )


__all__ = [
    "CHARA_DASHA_MD_CHECK_KEYS",
    "CharaDashaADPeriod",
    "CharaDashaJudgment",
    "CharaDashaMDPeriod",
    "CharaDashaResult",
    "run_sequence",
]
