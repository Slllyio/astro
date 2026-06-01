"""Sequence 6 — Vimshottari Antardasha 7-check judgment (D-15 locked).

Doctrine source
===============

Notebook NotebookLM proforma — "How To Read Antardasha In Vedic
Astrology". The Antardasha (AD) is the second-order period inside a
Mahadasha (MD); it modulates how the MD lord's promise plays out. The
7 check keys are locked in ``docs/doctrine-decisions.md`` D-15 and
reproduced verbatim in ``app/reading/schema.py`` as ``AD_CHECK_KEYS``.

The 7 checks (verbatim from D-15):

  1. ``rulership_of_ad_lord``         — Houses owned by AD lord (what it activates)
  2. ``house_placement_of_ad_lord``   — Bhava occupied by AD lord (where results play out)
  3. ``strength_dignity_influence``   — Combust/exalted/debilitated/dignified state
  4. ``rajyoga_formed``               — Latent Rajyogas activated by AD lord
  5. ``afflictions``                  — Pap Kartari, malefic aspects, MKS, graha yuddha
  6. ``divisional_chart_assessment``  — D3/D7/D9/D10 confirmation for AD lord
  7. ``mutual_position_md_ad``        — 6/8/12 friction vs trinal support between MD and AD lords

Architectural discipline (per Phase 4 brief)
============================================

This module ORCHESTRATES — it does NOT recompute. Each ``_check_*``
private function delegates to an existing Tier-0/1/2 module:

  * Step 1 → ``app.core.dignity.SIGN_RULERS`` (which signs the AD lord owns)
  * Step 2 → whole-sign-house arithmetic against natal Lagna
  * Step 3 → ``app.core.shadbala.is_exalted`` / ``is_debilitated`` +
              ``app.core.planet_state.is_combust``
  * Step 4 → ``computations.yogas_extended.detect_yogas`` (filter for
              AD-lord involvement)
  * Step 5 → ``computations.marana_karaka_sthana.detect_mks`` +
              ``computations.graha_yuddha.detect_graha_yuddha`` +
              Kartari overlay
  * Step 6 → ``computations.divisional_readings.d3_drekkana`` +
              ``d7_saptamsa`` + ``d9_navamsha`` + ``d10_dashamsha``
              (sign-overlap check for AD lord across the four vargas)
  * Step 7 → sign-distance arithmetic (whole-sign) between MD and AD
              lord placements

KP-contamination audit clean — every check name is pure Parashari
rashi-depositor logic; no "sub-lord" / "cuspal-sub" / KP-specific
terminology.

Public API
==========

    run_sequence(
        chart, asc_sign, moon_sign,
        current_md_lord, current_md_start_jd, current_md_end_jd,
    ) -> VimshottariADResult

Per spec Section 2 scope lock:

  - ``current_md_ads`` — list of :class:`ADJudgment` covering the
    leftover ADs of the *current* MD (from "now" onward).
  - ``next_md_first_3_ads`` — the first 3 ADs of the *next* MD.
"""
from __future__ import annotations

import logging
from typing import Any, Final, Mapping

import swisseph as swe
from pydantic import BaseModel, ConfigDict, Field

from app.core.dignity import (
    DEBILITATION,
    EXALTATION,
    OWN_SIGNS,
    SIGN_RULERS,
)
from app.core.ephemeris_engine import DASHA_LORDS, DAYS_PER_VEDIC_YEAR
from app.core.planet_state import is_combust
from app.core.shadbala import is_debilitated, is_exalted, is_moolatrikona
from app.reading.computations.divisional_readings.d3_drekkana import (
    read_d3_drekkana,
)
from app.reading.computations.divisional_readings.d7_saptamsa import (
    read_d7_saptamsa,
)
from app.reading.computations.divisional_readings.d9_navamsha import (
    read_d9_navamsha,
)
from app.reading.computations.graha_yuddha import detect_graha_yuddha
from app.reading.computations.marana_karaka_sthana import detect_mks
from app.reading.computations.yogas_extended import (
    detect_yogas as detect_extended_yogas,
)
from app.reading.schema import (
    AD_CHECK_KEYS,
    ADJudgment,
    ConfidenceScore,
    Finding,
)

logger = logging.getLogger(__name__)


_SEQUENCE_NAME: Final[str] = "vimshottari_ad"


_SEQUENCE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=NotebookLM 'How To Read Antardasha' — D-15"
)

_BENEFICS: Final[frozenset[str]] = frozenset(
    {"Jupiter", "Venus", "Mercury", "Moon"}
)
_MALEFICS: Final[frozenset[str]] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)

_ALL_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


# ---------------------------------------------------------------------------
# VimshottariADResult — local wrapper (schema.py is read-only per brief)
# ---------------------------------------------------------------------------


class VimshottariADResult(BaseModel):
    """Sequence 6 — Vimshottari Antardasha judgments.

    Per the spec Section 2 scope lock the engine emits ADs for two
    cohorts: the leftover ADs of the current MD, and the first 3 ADs
    of the next MD. Each :class:`ADJudgment` carries the exact 7 keys
    in :data:`AD_CHECK_KEYS`.

    Downstream consumers fold these into
    ``SequencesBlock.ad_judgments`` (a flat list).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    current_md_ads: list[ADJudgment] = Field(default_factory=list)
    next_md_first_3_ads: list[ADJudgment] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
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


def _sign_distance_forward(from_sign: int, to_sign: int) -> int:
    return ((to_sign - from_sign) % 12) + 1


def _signs_ruled_by(planet: str) -> list[int]:
    """Whole-sign signs ruled by ``planet``. Empty for nodes."""
    return [s for s, p in SIGN_RULERS.items() if p == planet]


def _format_iso(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


# ---------------------------------------------------------------------------
# Step 1 — rulership_of_ad_lord
# ---------------------------------------------------------------------------


def _check_rulership_of_ad_lord(
    asc_sign: int, ad_lord: str,
) -> Finding:
    """Houses owned by AD lord from natal Lagna (whole-sign).

    A Rajyoga-grade rulership (1/4/5/7/9/10 — kendra+trikona) is the
    classical "what the AD activates" answer.
    """
    signs_ruled = _signs_ruled_by(ad_lord)
    houses_ruled = sorted(_whole_sign_house(s, asc_sign) for s in signs_ruled)
    rajyoga_houses = [h for h in houses_ruled if h in (1, 4, 5, 7, 9, 10)]
    dusthana_houses = [h for h in houses_ruled if h in (6, 8, 12)]
    if rajyoga_houses and not dusthana_houses:
        direction = "positive"
    elif dusthana_houses and not rajyoga_houses:
        direction = "negative"
    elif rajyoga_houses and dusthana_houses:
        direction = "mixed"
    elif not houses_ruled:
        # Nodes own no signs.
        direction = "neutral"
    else:
        direction = "neutral"
    verdict = (
        f"AD lord {ad_lord} rules houses {houses_ruled} from Lagna"
    )[:140]
    return Finding(
        id="seq_6.step_1.rulership_of_ad_lord",
        rule="ad.rulership_of_ad_lord",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ad_lord={ad_lord}",
            f"signs_ruled={signs_ruled}",
            f"houses_ruled_from_lagna={houses_ruled}",
            f"rajyoga_houses={rajyoga_houses}",
            f"dusthana_houses={dusthana_houses}",
            "delegate=app.core.dignity.SIGN_RULERS",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 2 — house_placement_of_ad_lord
# ---------------------------------------------------------------------------


def _check_house_placement_of_ad_lord(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    ad_lord: str,
) -> Finding:
    """Whole-sign bhava occupied by AD lord."""
    ad_sign = _planet_sign(d1_chart, ad_lord)
    if ad_sign is None:
        return _neutral_finding(
            step_id="seq_6.step_2.house_placement_of_ad_lord",
            rule="ad.house_placement_of_ad_lord",
            verdict=f"AD lord {ad_lord} sign unknown — placement inconclusive",
            evidence=[f"ad_lord={ad_lord}", _DOCTRINE_SENTINEL],
        )
    bhava = _whole_sign_house(ad_sign, asc_sign)
    kendra = bhava in (1, 4, 7, 10)
    trikona = bhava in (1, 5, 9)
    dusthana = bhava in (6, 8, 12)
    if trikona:
        direction = "positive"
        flavour = "trikona"
    elif kendra:
        direction = "positive"
        flavour = "kendra"
    elif dusthana:
        direction = "negative"
        flavour = "dusthana"
    else:
        direction = "neutral"
        flavour = "neutral upachaya/dual"
    verdict = (
        f"AD lord {ad_lord} occupies bhava {bhava} ({flavour}) from Lagna"
    )[:140]
    return Finding(
        id="seq_6.step_2.house_placement_of_ad_lord",
        rule="ad.house_placement_of_ad_lord",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ad_lord={ad_lord}",
            f"ad_sign={ad_sign}",
            f"bhava_from_lagna={bhava}",
            f"is_kendra={kendra}",
            f"is_trikona={trikona}",
            f"is_dusthana={dusthana}",
            "delegate=whole-sign-house arithmetic",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 3 — strength_dignity_influence
# ---------------------------------------------------------------------------


def _check_strength_dignity_influence(
    d1_chart: Mapping[str, Mapping[str, object]], ad_lord: str,
) -> Finding:
    """Combust / exalted / debilitated / moolatrikona state of AD lord."""
    ad_sign = _planet_sign(d1_chart, ad_lord)
    ad_lon = _planet_lon(d1_chart, ad_lord)
    sun_lon = _planet_lon(d1_chart, "Sun")
    exalted = bool(ad_sign is not None and is_exalted(ad_lord, ad_sign))
    debilitated = bool(ad_sign is not None and is_debilitated(ad_lord, ad_sign))
    moolatrikona = bool(
        ad_sign is not None and is_moolatrikona(ad_lord, ad_sign)
    )
    own_sign = ad_sign in OWN_SIGNS.get(ad_lord, ())
    combust = bool(
        ad_lord not in ("Sun", "Rahu", "Ketu")
        and ad_lon is not None
        and sun_lon is not None
        and is_combust(ad_lord, ad_lon, sun_lon)
    )
    if exalted or moolatrikona:
        direction = "positive"
        state = "exalted" if exalted else "moolatrikona"
    elif own_sign:
        direction = "positive"
        state = "own_sign"
    elif debilitated or combust:
        direction = "negative"
        state = "debilitated" if debilitated else "combust"
    else:
        direction = "neutral"
        state = "neutral"
    verdict = (
        f"AD lord {ad_lord} dignity = {state} (sign {ad_sign})"
    )[:140]
    return Finding(
        id="seq_6.step_3.strength_dignity_influence",
        rule="ad.strength_dignity_influence",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ad_lord={ad_lord}",
            f"ad_sign={ad_sign}",
            f"exalted={exalted}",
            f"debilitated={debilitated}",
            f"moolatrikona={moolatrikona}",
            f"own_sign={own_sign}",
            f"combust={combust}",
            f"state={state}",
            "delegate=app.core.shadbala + planet_state.is_combust",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 4 — rajyoga_formed
# ---------------------------------------------------------------------------


def _check_rajyoga_formed(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    moon_sign: int,
    ad_lord: str,
) -> Finding:
    """Latent Rajyogas activated by AD lord.

    Delegates to ``computations.yogas_extended.detect_yogas`` and
    filters for yogas whose evidence mentions the AD lord — these are
    the rajayogas (kendra-trikona, parivartana, neech bhanga, etc.)
    that switch on when the AD lord's energy fires.
    """
    try:
        all_yogas = detect_extended_yogas(d1_chart, asc_sign, moon_sign)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rajyoga_formed yogas detection failed: %s", exc)
        all_yogas = []
    ad_involved: list[str] = []
    for y in all_yogas:
        text = y.verdict + " " + " ".join(y.evidence)
        if ad_lord in text:
            ad_involved.append(y.rule)
    direction = "positive" if ad_involved else "neutral"
    verdict = (
        f"AD lord {ad_lord} involved in {len(ad_involved)} latent yogas"
    )[:140]
    return Finding(
        id="seq_6.step_4.rajyoga_formed",
        rule="ad.rajyoga_formed",
        source_sequence=_SEQUENCE_NAME,
        classification="yoga",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ad_lord={ad_lord}",
            f"total_yogas_detected={len(all_yogas)}",
            f"yogas_involving_ad_lord={sorted(set(ad_involved))}",
            "delegate=computations.yogas_extended.detect_yogas",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 5 — afflictions
# ---------------------------------------------------------------------------


def _check_afflictions(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    ad_lord: str,
) -> Finding:
    """Pap Kartari, MKS, graha yuddha on AD lord."""
    ad_sign = _planet_sign(d1_chart, ad_lord)
    afflictions: list[str] = []

    # Pap Kartari: 12th and 2nd from AD lord both occupied by malefics.
    if ad_sign is not None:
        twelfth_sign = ((ad_sign - 1 - 1) % 12) + 1
        second_sign = ((ad_sign - 1 + 1) % 12) + 1
        twelfth_occ = [
            p for p in _ALL_PLANETS
            if p != ad_lord and _planet_sign(d1_chart, p) == twelfth_sign
        ]
        second_occ = [
            p for p in _ALL_PLANETS
            if p != ad_lord and _planet_sign(d1_chart, p) == second_sign
        ]
        if (
            twelfth_occ and second_occ
            and all(p in _MALEFICS for p in twelfth_occ)
            and all(p in _MALEFICS for p in second_occ)
        ):
            afflictions.append("pap_kartari")

    # MKS.
    try:
        mks = detect_mks(d1_chart, asc_sign)
        if ad_lord in mks:
            afflictions.append("marana_karaka_sthana")
    except Exception as exc:  # noqa: BLE001
        logger.warning("MKS detection failed for AD %s: %s", ad_lord, exc)

    # Graha yuddha — is AD lord the loser?
    try:
        gy_findings = detect_graha_yuddha(d1_chart)
        for f in gy_findings:
            ev = " ".join(f.evidence)
            if f"loser={ad_lord}" in ev:
                afflictions.append("graha_yuddha_loser")
                break
    except Exception as exc:  # noqa: BLE001
        logger.warning("Graha yuddha detection failed: %s", exc)

    direction = "negative" if afflictions else "neutral"
    verdict = (
        f"AD lord {ad_lord} afflictions: {afflictions or 'none'}"
    )[:140]
    return Finding(
        id="seq_6.step_5.afflictions",
        rule="ad.afflictions",
        source_sequence=_SEQUENCE_NAME,
        classification="affliction",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ad_lord={ad_lord}",
            f"ad_sign={ad_sign}",
            f"afflictions={afflictions}",
            "delegate=marana_karaka_sthana + graha_yuddha + kartari overlay",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 6 — divisional_chart_assessment
# ---------------------------------------------------------------------------


def _check_divisional_chart_assessment(
    chart: Mapping[str, Any], asc_sign: int, ad_lord: str,
) -> Finding:
    """D3 / D7 / D9 / D10 confirmation for AD lord — counts the divisional
    findings that mention the AD lord (a higher count signals consistent
    cross-varga support)."""
    d1 = chart["d1"]
    d3 = chart.get("divisional_charts", {}).get("Drekkana")
    d7 = chart.get("divisional_charts", {}).get("Saptamsa")
    d9 = chart["d9"]
    d10 = chart["d10"]
    hits: dict[str, int] = {}
    for varga_name, reader, args in (
        ("D3", read_d3_drekkana, (d3, asc_sign) if d3 else None),
        ("D7", read_d7_saptamsa, (d7, asc_sign) if d7 else None),
        ("D9", read_d9_navamsha, (d1, d9, asc_sign)),
    ):
        if args is None:
            continue
        try:
            findings = reader(*args)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Divisional read %s failed for AD %s: %s",
                varga_name, ad_lord, exc,
            )
            continue
        count = 0
        for f in findings.values():
            text = f.verdict + " " + " ".join(f.evidence)
            if ad_lord in text:
                count += 1
        hits[varga_name] = count

    # D10 reader requires an amatya_karaka argument; without re-running
    # the AmK identification we record the AD lord's D10 sign placement
    # only — a lighter-weight confirmation than the full reader.
    d10_sign = _planet_sign(d10, ad_lord)
    if d10_sign is not None:
        hits["D10_sign"] = d10_sign

    total_hits = sum(v for k, v in hits.items() if k != "D10_sign")
    direction = (
        "positive" if total_hits >= 3
        else "neutral" if total_hits >= 1
        else "neutral"
    )
    verdict = (
        f"AD lord {ad_lord} divisional hits: {hits}; total={total_hits}"
    )[:140]
    return Finding(
        id="seq_6.step_6.divisional_chart_assessment",
        rule="ad.divisional_chart_assessment",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"ad_lord={ad_lord}",
            f"divisional_hits={hits}",
            f"total_hits={total_hits}",
            "delegate=divisional_readings (d3/d7/d9) + d10 sign-overlap",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 7 — mutual_position_md_ad
# ---------------------------------------------------------------------------


def _check_mutual_position_md_ad(
    d1_chart: Mapping[str, Mapping[str, object]],
    md_lord: str,
    ad_lord: str,
) -> Finding:
    """6/8/12 friction vs trinal (5/9) support between MD and AD lord
    sign-positions."""
    md_sign = _planet_sign(d1_chart, md_lord)
    ad_sign = _planet_sign(d1_chart, ad_lord)
    if md_sign is None or ad_sign is None:
        return _neutral_finding(
            step_id="seq_6.step_7.mutual_position_md_ad",
            rule="ad.mutual_position_md_ad",
            verdict=f"MD/AD sign unknown — mutual position inconclusive",
            evidence=[
                f"md_lord={md_lord}",
                f"ad_lord={ad_lord}",
                _DOCTRINE_SENTINEL,
            ],
        )
    # Distance AD-from-MD and MD-from-AD (forward 1..12).
    ad_from_md = _sign_distance_forward(md_sign, ad_sign)
    md_from_ad = _sign_distance_forward(ad_sign, md_sign)
    friction_houses = {6, 8, 12}
    trinal_houses = {5, 9}
    if md_lord == ad_lord:
        # Identical lord (e.g. Mercury MD - Mercury AD).
        direction = "neutral"
        relation = "identical_lord"
    elif ad_from_md in trinal_houses and md_from_ad in trinal_houses:
        direction = "positive"
        relation = "mutual_trinal_support"
    elif ad_from_md in friction_houses or md_from_ad in friction_houses:
        direction = "negative"
        relation = "6_8_12_friction"
    elif ad_from_md in (1, 7) and md_from_ad in (1, 7):
        direction = "mixed"
        relation = "conjoined_or_opposite"
    else:
        direction = "neutral"
        relation = "neutral_distance"
    verdict = (
        f"MD={md_lord} ↔ AD={ad_lord}: ad_from_md={ad_from_md}, "
        f"md_from_ad={md_from_ad} — {relation}"
    )[:140]
    return Finding(
        id="seq_6.step_7.mutual_position_md_ad",
        rule="ad.mutual_position_md_ad",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"ad_lord={ad_lord}",
            f"md_sign={md_sign}",
            f"ad_sign={ad_sign}",
            f"ad_from_md={ad_from_md}",
            f"md_from_ad={md_from_ad}",
            f"relation={relation}",
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
    checks: Mapping[str, Finding], md_lord: str, ad_lord: str,
) -> Finding:
    pos = sum(1 for f in checks.values() if f.direction == "positive")
    neg = sum(1 for f in checks.values() if f.direction == "negative")
    mixed = sum(1 for f in checks.values() if f.direction == "mixed")
    if pos > neg + mixed:
        direction = "positive"
        tone = "AD supports MD's promise"
    elif neg > pos + mixed:
        direction = "negative"
        tone = "AD modulates MD toward affliction"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "AD neutrally modulates MD"
    else:
        direction = "mixed"
        tone = "AD effect mixed"
    verdict = (
        f"MD={md_lord} AD={ad_lord}: {tone}; +{pos}/-{neg}/~{mixed}"
    )[:140]
    return Finding(
        id="seq_6.overall",
        rule="ad.overall",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"ad_lord={ad_lord}",
            f"positive_checks={pos}",
            f"negative_checks={neg}",
            f"mixed_checks={mixed}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Per-AD judgment orchestrator
# ---------------------------------------------------------------------------


def _judge_antardasha(
    chart: Mapping[str, Any],
    asc_sign: int,
    moon_sign: int,
    md_lord: str,
    ad_lord: str,
    start_jd: float,
    end_jd: float,
    birth_jd: float,
) -> ADJudgment:
    """Build an :class:`ADJudgment` by running all 7 named checks."""
    d1 = chart["d1"]

    checks: dict[str, Finding] = {
        "rulership_of_ad_lord": _check_rulership_of_ad_lord(asc_sign, ad_lord),
        "house_placement_of_ad_lord": _check_house_placement_of_ad_lord(
            d1, asc_sign, ad_lord,
        ),
        "strength_dignity_influence": _check_strength_dignity_influence(
            d1, ad_lord,
        ),
        "rajyoga_formed": _check_rajyoga_formed(d1, asc_sign, moon_sign, ad_lord),
        "afflictions": _check_afflictions(d1, asc_sign, ad_lord),
        "divisional_chart_assessment": _check_divisional_chart_assessment(
            chart, asc_sign, ad_lord,
        ),
        "mutual_position_md_ad": _check_mutual_position_md_ad(
            d1, md_lord, ad_lord,
        ),
    }

    overall = _synthesize_overall(checks, md_lord, ad_lord)

    age_at_start = (start_jd - birth_jd) / DAYS_PER_VEDIC_YEAR
    age_at_end = (end_jd - birth_jd) / DAYS_PER_VEDIC_YEAR

    # is_current/is_past/is_future are with respect to birth_jd. Note
    # that ADs in the leftover of the current MD straddle birth_jd; the
    # surface convention here mirrors MD: the AD that contains birth_jd
    # is "current"; ADs after birth_jd are "future"; before are "past".
    is_current = start_jd <= birth_jd < end_jd
    is_past = end_jd <= birth_jd
    is_future = start_jd > birth_jd

    return ADJudgment(
        ad_lord=ad_lord,
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
# AD-sequence period derivation
# ---------------------------------------------------------------------------


def _ad_sequence_for_md(
    md_lord: str,
    md_total_years: float,
    md_start_jd: float,
) -> list[dict[str, Any]]:
    """Compute the 9 ADs of a given MD (lord + start_jd + total years).

    Mirrors the math in ``app.core.antardasha.compute_antardashas`` but
    works for an *arbitrary* MD (not just the current one), so we can
    derive the next MD's ADs as well.

    Returns list of dicts with ``ad_lord``, ``start_jd``, ``end_jd``.
    """
    lord_names = [n for n, _ in DASHA_LORDS]
    start_index = lord_names.index(md_lord)
    n = len(DASHA_LORDS)

    out: list[dict[str, Any]] = []
    cursor = md_start_jd
    for offset in range(n):
        ad_lord, ad_lord_years = DASHA_LORDS[(start_index + offset) % n]
        duration_years = md_total_years * ad_lord_years / 120
        ad_start = cursor
        ad_end = ad_start + duration_years * DAYS_PER_VEDIC_YEAR
        out.append(
            {
                "ad_lord": ad_lord,
                "start_jd": ad_start,
                "end_jd": ad_end,
            }
        )
        cursor = ad_end
    return out


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_sequence(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    current_md_lord: str,
    current_md_start_jd: float,
    current_md_end_jd: float,
) -> VimshottariADResult:
    """Run the 7-step Vimshottari Antardasha judgment per spec §2 scope.

    Args:
        chart: Full natal chart dict (see
            ``app.core.ephemeris_engine.calculate_all_charts``).
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi.
        current_md_lord: Currently-active Mahadasha lord.
        current_md_start_jd: Julian Day of current MD start.
        current_md_end_jd: Julian Day of current MD end.

    Returns:
        :class:`VimshottariADResult` — schema-validated; each
        :class:`ADJudgment` carries the exact 7 keys in
        :data:`AD_CHECK_KEYS`.

    Raises:
        ValueError: If asc_sign / moon_sign are out of range, or the
            current_md_lord is missing, or the chart envelope is
            malformed.
    """
    _validate_asc_sign(asc_sign)
    if not isinstance(moon_sign, int) or not (1 <= moon_sign <= 12):
        raise ValueError(
            f"moon_sign must be a 1-indexed sign in 1..12, got {moon_sign!r}"
        )
    if not isinstance(current_md_lord, str) or not current_md_lord:
        raise ValueError("current_md_lord must be a non-empty planet name")
    if "d1" not in chart or "d9" not in chart:
        raise ValueError("chart envelope missing required d1/d9 keys")
    birth_jd_val = chart.get("birth_jd") or chart.get("jd")
    if not isinstance(birth_jd_val, (int, float)):
        raise ValueError("chart envelope missing 'birth_jd' (or 'jd') float")
    birth_jd = float(birth_jd_val)
    if current_md_end_jd <= current_md_start_jd:
        raise ValueError(
            "current_md_end_jd must be strictly greater than current_md_start_jd"
        )

    # Current MD's 9 ADs.
    md_total_years = (
        (current_md_end_jd - current_md_start_jd) / DAYS_PER_VEDIC_YEAR
    )
    current_ads_raw = _ad_sequence_for_md(
        md_lord=current_md_lord,
        md_total_years=md_total_years,
        md_start_jd=current_md_start_jd,
    )

    # Leftover ADs of the current MD = those ending after birth_jd
    # (i.e. the ones the consultee has yet to live through).
    current_md_ads: list[ADJudgment] = []
    for ad in current_ads_raw:
        if ad["end_jd"] <= birth_jd:
            continue
        judgment = _judge_antardasha(
            chart=chart,
            asc_sign=asc_sign,
            moon_sign=moon_sign,
            md_lord=current_md_lord,
            ad_lord=ad["ad_lord"],
            start_jd=ad["start_jd"],
            end_jd=ad["end_jd"],
            birth_jd=birth_jd,
        )
        current_md_ads.append(judgment)

    # Next MD's first 3 ADs.
    lord_names = [n for n, _ in DASHA_LORDS]
    next_idx = (lord_names.index(current_md_lord) + 1) % len(DASHA_LORDS)
    next_md_lord, next_md_years = DASHA_LORDS[next_idx]
    next_md_start = current_md_end_jd
    next_ads_raw = _ad_sequence_for_md(
        md_lord=next_md_lord,
        md_total_years=float(next_md_years),
        md_start_jd=next_md_start,
    )[:3]
    next_md_first_3_ads: list[ADJudgment] = []
    for ad in next_ads_raw:
        judgment = _judge_antardasha(
            chart=chart,
            asc_sign=asc_sign,
            moon_sign=moon_sign,
            md_lord=next_md_lord,
            ad_lord=ad["ad_lord"],
            start_jd=ad["start_jd"],
            end_jd=ad["end_jd"],
            birth_jd=birth_jd,
        )
        next_md_first_3_ads.append(judgment)

    return VimshottariADResult(
        current_md_ads=current_md_ads,
        next_md_first_3_ads=next_md_first_3_ads,
    )


__all__ = ["VimshottariADResult", "run_sequence"]
