"""Doctrine source: notebook NotebookLM proforma — "The Varga System Handbook:
Blueprint for Professional Destiny" (Executive Consulting Methodology).

Sequence 2 — Career Executive Consulting. Four classical checks that an
astrologer applies before issuing a career prediction:

1. **vargottama_amatya_karaka** — identify the Amatya Karaka (the
   professional / consulting karaka) and verify whether it is
   *vargottama* (same sign in D1 and D9). A vargottama AmK is the
   single strongest single-planet career significator possible.

2. **gandanta_knots** — scan the chart for planets sitting in the
   ``+- 3°20'`` ribbon at the three water-to-fire nakshatra junctions
   (Revati-Ashwini, Ashlesha-Magha, Jyeshtha-Mula). A Gandanta planet
   ruling the dasha sequence introduces unstable career transitions.

3. **vimsopaka_strength** — the *Shodashavarga Vimsopaka Bala* score
   (0..20) of the current MD lord. The classical threshold is **>10**;
   below that, predictions about career promise must be downgraded
   regardless of which yogas are present.

4. **gulika_saturn_bottlenecks** — debilitated Saturn in D10's 6th
   house OR Gulika in D10's 10th house signal a *structural* career
   bottleneck (chronic overwork, stalled promotion).

Architectural discipline (per Phase 4 brief)
--------------------------------------------

This module ORCHESTRATES — it does NOT recompute. Delegates:

  * Step 1 -> ``computations.karakas.compute_karakas`` (AmK identity)
              + ``computations.divisional_readings.d9_navamsha`` (vargottama
              flag)
  * Step 2 -> ``computations.gandanta.detect_gandanta``
  * Step 3 -> ``computations.vimsopaka.compute_vimsopaka``
  * Step 4 -> natal Saturn debilitation (``app.core.dignity.DEBILITATION``)
              + ``computations.gulika.compute_gulika_and_mandi``

Public API
==========

    run_sequence(chart, asc_sign, moon_sign, current_md_lord,
                 birth_jd, birth_lat, birth_lon, is_daytime, weekday)
        -> CareerExecutiveResult
"""
from __future__ import annotations

import logging
from typing import Any, Final, Mapping

from app.core.dignity import DEBILITATION, SIGN_RULERS
from app.core.shodashavarga import SHODASHAVARGA_NAMES
from app.reading.computations.divisional_readings.d9_navamsha import (
    read_d9_navamsha,
)
from app.reading.computations.gandanta import detect_gandanta
from app.reading.computations.gulika import compute_gulika_and_mandi
from app.reading.computations.karakas import compute_karakas
from app.reading.computations.vimsopaka import compute_vimsopaka
from app.reading.schema import (
    CAREER_EXECUTIVE_KEYS,
    CareerExecutiveResult,
    ConfidenceScore,
    Finding,
)

logger = logging.getLogger(__name__)


_SEQUENCE_NAME: Final[str] = "career_executive"


_SEQUENCE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=NotebookLM Varga Handbook — Career Executive Methodology"
)


# Vimsopaka classical gate: a dasha lord below ~10/20 is too weak to
# carry a strong career promise per the proforma.
_VIMSOPAKA_THRESHOLD: Final[float] = 10.0


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


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    """Whole-sign house index 1..12 of a planet given the ascendant."""
    return ((planet_sign - asc_sign) % 12) + 1


def _extract_amk_planet(chart: Mapping[str, Any]) -> str | None:
    """Run karakas primitive and return the planet currently holding AmK."""
    karakas = compute_karakas(chart["d1"])
    amk_finding = karakas.get("amatyakaraka")
    if amk_finding is None:
        return None
    for line in amk_finding.evidence:
        if line.startswith("planet="):
            return line.split("=", 1)[1]
    return None


# ---------------------------------------------------------------------------
# Step 1 — vargottama_amatya_karaka
# ---------------------------------------------------------------------------


def _check_vargottama_amatya_karaka(
    chart: Mapping[str, Any], asc_sign: int,
) -> Finding:
    """Step 1: Identify the Amatya Karaka and check vargottama status.

    Delegates to:
      * ``computations.karakas.compute_karakas`` for AmK identity.
      * ``computations.divisional_readings.d9_navamsha.read_d9_navamsha``
        to flag whether the AmK is vargottama (same sign in D1+D9).
    """
    amk_planet = _extract_amk_planet(chart)
    d1_chart = chart["d1"]
    d9_chart = chart["d9"]

    d9_findings = read_d9_navamsha(d1_chart, d9_chart, asc_sign)

    is_vargottama = False
    amk_d1_sign: int | None = None
    amk_d9_sign: int | None = None
    if amk_planet is not None:
        amk_d1_sign = _planet_sign(d1_chart, amk_planet)
        amk_d9_sign = _planet_sign(d9_chart, amk_planet)
        if amk_d1_sign is not None and amk_d9_sign == amk_d1_sign:
            is_vargottama = True

    if amk_planet is None:
        verdict = "Amatya Karaka unidentifiable — career karaka inconclusive"
        direction = "neutral"
    elif is_vargottama:
        verdict = (
            f"Amatyakaraka {amk_planet} VARGOTTAMA "
            f"(D1+D9 sign={amk_d1_sign}) — strong career karaka"
        )
        direction = "positive"
    else:
        verdict = (
            f"Amatyakaraka {amk_planet}: D1 sign={amk_d1_sign}, "
            f"D9 sign={amk_d9_sign} — NOT vargottama"
        )
        direction = "neutral"

    verdict = verdict[:140]

    return Finding(
        id="seq_2.step_1.vargottama_amatya_karaka",
        rule="career_executive.vargottama_amatya_karaka",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"amatyakaraka_planet={amk_planet or 'unknown'}",
            f"amk_d1_sign={amk_d1_sign}",
            f"amk_d9_sign={amk_d9_sign}",
            f"is_vargottama={is_vargottama}",
            f"d9_findings_count={len(d9_findings)}",
            "delegate=karakas + divisional_readings.d9_navamsha (Tier-0/1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 2 — gandanta_knots
# ---------------------------------------------------------------------------


def _check_gandanta_knots(
    chart: Mapping[str, Any], current_md_lord: str,
) -> Finding:
    """Step 2: Scan for Gandanta knots and flag whether MD lord / AmK is hit.

    Delegates to ``computations.gandanta.detect_gandanta``. The
    sequence-level synthesis layers the Gandanta findings against the
    currently-active dasha lord — a Gandanta MD lord is the classical
    "knotted career window" the executive proforma warns about.
    """
    d1_chart = chart["d1"]
    gandanta_findings = detect_gandanta(d1_chart)

    afflicted_planets: list[str] = []
    for f in gandanta_findings:
        # ID grammar: primitive.gandanta.<planet_lowercase>
        if f.id.startswith("primitive.gandanta."):
            afflicted_planets.append(
                f.id.replace("primitive.gandanta.", "").capitalize()
            )

    amk_planet = _extract_amk_planet(chart) or ""
    md_lord_in_gandanta = current_md_lord in afflicted_planets
    amk_in_gandanta = amk_planet in afflicted_planets if amk_planet else False

    direction = (
        "negative" if (md_lord_in_gandanta or amk_in_gandanta) else "neutral"
    )

    if not afflicted_planets:
        verdict = "No Gandanta knots — no water/fire junction afflictions"
    else:
        flag = ""
        if md_lord_in_gandanta:
            flag += f" MD={current_md_lord} HIT;"
        if amk_in_gandanta:
            flag += f" AmK={amk_planet} HIT;"
        verdict = (
            f"Gandanta planets: {', '.join(afflicted_planets)}"
            f"{flag or ' (no MD/AmK overlap)'}"
        )

    verdict = verdict[:140]

    return Finding(
        id="seq_2.step_2.gandanta_knots",
        rule="career_executive.gandanta_knots",
        source_sequence=_SEQUENCE_NAME,
        classification="affliction",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"gandanta_planets={afflicted_planets}",
            f"current_md_lord={current_md_lord}",
            f"md_lord_in_gandanta={md_lord_in_gandanta}",
            f"amatyakaraka={amk_planet or 'unknown'}",
            f"amk_in_gandanta={amk_in_gandanta}",
            "delegate=computations.gandanta.detect_gandanta (Tier-0)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 3 — vimsopaka_strength
# ---------------------------------------------------------------------------


def _check_vimsopaka_strength(
    chart: Mapping[str, Any], current_md_lord: str,
) -> Finding:
    """Step 3: Verify MD lord's Vimsopaka score against the >10 threshold.

    Delegates to ``computations.vimsopaka.compute_vimsopaka``. Below
    the threshold every downstream career claim must be downgraded —
    this step is the *gate* the proforma puts in front of the rest of
    the career synthesis.
    """
    d1_chart = chart["d1"]
    div_charts = chart.get("divisional_charts", {})

    # Build the divisor -> chart map expected by compute_vimsopaka.
    varga_in: dict[int, dict] = {1: d1_chart, 9: chart["d9"], 10: chart["d10"]}
    for divisor, name in SHODASHAVARGA_NAMES.items():
        if divisor in varga_in:
            continue
        candidate = div_charts.get(name)
        if isinstance(candidate, dict):
            varga_in[divisor] = candidate

    findings = compute_vimsopaka(d1_chart, varga_in)
    md_finding = findings.get(current_md_lord)

    score: float | None = None
    band = "n/a"
    if md_finding is not None:
        for line in md_finding.evidence:
            if line.startswith("score="):
                try:
                    score = float(line.split("=", 1)[1])
                except ValueError:
                    score = None
            elif line.startswith("band="):
                band = line.split("=", 1)[1]

    passes_gate = score is not None and score > _VIMSOPAKA_THRESHOLD
    direction = "positive" if passes_gate else "negative" if score is not None else "neutral"

    if score is None:
        verdict = (
            f"MD lord {current_md_lord}: Vimsopaka unavailable — gate inconclusive"
        )
    elif passes_gate:
        verdict = (
            f"MD lord {current_md_lord} Vimsopaka {score:.2f} ({band}) — gate PASS (>10)"
        )
    else:
        verdict = (
            f"MD lord {current_md_lord} Vimsopaka {score:.2f} ({band}) — gate FAIL (<=10)"
        )

    verdict = verdict[:140]

    return Finding(
        id="seq_2.step_3.vimsopaka_strength",
        rule="career_executive.vimsopaka_strength",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={current_md_lord}",
            f"md_lord_vimsopaka_score={score if score is not None else -1.0}",
            f"md_lord_vimsopaka_band={band}",
            f"threshold={_VIMSOPAKA_THRESHOLD}",
            f"gate_passes={passes_gate}",
            "delegate=computations.vimsopaka.compute_vimsopaka (Tier-0)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 4 — gulika_saturn_bottlenecks
# ---------------------------------------------------------------------------


def _check_gulika_saturn_bottlenecks(
    chart: Mapping[str, Any],
    asc_sign: int,
    birth_jd: float,
    birth_lat: float,
    birth_lon: float,
    is_daytime: bool,
    weekday: int,
) -> Finding:
    """Step 4: Detect classical career bottlenecks.

    Two patterns from the proforma:

      * **Saturn debilitated in D10-6H**: chronic overwork bottleneck.
        Saturn is debilitated in Aries (sign 1). The 6H from D10's
        lagna (which inherits the D1 ascendant per the project's
        convention) is sign ``((asc - 1 + 5) % 12) + 1``.

      * **Gulika in D10-10H**: the chart's master-bottleneck point
        falling on the very career-significator house.

    Delegates to ``computations.gulika.compute_gulika_and_mandi`` for
    Gulika's longitude/sign and ``app.core.dignity.DEBILITATION`` for
    Saturn's debilitation sign.
    """
    d10_chart = chart["d10"]

    # Saturn in D10: get its sign and compute its D10-house from asc.
    saturn_d10_sign = _planet_sign(d10_chart, "Saturn")
    saturn_debilitated_sign = DEBILITATION["Saturn"]
    saturn_debilitated = saturn_d10_sign == saturn_debilitated_sign
    saturn_d10_house = (
        _whole_sign_house(saturn_d10_sign, asc_sign)
        if saturn_d10_sign is not None
        else None
    )
    saturn_in_d10_6h = saturn_d10_house == 6
    saturn_bottleneck = saturn_debilitated and saturn_in_d10_6h

    # Gulika longitude -> sign -> D10-house.
    upagrahas = compute_gulika_and_mandi(
        birth_jd=birth_jd,
        lat=birth_lat,
        lon=birth_lon,
        is_daytime=is_daytime,
        weekday=weekday,
    )
    gulika_finding = upagrahas["gulika"]
    gulika_lon: float | None = None
    gulika_sign: int | None = None
    for line in gulika_finding.evidence:
        if line.startswith("longitude="):
            try:
                gulika_lon = float(line.split("=", 1)[1])
            except ValueError:
                gulika_lon = None
    if gulika_lon is not None:
        # Sign is 1-indexed from longitude in the D1 zodiac. Gulika is
        # always a *natal* position so we use the natal sign directly.
        gulika_sign = int(gulika_lon // 30.0) % 12 + 1

    gulika_d10_house: int | None = None
    # Gulika's D10-house uses the *natal* sign — Gulika is not re-projected
    # into D10 in classical doctrine; the bottleneck pattern asks whether
    # Gulika sits in the natal 10th. Mirror that: house counted from asc.
    if gulika_sign is not None:
        gulika_d10_house = _whole_sign_house(gulika_sign, asc_sign)
    gulika_bottleneck = gulika_d10_house == 10

    any_bottleneck = saturn_bottleneck or gulika_bottleneck
    direction = "negative" if any_bottleneck else "neutral"

    if not any_bottleneck:
        verdict = (
            f"No structural bottleneck: Saturn D10 sign={saturn_d10_sign}, "
            f"Gulika natal sign={gulika_sign}"
        )
    else:
        parts = []
        if saturn_bottleneck:
            parts.append("debilitated Saturn in D10-6H (overwork)")
        if gulika_bottleneck:
            parts.append("Gulika in 10H (master-bottleneck)")
        verdict = "Bottleneck detected: " + "; ".join(parts)

    verdict = verdict[:140]

    return Finding(
        id="seq_2.step_4.gulika_saturn_bottlenecks",
        rule="career_executive.gulika_saturn_bottlenecks",
        source_sequence=_SEQUENCE_NAME,
        classification="affliction",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"saturn_d10_sign={saturn_d10_sign}",
            f"saturn_d10_house={saturn_d10_house}",
            f"saturn_debilitated_in_d10={saturn_debilitated}",
            f"saturn_bottleneck_6h_d10={saturn_bottleneck}",
            f"gulika_longitude={gulika_lon}",
            f"gulika_sign={gulika_sign}",
            f"gulika_d10_house={gulika_d10_house}",
            f"gulika_bottleneck_10h={gulika_bottleneck}",
            "delegate=computations.gulika + dignity.DEBILITATION (Tier-0)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Overall verdict
# ---------------------------------------------------------------------------


def _overall_verdict(
    steps: dict[str, Finding], current_md_lord: str,
) -> Finding:
    pos = sum(1 for f in steps.values() if f.direction == "positive")
    neg = sum(1 for f in steps.values() if f.direction == "negative")

    if pos > neg:
        direction = "positive"
        tone = "career promise constructively confirmed"
    elif neg > pos:
        direction = "negative"
        tone = "structural career impediments dominate"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "career signals neutral"
    else:
        direction = "mixed"
        tone = "career signals mixed (positive + negative balanced)"

    verdict = (
        f"Career executive verdict (MD={current_md_lord}): {tone}; "
        f"+{pos}/-{neg}"
    )[:140]

    return Finding(
        id="seq_2.overall",
        rule="career_executive.overall",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"positive_steps={pos}",
            f"negative_steps={neg}",
            f"current_md_lord={current_md_lord}",
            f"step_directions={ {k: v.direction for k, v in steps.items()} }",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_sequence(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    current_md_lord: str,
    birth_jd: float,
    birth_lat: float,
    birth_lon: float,
    is_daytime: bool,
    weekday: int,
) -> CareerExecutiveResult:
    """Run the 4-step Career Executive Consulting orchestration.

    Args:
        chart: Full natal chart from
            ``app.core.ephemeris_engine.calculate_all_charts``.
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi. Reserved for downstream
            extension (planets-from-Moon checks); current
            implementation does not depend on it directly.
        current_md_lord: Currently-active Mahadasha lord name.
        birth_jd: Julian Day at birth (needed for Gulika).
        birth_lat: Geographic latitude in decimal degrees (north positive).
        birth_lon: Geographic longitude in decimal degrees (east positive).
        is_daytime: True if birth was between sunrise and sunset.
        weekday: 0..6 with 0=Sunday (matches
            ``app.core.panchanga._vara_info`` convention).

    Returns:
        :class:`CareerExecutiveResult` — schema-validated; ``steps``
        keys are exactly :data:`CAREER_EXECUTIVE_KEYS`.

    Raises:
        ValueError: If inputs are out of range (asc_sign,
            moon_sign, weekday) or the MD lord string is empty.
    """
    _validate_asc_sign(asc_sign)
    if not isinstance(moon_sign, int) or not (1 <= moon_sign <= 12):
        raise ValueError(
            f"moon_sign must be a 1-indexed sign in 1..12, got {moon_sign!r}"
        )
    if not isinstance(current_md_lord, str) or not current_md_lord:
        raise ValueError("current_md_lord must be a non-empty planet name")
    if not 0 <= weekday <= 6:
        raise ValueError(f"weekday must be 0..6, got {weekday}")

    step_amk = _check_vargottama_amatya_karaka(chart, asc_sign)
    step_gandanta = _check_gandanta_knots(chart, current_md_lord)
    step_vimsopaka = _check_vimsopaka_strength(chart, current_md_lord)
    step_bottleneck = _check_gulika_saturn_bottlenecks(
        chart, asc_sign, birth_jd, birth_lat, birth_lon, is_daytime, weekday,
    )

    steps: dict[str, Finding] = {
        "vargottama_amatya_karaka": step_amk,
        "gandanta_knots": step_gandanta,
        "vimsopaka_strength": step_vimsopaka,
        "gulika_saturn_bottlenecks": step_bottleneck,
    }
    assert set(steps.keys()) == set(CAREER_EXECUTIVE_KEYS), (
        "CAREER_EXECUTIVE_KEYS / steps mismatch"
    )

    overall = _overall_verdict(steps, current_md_lord)

    return CareerExecutiveResult(steps=steps, overall_verdict=overall)


__all__ = ["run_sequence"]
