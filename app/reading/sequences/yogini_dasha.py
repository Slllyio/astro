"""Sequence — Yogini Dasha 36-year specialty dasha (D-18 locked).

Doctrine source
===============

Tantric tradition + Shastras (Maha Tantra commentary); Sanjay Rath
"Crux of Vedic Astrology" Ch.17. The Yogini Dasha is a 36-year
short-cycle dasha that practitioners use to **cross-validate
Vimshottari predictions** — especially yearly themes that the 120-year
Vimshottari sweep tends to under-resolve.

Doctrine lock (D-18, ``docs/doctrine-decisions.md``):

- 8 Yoginis, each ruling a deity-period with a fixed length:

  ================  ==============  =================  ========
  Yogini (index)    Length (years)  Ruling planet      Nature
  ================  ==============  =================  ========
  Mangala (0)       1               Sun                neutral
  Pingala (1)       2               Moon               benefic
  Dhanya (2)        3               Jupiter            benefic
  Bhramari (3)      4               Mars               neutral
  Bhadrika (4)      5               Mercury            benefic
  Ulka (5)          6               Saturn             malefic
  Siddha (6)        7               Venus              benefic
  Sankata (7)       8               Rahu               malefic
  ================  ==============  =================  ========

- Total cycle = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 = **36 years**, repeats
  ~3.3 times across a 120-year lifespan.
- Start yogini is determined by the Moon's natal nakshatra via the
  cyclic 8-fold mapping ``(nakshatra_index_1based - 1) % 8``.

Architectural discipline
========================

This module ORCHESTRATES — it does NOT recompute primitives. Each
per-MD check delegates to an existing Tier-0/1/2 module:

  * ``ruling_yogini_nature``     -> in-module deity-nature table (locked
                                    per D-18; no recompute).
  * ``ruling_planet_placement``  -> chart["d1"] sign + whole-sign house
                                    from Lagna (same _whole_sign_house
                                    primitive used by vimshottari_md).
  * ``ruling_planet_dignity``    -> ``app.core.dignity`` exaltation /
                                    debilitation + moolatrikona checks.
  * ``ruling_planet_in_kendra_or_kona``
                                 -> whole-sign bhava check (1/4/5/7/9/10).
  * ``cross_check_with_vimshottari``
                                 -> chart["current_mahadasha"] is the
                                    cross-reference; the check reports
                                    whether the Yogini ruling planet
                                    matches / supports / opposes the
                                    Vimshottari MD lord.

Per the Phase-4 architectural discipline: no math here is re-derived
from ephemeris. Nakshatra resolution delegates to
``app.core.nakshatra.nakshatra_for_longitude``; JD/calendar conversion
uses ``swisseph.revjul`` (same convention as ``vimshottari_md``).

Public API
==========

    run_sequence(chart, asc_sign, moon_nakshatra) -> YoginiDashaResult

Where ``moon_nakshatra`` is the **1-indexed** nakshatra number (1..27)
of the natal Moon. The function exposes the named-1-indexed form for
parity with the Maha Tantra reference table; callers can pass
``nakshatra_for_longitude(moon_lon)["index"] + 1`` to convert from the
0-indexed core primitive.

Returns a :class:`YoginiDashaResult` with:

  - ``timeline``               — chronological list of
                                 :class:`YoginiMDPeriod` covering the
                                 first 36-year cycle from birth plus
                                 ~2 further cycles (sufficient for the
                                 standard 100-yr forecast horizon).
  - ``current_md_judgment``    — the period where ``is_current=True``.

Schema note
===========

The brief forbids modifying ``schema.py`` for this sequence, so the
result model + judgment model are defined locally as Pydantic
``BaseModel`` subclasses. They mirror the established Finding /
ConfidenceScore conventions and pass through schema-validated
``Finding`` envelopes for each named check.
"""
from __future__ import annotations

import logging
from typing import Any, Final, Mapping

import swisseph as swe
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.dignity import DEBILITATION, EXALTATION, MOOLATRIKONA_RANGES, SIGN_RULERS
from app.core.nakshatra import NAKSHATRAS, nakshatra_for_longitude
from app.reading.computations.functional_nature import (
    compute_functional_nature,
)
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_SEQUENCE_NAME: Final[str] = "yogini_dasha"

# Sequence-level confidence envelope — each check is a structural
# delegation, not a 3-pillar judgment. Same envelope as vimshottari_md
# (downstream domain layers re-score with full evidence weighting).
_SEQUENCE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=Maha Tantra + Sanjay Rath 'Crux of Vedic Astrology' Ch.17 — D-18"
)


# ---------------------------------------------------------------------------
# Yogini Dasha canonical constants (D-18)
# ---------------------------------------------------------------------------

YOGINI_NAMES: Final[tuple[str, ...]] = (
    "Mangala", "Pingala", "Dhanya", "Bhramari",
    "Bhadrika", "Ulka", "Siddha", "Sankata",
)

YOGINI_LENGTHS: Final[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7, 8)
"""Yogini period lengths in years. Sum = 36."""

assert sum(YOGINI_LENGTHS) == 36, "Yogini cycle must sum to 36 years"

YOGINI_RULING_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Jupiter", "Mars",
    "Mercury", "Saturn", "Venus", "Rahu",
)

# Deity nature per Maha Tantra commentary.
# Pingala (Moon), Dhanya (Jupiter), Bhadrika (Mercury), Siddha (Venus) are
# the four benefic yoginis; Ulka (Saturn) and Sankata (Rahu) are the two
# malefics; Mangala (Sun) and Bhramari (Mars) are mixed/neutral with a
# protective-but-fiery tone.
YOGINI_NATURE: Final[dict[str, str]] = {
    "Mangala":  "neutral",   # Sun-ruled — auspicious in name, fiery
    "Pingala":  "benefic",   # Moon-ruled — nourishing
    "Dhanya":   "benefic",   # Jupiter-ruled — wealth/prosperity
    "Bhramari": "neutral",   # Mars-ruled — wandering / energetic
    "Bhadrika": "benefic",   # Mercury-ruled — auspicious / good news
    "Ulka":     "malefic",   # Saturn-ruled — calamitous (meteor)
    "Siddha":   "benefic",   # Venus-ruled — accomplishment
    "Sankata":  "malefic",   # Rahu-ruled — crisis / obstacles
}

# Nakshatra index (1-indexed, 1..27) -> starting yogini index (0..7).
# Cyclic mapping per D-18: (nak_index_1based - 1) % 8.
NAKSHATRA_TO_YOGINI: Final[dict[int, int]] = {
    nak: (nak - 1) % 8 for nak in range(1, 28)
}

# Verify the spec-table assertion: nakshatra 27 (Revati) → yogini 2 (Dhanya).
assert NAKSHATRA_TO_YOGINI[27] == 2
assert YOGINI_NAMES[NAKSHATRA_TO_YOGINI[27]] == "Dhanya"
# nakshatra 1 (Ashwini) → yogini 0 (Mangala).
assert NAKSHATRA_TO_YOGINI[1] == 0
assert YOGINI_NAMES[NAKSHATRA_TO_YOGINI[1]] == "Mangala"


YOGINI_MD_CHECK_KEYS: Final[tuple[str, ...]] = (
    "ruling_yogini_nature",
    "ruling_planet_placement",
    "ruling_planet_dignity",
    "ruling_planet_in_kendra_or_kona",
    "cross_check_with_vimshottari",
)


# Gregorian-mean Vedic year per CLAUDE.md locked decision (not 365.25).
_DAYS_PER_VEDIC_YEAR: Final[float] = 365.2425


# ---------------------------------------------------------------------------
# Local schema (schema.py is read-only per Phase-4 brief)
# ---------------------------------------------------------------------------


class YoginiADPeriod(BaseModel):
    """Antardasha sub-period within a Yogini Mahadasha period.

    AD lengths are proportional to the MD length. There are 8 ADs per
    MD (one for each Yogini, starting with the MD-yogini itself).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    ad_yogini: str
    ad_ruling_planet: str
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    fraction_of_md: float


class YoginiMDJudgment(BaseModel):
    """Per-MD judgment carrying the 5 named checks (D-18 keys)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    yogini: str
    ruling_planet: str
    length_years: int
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    age_at_start: float
    age_at_end: float
    is_current: bool
    is_past: bool
    is_future: bool
    antardashas: list[YoginiADPeriod] = Field(default_factory=list)
    checks: dict[str, Finding]
    overall_verdict: Finding

    @model_validator(mode="after")
    def _validate_check_keys(self):
        expected = set(YOGINI_MD_CHECK_KEYS)
        got = set(self.checks.keys())
        missing = sorted(expected - got)
        extra = sorted(got - expected)
        if missing or extra:
            raise ValueError(
                "YoginiMDJudgment.checks must contain exactly the keys in "
                f"YOGINI_MD_CHECK_KEYS. missing={missing!r} extra={extra!r}"
            )
        return self


class YoginiDashaResult(BaseModel):
    """Sequence result — Yogini Dasha timeline for the lifetime.

    ``timeline`` contains chronological :class:`YoginiMDJudgment`
    entries covering ~100 years (about 3 cycles starting from birth).
    Exactly one entry has ``is_current=True``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    starting_yogini: str
    starting_yogini_index: int
    moon_nakshatra_index_1based: int
    timeline: list[YoginiMDJudgment]
    current_md_judgment: YoginiMDJudgment


# ---------------------------------------------------------------------------
# Small helpers (mirrors of vimshottari_md.py for consistency)
# ---------------------------------------------------------------------------


def _validate_asc_sign(value: int) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(
            f"asc_sign must be a 1-indexed sign in 1..12, got {value!r}"
        )
    return value


def _validate_moon_nakshatra(value: int) -> int:
    if not isinstance(value, int) or not (1 <= value <= 27):
        raise ValueError(
            "moon_nakshatra must be a 1-indexed nakshatra in 1..27, "
            f"got {value!r}"
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


def _format_iso(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _moolatrikona(planet: str, lon: float) -> bool:
    rng = MOOLATRIKONA_RANGES.get(planet)
    if rng is None:
        return False
    lo, hi = rng
    norm = lon % 360.0
    return lo <= norm < hi


# ---------------------------------------------------------------------------
# Timeline construction
# ---------------------------------------------------------------------------


def _compute_timeline(
    start_yogini_idx: int, birth_jd: float,
) -> list[dict[str, Any]]:
    """Return chronological MD periods starting at birth.

    Generates ~3 full 36-year cycles (24 MDs) so the timeline always
    covers the full lifetime forecast horizon (108 years).
    """
    if not (0 <= start_yogini_idx < 8):
        raise ValueError(
            f"start_yogini_idx must be in 0..7, got {start_yogini_idx!r}"
        )

    periods: list[dict[str, Any]] = []
    cursor_jd = float(birth_jd)
    # 3 full cycles = 24 MDs ≈ 108 years from birth (well past the
    # standard 100-year forecast horizon).
    for cycle_offset in range(24):
        idx = (start_yogini_idx + cycle_offset) % 8
        years = YOGINI_LENGTHS[idx]
        period_end = cursor_jd + years * _DAYS_PER_VEDIC_YEAR
        periods.append({
            "yogini": YOGINI_NAMES[idx],
            "yogini_index": idx,
            "ruling_planet": YOGINI_RULING_PLANETS[idx],
            "length_years": years,
            "start_jd": cursor_jd,
            "end_jd": period_end,
        })
        cursor_jd = period_end
    return periods


def _compute_ads_for_md(
    md_yogini_idx: int, md_start_jd: float, md_end_jd: float,
) -> list[YoginiADPeriod]:
    """Build 8 antardashas inside the MD, proportional to MD length.

    ADs cycle in the same Yogini order as MDs, starting with the MD
    yogini itself. Each AD's length is ``(ad_yogini_length / 36) *
    md_length_in_days``.
    """
    md_length_days = md_end_jd - md_start_jd
    ads: list[YoginiADPeriod] = []
    cursor_jd = md_start_jd
    for offset in range(8):
        ad_idx = (md_yogini_idx + offset) % 8
        fraction = YOGINI_LENGTHS[ad_idx] / 36.0
        ad_length_days = md_length_days * fraction
        ad_end = cursor_jd + ad_length_days
        ads.append(
            YoginiADPeriod(
                ad_yogini=YOGINI_NAMES[ad_idx],
                ad_ruling_planet=YOGINI_RULING_PLANETS[ad_idx],
                start_jd=float(cursor_jd),
                end_jd=float(ad_end),
                start_date=_format_iso(cursor_jd),
                end_date=_format_iso(ad_end),
                fraction_of_md=float(fraction),
            )
        )
        cursor_jd = ad_end
    return ads


# ---------------------------------------------------------------------------
# Per-check Findings (5 named checks per D-18)
# ---------------------------------------------------------------------------


def _check_ruling_yogini_nature(yogini: str, ruling_planet: str) -> Finding:
    """The deity-nature of the Yogini ruling the MD (D-18 table)."""
    nature = YOGINI_NATURE.get(yogini, "neutral")
    if nature == "benefic":
        direction = "positive"
    elif nature == "malefic":
        direction = "negative"
    else:
        direction = "neutral"
    verdict = (
        f"Yogini {yogini} (ruled by {ruling_planet}) is {nature} by nature"
    )[:140]
    return Finding(
        id="seq_yogini.step_01.ruling_yogini_nature",
        rule="yogini_md.ruling_yogini_nature",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"yogini={yogini}",
            f"ruling_planet={ruling_planet}",
            f"nature={nature}",
            "delegate=in-module YOGINI_NATURE table (D-18)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_ruling_planet_placement(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    ruling_planet: str,
) -> Finding:
    """Bhava (whole-sign from Lagna) of the Yogini ruling planet."""
    rp_sign = _planet_sign(d1_chart, ruling_planet)
    if rp_sign is None:
        return _neutral_finding(
            step_id="seq_yogini.step_02.ruling_planet_placement",
            rule="yogini_md.ruling_planet_placement",
            verdict=(
                f"Ruling planet {ruling_planet} sign unknown — "
                "placement inconclusive"
            ),
            evidence=[
                f"ruling_planet={ruling_planet}",
                f"asc_sign={asc_sign}",
                _DOCTRINE_SENTINEL,
            ],
        )
    bhava = _whole_sign_house(rp_sign, asc_sign)
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
        flavour = "upachaya/dual house"
    verdict = (
        f"Ruling planet {ruling_planet} in bhava {bhava} ({flavour})"
    )[:140]
    return Finding(
        id="seq_yogini.step_02.ruling_planet_placement",
        rule="yogini_md.ruling_planet_placement",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ruling_planet={ruling_planet}",
            f"ruling_planet_sign={rp_sign}",
            f"asc_sign={asc_sign}",
            f"bhava_from_lagna={bhava}",
            f"is_kendra={kendra}",
            f"is_trikona={trikona}",
            f"is_dusthana={dusthana}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_ruling_planet_dignity(
    d1_chart: Mapping[str, Mapping[str, object]],
    ruling_planet: str,
) -> Finding:
    """Dignity (exalted/own/moolatrikona/debilitated) of ruling planet."""
    rp_sign = _planet_sign(d1_chart, ruling_planet)
    rp_lon = _planet_lon(d1_chart, ruling_planet)
    if rp_sign is None:
        return _neutral_finding(
            step_id="seq_yogini.step_03.ruling_planet_dignity",
            rule="yogini_md.ruling_planet_dignity",
            verdict=(
                f"Ruling planet {ruling_planet} sign unknown — "
                "dignity inconclusive"
            ),
            evidence=[
                f"ruling_planet={ruling_planet}",
                _DOCTRINE_SENTINEL,
            ],
        )
    exalted = EXALTATION.get(ruling_planet) == rp_sign
    debilitated = DEBILITATION.get(ruling_planet) == rp_sign
    # Own sign: SIGN_RULERS maps sign->ruler. The planet is in its own sign
    # when SIGN_RULERS[rp_sign] == ruling_planet.
    own_sign = SIGN_RULERS.get(rp_sign) == ruling_planet
    moolatrikona = (
        rp_lon is not None and _moolatrikona(ruling_planet, rp_lon)
    )

    if exalted:
        direction = "positive"
        label = "exalted"
    elif moolatrikona:
        direction = "positive"
        label = "moolatrikona"
    elif own_sign:
        direction = "positive"
        label = "own_sign"
    elif debilitated:
        direction = "negative"
        label = "debilitated"
    else:
        direction = "neutral"
        label = "neutral"
    verdict = (
        f"Ruling planet {ruling_planet} dignity={label} (sign {rp_sign})"
    )[:140]
    return Finding(
        id="seq_yogini.step_03.ruling_planet_dignity",
        rule="yogini_md.ruling_planet_dignity",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ruling_planet={ruling_planet}",
            f"ruling_planet_sign={rp_sign}",
            f"dignity={label}",
            f"exalted={exalted}",
            f"debilitated={debilitated}",
            f"own_sign={own_sign}",
            f"moolatrikona={moolatrikona}",
            "delegate=app.core.dignity (EXALTATION/DEBILITATION/MOOLATRIKONA_RANGES/SIGN_RULERS)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_ruling_planet_in_kendra_or_kona(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    ruling_planet: str,
) -> Finding:
    """Whether the ruling planet sits in a kendra (1/4/7/10) or kona (1/5/9).

    Cross-check with functional_nature: if the planet is in kendra+kona
    AND is a functional yogakaraka for this Lagna, the MD inherits an
    extra rajayoga tone.
    """
    rp_sign = _planet_sign(d1_chart, ruling_planet)
    if rp_sign is None:
        return _neutral_finding(
            step_id="seq_yogini.step_04.ruling_planet_in_kendra_or_kona",
            rule="yogini_md.ruling_planet_in_kendra_or_kona",
            verdict=(
                f"Ruling planet {ruling_planet} sign unknown — "
                "kendra/kona check inconclusive"
            ),
            evidence=[
                f"ruling_planet={ruling_planet}",
                _DOCTRINE_SENTINEL,
            ],
        )
    bhava = _whole_sign_house(rp_sign, asc_sign)
    kendra = bhava in (1, 4, 7, 10)
    kona = bhava in (1, 5, 9)
    # Functional nature overlay.
    fn_table = compute_functional_nature(asc_sign)
    fn_finding = fn_table.get(ruling_planet)
    functional_nature = "unknown"
    if fn_finding is not None:
        for line in fn_finding.evidence:
            if line.startswith("nature="):
                functional_nature = line.split("=", 1)[1]
                break
    is_yogakaraka = functional_nature == "yogakaraka"
    if kendra and kona:
        direction = "positive"
        location = "kendra+kona (rajayoga sthana)"
    elif kendra:
        direction = "positive"
        location = "kendra"
    elif kona:
        direction = "positive"
        location = "kona"
    else:
        direction = "neutral"
        location = f"bhava_{bhava} (non-kendra/non-kona)"
    if is_yogakaraka and (kendra or kona):
        # Yogakaraka in kendra/kona is the strongest single-planet yoga.
        direction = "positive"
    verdict = (
        f"Ruling planet {ruling_planet} in {location}; "
        f"functional_nature={functional_nature}"
    )[:140]
    return Finding(
        id="seq_yogini.step_04.ruling_planet_in_kendra_or_kona",
        rule="yogini_md.ruling_planet_in_kendra_or_kona",
        source_sequence=_SEQUENCE_NAME,
        classification="yoga",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ruling_planet={ruling_planet}",
            f"ruling_planet_sign={rp_sign}",
            f"bhava_from_lagna={bhava}",
            f"is_kendra={kendra}",
            f"is_kona={kona}",
            f"functional_nature={functional_nature}",
            f"is_yogakaraka={is_yogakaraka}",
            "delegate=computations.functional_nature (D-7)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


def _check_cross_check_with_vimshottari(
    chart: Mapping[str, Any], yogini: str, ruling_planet: str,
) -> Finding:
    """Cross-validate the Yogini MD against the active Vimshottari MD.

    Yogini's design purpose: confirm or contradict Vimshottari predictions
    for the same period. A constructive cross-check exists when:

    - the Yogini ruling planet **is** the Vimshottari MD lord (strong
      confirmation), OR
    - the Yogini ruling planet shares the Vimshottari MD lord's sign /
      nakshatra-lord (sympathetic resonance), OR
    - both are classed as benefic Yoginis.

    A contradictive cross-check exists when the Vimshottari MD is
    benefic-flavoured but the Yogini is malefic (Ulka/Sankata), and
    vice versa.
    """
    current = chart.get("current_mahadasha") or {}
    vim_md_lord = current.get("mahadasha_lord")
    if not vim_md_lord:
        return _neutral_finding(
            step_id="seq_yogini.step_05.cross_check_with_vimshottari",
            rule="yogini_md.cross_check_with_vimshottari",
            verdict=(
                "No active Vimshottari MD in chart envelope — "
                "cross-check inconclusive"
            ),
            evidence=[
                f"yogini={yogini}",
                f"ruling_planet={ruling_planet}",
                "vimshottari_md_lord=unknown",
                _DOCTRINE_SENTINEL,
            ],
        )

    same_planet = (ruling_planet == vim_md_lord)
    d1 = chart.get("d1") or {}
    vim_sign = _planet_sign(d1, vim_md_lord)
    rp_sign = _planet_sign(d1, ruling_planet)
    same_sign = (
        vim_sign is not None and rp_sign is not None and vim_sign == rp_sign
    )
    # Sign-depositor resonance: both rulers share a depositor.
    vim_dep = SIGN_RULERS.get(vim_sign) if vim_sign else None
    rp_dep = SIGN_RULERS.get(rp_sign) if rp_sign else None
    same_depositor = (
        vim_dep is not None and rp_dep is not None and vim_dep == rp_dep
    )

    yogini_nature = YOGINI_NATURE.get(yogini, "neutral")

    if same_planet:
        direction = "positive"
        verdict_tone = "Yogini ruling planet == Vimshottari MD lord (strong confirmation)"
    elif same_sign:
        direction = "positive"
        verdict_tone = "Yogini ruling planet shares Vimshottari MD lord sign (sympathetic resonance)"
    elif same_depositor:
        direction = "positive"
        verdict_tone = "Yogini ruling planet shares Vimshottari MD lord depositor"
    elif yogini_nature == "malefic":
        direction = "negative"
        verdict_tone = (
            f"Yogini {yogini} ({yogini_nature}) overlays Vimshottari MD "
            f"{vim_md_lord} — afflictive cross-check"
        )
    elif yogini_nature == "benefic":
        direction = "positive"
        verdict_tone = (
            f"Yogini {yogini} ({yogini_nature}) overlays Vimshottari MD "
            f"{vim_md_lord} — supportive cross-check"
        )
    else:
        direction = "neutral"
        verdict_tone = (
            f"Yogini {yogini} (neutral) and Vimshottari MD {vim_md_lord} "
            "— no resonance signal"
        )
    verdict = verdict_tone[:140]
    return Finding(
        id="seq_yogini.step_05.cross_check_with_vimshottari",
        rule="yogini_md.cross_check_with_vimshottari",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"yogini={yogini}",
            f"yogini_nature={yogini_nature}",
            f"yogini_ruling_planet={ruling_planet}",
            f"vimshottari_md_lord={vim_md_lord}",
            f"same_planet={same_planet}",
            f"same_sign={same_sign}",
            f"same_depositor={same_depositor}",
            "doctrine=Yogini-Vimshottari cross-validation (Maha Tantra Ch.17)",
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
    checks: Mapping[str, Finding], yogini: str, ruling_planet: str,
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
        tone = "Yogini ruler neutrally placed"
    else:
        direction = "mixed"
        tone = "balanced positives and negatives"
    verdict = (
        f"Yogini={yogini} ({ruling_planet}) verdict: {tone}; "
        f"+{pos}/-{neg}/~{mixed}"
    )[:140]
    return Finding(
        id="seq_yogini.overall",
        rule="yogini_md.overall",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"yogini={yogini}",
            f"ruling_planet={ruling_planet}",
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


def _judge_md(
    chart: Mapping[str, Any],
    asc_sign: int,
    period: Mapping[str, Any],
    birth_jd: float,
    is_current: bool,
    is_past: bool,
    is_future: bool,
) -> YoginiMDJudgment:
    d1 = chart["d1"]
    yogini: str = period["yogini"]
    yogini_idx: int = period["yogini_index"]
    ruling_planet: str = period["ruling_planet"]
    length_years: int = period["length_years"]
    start_jd: float = period["start_jd"]
    end_jd: float = period["end_jd"]

    checks: dict[str, Finding] = {
        "ruling_yogini_nature": _check_ruling_yogini_nature(
            yogini, ruling_planet,
        ),
        "ruling_planet_placement": _check_ruling_planet_placement(
            d1, asc_sign, ruling_planet,
        ),
        "ruling_planet_dignity": _check_ruling_planet_dignity(
            d1, ruling_planet,
        ),
        "ruling_planet_in_kendra_or_kona": _check_ruling_planet_in_kendra_or_kona(
            d1, asc_sign, ruling_planet,
        ),
        "cross_check_with_vimshottari": _check_cross_check_with_vimshottari(
            chart, yogini, ruling_planet,
        ),
    }

    overall = _synthesize_overall(checks, yogini, ruling_planet)
    ads = _compute_ads_for_md(yogini_idx, start_jd, end_jd)

    age_at_start = (start_jd - birth_jd) / _DAYS_PER_VEDIC_YEAR
    age_at_end = (end_jd - birth_jd) / _DAYS_PER_VEDIC_YEAR

    return YoginiMDJudgment(
        yogini=yogini,
        ruling_planet=ruling_planet,
        length_years=length_years,
        start_jd=float(start_jd),
        end_jd=float(end_jd),
        start_date=_format_iso(start_jd),
        end_date=_format_iso(end_jd),
        age_at_start=float(age_at_start),
        age_at_end=float(age_at_end),
        is_current=is_current,
        is_past=is_past,
        is_future=is_future,
        antardashas=ads,
        checks=checks,
        overall_verdict=overall,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_sequence(
    chart: dict, asc_sign: int, moon_nakshatra: int,
) -> YoginiDashaResult:
    """Run the Yogini Dasha (5-check) sequence.

    Args:
        chart: Full natal chart dict from
            ``app.core.ephemeris_engine.calculate_all_charts``. Must
            include ``d1``, ``birth_jd`` (or ``jd``), and optionally
            ``current_mahadasha`` for the Vimshottari cross-check.
        asc_sign: 1-indexed natal ascendant rashi.
        moon_nakshatra: 1-indexed natal Moon nakshatra (1..27).
            Callers can convert from 0-indexed via
            ``nakshatra_for_longitude(moon_lon)["index"] + 1``.

    Returns:
        :class:`YoginiDashaResult` — the chronological lifetime
        Yogini timeline plus the singled-out ``current_md_judgment``.

    Raises:
        ValueError: If ``asc_sign`` / ``moon_nakshatra`` are out of
            range or the chart envelope lacks required keys.
    """
    _validate_asc_sign(asc_sign)
    _validate_moon_nakshatra(moon_nakshatra)
    if "d1" not in chart:
        raise ValueError("chart envelope missing required 'd1' key")
    birth_jd_val = chart.get("birth_jd") or chart.get("jd")
    if not isinstance(birth_jd_val, (int, float)):
        raise ValueError("chart envelope missing 'birth_jd' (or 'jd') float")
    birth_jd = float(birth_jd_val)

    start_yogini_idx = NAKSHATRA_TO_YOGINI[moon_nakshatra]
    starting_yogini = YOGINI_NAMES[start_yogini_idx]

    periods = _compute_timeline(start_yogini_idx, birth_jd)

    timeline: list[YoginiMDJudgment] = []
    # First period covers birth — the chart's birth_jd is by construction
    # the start of period[0], so the FIRST period is always is_current=True
    # at birth. For non-birth-time evaluation, we'd compare against
    # chart["query_jd"] but the brief specifies birth-time evaluation.
    # We treat "current" as the period that contains birth_jd.
    for period in periods:
        start_jd = period["start_jd"]
        end_jd = period["end_jd"]
        is_current = start_jd <= birth_jd < end_jd
        is_past = end_jd <= birth_jd
        is_future = start_jd > birth_jd
        judgment = _judge_md(
            chart=chart,
            asc_sign=asc_sign,
            period=period,
            birth_jd=birth_jd,
            is_current=is_current,
            is_past=is_past,
            is_future=is_future,
        )
        timeline.append(judgment)

    currents = [j for j in timeline if j.is_current]
    if len(currents) != 1:
        raise ValueError(
            f"Expected exactly one is_current=True judgment, got {len(currents)}"
        )
    current_md_judgment = currents[0]

    return YoginiDashaResult(
        starting_yogini=starting_yogini,
        starting_yogini_index=start_yogini_idx,
        moon_nakshatra_index_1based=moon_nakshatra,
        timeline=timeline,
        current_md_judgment=current_md_judgment,
    )


__all__ = [
    "NAKSHATRA_TO_YOGINI",
    "YOGINI_LENGTHS",
    "YOGINI_MD_CHECK_KEYS",
    "YOGINI_NAMES",
    "YOGINI_NATURE",
    "YOGINI_RULING_PLANETS",
    "YoginiADPeriod",
    "YoginiDashaResult",
    "YoginiMDJudgment",
    "run_sequence",
]
