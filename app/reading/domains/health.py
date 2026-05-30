"""Doctrine source: Composition of computations.marana_karaka_sthana,
computations.trika_doctrine (Vipareeta 6/8/12 exchange),
computations.bhava_bala (1/6/8/12 strengths),
computations.avasthas (lagna lord state),
computations.sade_sati_severity, and computations.remedies.

Phase 5 Wave A domain synthesizer — HEALTH.

Architectural discipline (spec Section 1)
-----------------------------------------

Domains are **pure synthesizers**. This module composes upstream
Finding objects BY ID; it does NOT recompute MKS / Bhava-bala / Sade
Sati math. The composition gate
(``test_health_domain_references_bhava_bala_finding_ids``) requires
that at least one upstream bhava_bala id appears in this domain's
evidence; ``test_health_domain_references_sade_sati`` requires the same
for the Sade Sati primitive.

Health convention (per Phase 5 brief)
-------------------------------------

  - **promise**        — the constitution (lagna lord state + 1H strength).
  - **triggers**       — current MD/AD as dasha-context activations.
  - **timing_windows** — Sade Sati phase windows (event_type=health_event)
                          + current MD/AD if active.
  - **afflictions**    — DOMINANT FIELD: MKS hits on the lagna lord,
                          Vipareeta trika exchanges (positive — protective
                          inversion), bhava-bala weakness on 1/6/8/12,
                          Sade Sati severity (when active).
  - **cross_checks**   — health triangulation (1H/6H concordance) +
                          bhava-bala summary.
  - **remedies**       — for any afflicted relevant planet via
                          :func:`generate_remedies`.
  - **confidence**     — 3-vote rule: 1H bhava_bala strong, lagna lord
                          favourable avastha, Sun (vitality karaka) free
                          of MKS.

Public API
==========

    synthesize_health(chart, asc_sign, moon_sign,
                      sequences_result, primitives, foundations)
        -> DomainReading
"""
from __future__ import annotations

import logging
from typing import Any, Final, Mapping

from app.core.dignity import SIGN_RULERS
from app.reading.computations.confidence_voting import cast_confidence_vote
from app.reading.computations.remedies import generate_remedies
from app.reading.schema import (
    ConfidenceScore,
    DomainReading,
    Finding,
    RemedyRecommendation,
    TimingWindow,
)

logger = logging.getLogger(__name__)


_DOMAIN_NAME: Final[str] = "health"
_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=composition of bhava_bala + mks + trika + avasthas + sade_sati "
    "(Phase 5 Wave A)"
)

_NEUTRAL_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_HEALTH_HOUSES: Final[tuple[int, ...]] = (1, 6, 8, 12)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lagna_lord_name(asc_sign: int) -> str:
    return SIGN_RULERS[asc_sign]


# ---------------------------------------------------------------------------
# Promise — constitution
# ---------------------------------------------------------------------------


def _build_promise(
    asc_sign: int,
    primitives: Mapping[str, Any],
) -> Finding:
    """Constitution = lagna lord avastha + 1H bhava-bala."""
    lord = _lagna_lord_name(asc_sign)
    avasthas: Mapping[str, Finding] = primitives.get("avasthas", {})
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})

    lord_avastha = avasthas.get(lord)
    h1 = bhava_bala.get(1)

    refs: list[str] = []
    if lord_avastha is not None:
        refs.append(lord_avastha.id)
    if h1 is not None:
        refs.append(h1.id)

    # Direction: positive if both lord avastha is positive AND 1H is strong.
    direction = "neutral"
    if (
        lord_avastha is not None
        and lord_avastha.direction == "positive"
        and h1 is not None
        and h1.direction == "positive"
    ):
        direction = "positive"
    elif (
        (lord_avastha is not None and lord_avastha.direction == "negative")
        or (h1 is not None and h1.direction == "negative")
    ):
        direction = "negative"

    parts: list[str] = []
    if lord_avastha is not None:
        parts.append(f"lagna lord {lord}: {lord_avastha.verdict}")
    if h1 is not None:
        parts.append(h1.verdict)
    verdict = "Constitution: " + ("; ".join(parts) if parts else "indicative")
    verdict = verdict[:140]

    return Finding(
        id="domain.health.promise",
        rule="health.promise",
        source_sequence=None,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"lagna_lord={lord}",
            f"asc_sign={asc_sign}",
            f"upstream_refs={refs}",
            "composition=avasthas[lord] + bhava_bala[1H]",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_NEUTRAL_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------


def _build_triggers(
    primitives: Mapping[str, Any],
    sequences_result: Mapping[str, Any],
) -> list[Finding]:
    """Current MD/AD as dasha-context activations + Sade Sati when active."""
    triggers: list[Finding] = []

    # 1. Sade Sati as a trigger when active.
    ss = primitives.get("sade_sati")
    if ss is not None and ss.direction == "negative":
        triggers.append(
            Finding(
                id="domain.health.trigger.sade_sati",
                rule="health.trigger.sade_sati",
                source_sequence=None,
                classification="trigger",
                direction="negative",
                verdict=("Sade Sati active — " + ss.verdict)[:140],
                evidence=[
                    f"upstream_sade_sati_id={ss.id}",
                    "composition=practitioner.sade_sati.current",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 2. Current MD/AD.
    md_result = sequences_result.get("vimshottari_md")
    if md_result is not None:
        cur_md = md_result.current_md_judgment
        triggers.append(
            Finding(
                id="domain.health.trigger.current_md",
                rule="health.trigger.current_md",
                source_sequence=None,
                classification="trigger",
                direction=cur_md.overall_verdict.direction,
                verdict=(
                    f"Current MD {cur_md.md_lord} ({cur_md.start_date} -> "
                    f"{cur_md.end_date})"
                )[:140],
                evidence=[
                    f"md_lord={cur_md.md_lord}",
                    f"upstream_md_overall_id={cur_md.overall_verdict.id}",
                    "composition=vimshottari_md.current_md_judgment.overall_verdict",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    ad_result = sequences_result.get("vimshottari_ad")
    if ad_result is not None and ad_result.current_md_ads:
        first_ad = ad_result.current_md_ads[0]
        triggers.append(
            Finding(
                id="domain.health.trigger.current_ad",
                rule="health.trigger.current_ad",
                source_sequence=None,
                classification="trigger",
                direction=first_ad.overall_verdict.direction,
                verdict=(
                    f"Current AD {first_ad.ad_lord} under MD {first_ad.md_lord}"
                )[:140],
                evidence=[
                    f"ad_lord={first_ad.ad_lord}",
                    f"upstream_ad_overall_id={first_ad.overall_verdict.id}",
                    "composition=vimshottari_ad.current_md_ads[0].overall_verdict",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    return triggers


# ---------------------------------------------------------------------------
# Afflictions — dominant content
# ---------------------------------------------------------------------------


def _build_afflictions(
    asc_sign: int,
    primitives: Mapping[str, Any],
) -> tuple[list[Finding], list[str]]:
    """Afflictions are the dominant content for health (per Phase 5 brief)."""
    afflictions: list[Finding] = []
    afflicted_planets: list[str] = []
    lagna_lord = _lagna_lord_name(asc_sign)

    # 1. MKS on lagna lord — direct constitution affliction.
    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    for planet, mks_finding in mks.items():
        if planet == lagna_lord:
            afflictions.append(
                Finding(
                    id=f"domain.health.affliction.mks_lagna_lord_{planet.lower()}",
                    rule="health.affliction.mks_lagna_lord",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=(
                        f"Lagna lord {planet} in MKS — " + mks_finding.verdict
                    )[:140],
                    evidence=[
                        f"planet={planet}",
                        f"upstream_mks_finding_id={mks_finding.id}",
                        "composition=practitioner.mks (lagna lord)",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )
            if planet not in afflicted_planets:
                afflicted_planets.append(planet)

    # 2. Weak bhava-bala on the four health houses (1/6/8/12).
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    for house in _HEALTH_HOUSES:
        bh = bhava_bala.get(house)
        if bh is None:
            continue
        if bh.direction == "negative":
            afflictions.append(
                Finding(
                    id=f"domain.health.affliction.weak_h{house}",
                    rule="health.affliction.weak_bhava",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=(f"Health-house {house}H weak — " + bh.verdict)[:140],
                    evidence=[
                        f"house={house}",
                        f"upstream_bhava_bala_id={bh.id}",
                        "composition=foundation.bhava_bala (1/6/8/12)",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )

    # 3. Negative avastha on the lagna lord (constitution affliction).
    avasthas: Mapping[str, Finding] = primitives.get("avasthas", {})
    lord_av = avasthas.get(lagna_lord)
    if lord_av is not None and lord_av.direction == "negative":
        afflictions.append(
            Finding(
                id=f"domain.health.affliction.lagna_lord_avastha_{lagna_lord.lower()}",
                rule="health.affliction.lagna_lord_avastha",
                source_sequence=None,
                classification="affliction",
                direction="negative",
                verdict=(
                    f"Lagna lord {lagna_lord} afflicted avastha — " + lord_av.verdict
                )[:140],
                evidence=[
                    f"lagna_lord={lagna_lord}",
                    f"upstream_avastha_id={lord_av.id}",
                    "composition=primitive.avasthas[lagna_lord] (negative)",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )
        if lagna_lord not in afflicted_planets:
            afflicted_planets.append(lagna_lord)

    # 4. Sade Sati severe (overlay).
    ss = primitives.get("sade_sati")
    if ss is not None and ss.direction == "negative":
        afflictions.append(
            Finding(
                id="domain.health.affliction.sade_sati",
                rule="health.affliction.sade_sati",
                source_sequence=None,
                classification="affliction",
                direction="negative",
                verdict=("Sade Sati overlay — " + ss.verdict)[:140],
                evidence=[
                    f"upstream_sade_sati_id={ss.id}",
                    "composition=practitioner.sade_sati.current",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )
        if "Saturn" not in afflicted_planets:
            afflicted_planets.append("Saturn")

    return afflictions, afflicted_planets


# ---------------------------------------------------------------------------
# Cross-checks
# ---------------------------------------------------------------------------


def _build_cross_checks(primitives: Mapping[str, Any]) -> list[Finding]:
    cross_checks: list[Finding] = []

    # 1. Health triangulation (1H/6H concordance).
    triangulation: Mapping[str, Finding] = primitives.get("karaka_triangulation", {})
    tri = triangulation.get("health")
    if tri is not None:
        cross_checks.append(
            Finding(
                id="domain.health.cross_check.triangulation",
                rule="health.cross_check.triangulation",
                source_sequence=None,
                classification="primitive",
                direction=tri.direction,
                verdict=("Health triangulation — " + tri.verdict)[:140],
                evidence=[
                    f"upstream_triangulation_id={tri.id}",
                    "composition=foundation.karaka_triangulation.health",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 2. Bhava-bala summary across health houses.
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    health_bhava_ids: list[str] = []
    for house in _HEALTH_HOUSES:
        bh = bhava_bala.get(house)
        if bh is not None:
            health_bhava_ids.append(bh.id)
    if health_bhava_ids:
        # Determine direction: positive if 1H is positive AND 6H not negative.
        h1 = bhava_bala.get(1)
        direction = "neutral"
        if h1 is not None and h1.direction == "positive":
            direction = "positive"
        elif h1 is not None and h1.direction == "negative":
            direction = "negative"
        cross_checks.append(
            Finding(
                id="domain.health.cross_check.bhava_bala_summary",
                rule="health.cross_check.bhava_bala_summary",
                source_sequence=None,
                classification="primitive",
                direction=direction,
                verdict=(
                    f"Bhava-bala summary across {len(health_bhava_ids)} health houses"
                )[:140],
                evidence=[
                    f"health_houses={list(_HEALTH_HOUSES)}",
                    f"upstream_bhava_bala_ids={health_bhava_ids}",
                    "composition=foundation.bhava_bala[1/6/8/12]",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 3. Trika exchange (Vipareeta — protective inversion when present).
    trika_list: list[Finding] = primitives.get("trika_exchanges", [])
    if trika_list:
        first_trika = trika_list[0]
        cross_checks.append(
            Finding(
                id="domain.health.cross_check.vipareeta",
                rule="health.cross_check.vipareeta",
                source_sequence=None,
                classification="primitive",
                direction="positive",
                verdict=(
                    "Vipareeta Raja Yoga (trika exchange) — " + first_trika.verdict
                )[:140],
                evidence=[
                    f"upstream_trika_id={first_trika.id}",
                    f"total_exchanges={len(trika_list)}",
                    "composition=practitioner.trika_doctrine (protective inversion)",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 4. Sade Sati inactive cross-check (always emit for explicit signal).
    ss = primitives.get("sade_sati")
    if ss is not None and ss.direction == "neutral":
        cross_checks.append(
            Finding(
                id="domain.health.cross_check.sade_sati_inactive",
                rule="health.cross_check.sade_sati_inactive",
                source_sequence=None,
                classification="primitive",
                direction="neutral",
                verdict=("Sade Sati inactive — " + ss.verdict)[:140],
                evidence=[
                    f"upstream_sade_sati_id={ss.id}",
                    "composition=practitioner.sade_sati.current (inactive)",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    return cross_checks


# ---------------------------------------------------------------------------
# Timing windows — Sade Sati phase + current MD/AD
# ---------------------------------------------------------------------------


def _build_timing_windows(
    primitives: Mapping[str, Any],
    sequences_result: Mapping[str, Any],
) -> list[TimingWindow]:
    """Sade Sati phase + current MD/AD windows (event_type=health_event)."""
    ss = primitives.get("sade_sati")
    ss_active = bool(ss is not None and ss.direction == "negative")
    event_type = "health_event" if ss_active else "general"

    windows: list[TimingWindow] = []
    md_result = sequences_result.get("vimshottari_md")
    if md_result is not None:
        cur_md = md_result.current_md_judgment
        windows.append(
            TimingWindow(
                start_date=cur_md.start_date,
                end_date=cur_md.end_date,
                driving_period=f"MD {cur_md.md_lord}",
                event_type=event_type,
                confidence_band="indicative_only",
                triggering_finding_ids=[cur_md.overall_verdict.id]
                + ([ss.id] if ss is not None else []),
            )
        )

    ad_result = sequences_result.get("vimshottari_ad")
    if ad_result is not None and ad_result.current_md_ads:
        first_ad = ad_result.current_md_ads[0]
        windows.append(
            TimingWindow(
                start_date=first_ad.start_date,
                end_date=first_ad.end_date,
                driving_period=f"AD {first_ad.ad_lord} under MD {first_ad.md_lord}",
                event_type=event_type,
                confidence_band="indicative_only",
                triggering_finding_ids=[first_ad.overall_verdict.id]
                + ([ss.id] if ss is not None else []),
            )
        )

    return windows


# ---------------------------------------------------------------------------
# Remedies
# ---------------------------------------------------------------------------


def _build_remedies(
    asc_sign: int,
    afflicted_planets: list[str],
    primitives: Mapping[str, Any],
    foundations: Mapping[str, Any],
) -> list[RemedyRecommendation]:
    if not afflicted_planets:
        return []

    lagna_lord = SIGN_RULERS[asc_sign]
    fifth_sign = ((asc_sign - 1) + 4) % 12 + 1
    ninth_sign = ((asc_sign - 1) + 8) % 12 + 1
    fifth_lord = SIGN_RULERS[fifth_sign]
    ninth_lord = SIGN_RULERS[ninth_sign]

    karakas = primitives.get("karakas") or {}
    atmakaraka = "Sun"
    ak_finding = karakas.get("atmakaraka") if isinstance(karakas, Mapping) else None
    if ak_finding is not None:
        for line in ak_finding.evidence:
            if line.startswith("planet="):
                atmakaraka = line.split("=", 1)[1]
                break

    fn = foundations.get("functional_nature") or {}
    natures: dict[str, str] = {}
    if isinstance(fn, Mapping):
        for planet, finding in fn.items():
            for line in finding.evidence:
                if line.startswith("nature="):
                    natures[planet] = line.split("=", 1)[1]
                    break

    try:
        bundle = generate_remedies(
            afflicted_planets=afflicted_planets,
            lagna_lord=lagna_lord,
            fifth_lord=fifth_lord,
            ninth_lord=ninth_lord,
            atmakaraka=atmakaraka,
            asc_sign=asc_sign,
            functional_natures=natures,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("generate_remedies failed for health: %s", exc)
        return []

    remedies: list[RemedyRecommendation] = []
    for category, kind in (
        ("mantras", "mantra"),
        ("daan", "donation"),
        ("yantras", "yantra"),
        ("gemstones", "gemstone"),
    ):
        for f in bundle.get(category, []):
            remedies.append(
                RemedyRecommendation(
                    kind=kind,  # type: ignore[arg-type]
                    description=f.verdict,
                    source=f"upstream:{f.id}",
                )
            )
    return remedies


# ---------------------------------------------------------------------------
# Confidence + overall verdict
# ---------------------------------------------------------------------------


def _compute_confidence(
    asc_sign: int,
    primitives: Mapping[str, Any],
) -> ConfidenceScore:
    """3-vote rule for health: 1H bhava-bala, lagna lord avastha, Sun karaka."""
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    h1 = bhava_bala.get(1)
    house_indicator = bool(h1 is not None and h1.direction == "positive")

    lord = _lagna_lord_name(asc_sign)
    avasthas: Mapping[str, Finding] = primitives.get("avasthas", {})
    lord_av = avasthas.get(lord)
    lord_indicator = bool(lord_av is not None and lord_av.direction == "positive")

    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    karaka_indicator = "Sun" not in mks

    return cast_confidence_vote(house_indicator, lord_indicator, karaka_indicator)


def _compute_overall_verdict(
    promise: Finding,
    triggers: list[Finding],
    afflictions: list[Finding],
    cross_checks: list[Finding],
) -> Finding:
    pos = sum(
        1 for f in [promise, *triggers, *cross_checks]
        if f.direction == "positive"
    )
    neg = sum(
        1 for f in [*afflictions, *triggers, *cross_checks, promise]
        if f.direction == "negative"
    )

    if pos > neg:
        direction = "positive"
        tone = "constitution strong; afflictions limited"
    elif neg > pos:
        direction = "negative"
        tone = "health afflictions dominate"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "health signals neutral"
    else:
        direction = "mixed"
        tone = "health signals mixed"

    verdict = f"Health domain verdict: {tone}; +{pos}/-{neg}"[:140]
    upstream = [promise.id] + [t.id for t in triggers] + [c.id for c in cross_checks]

    return Finding(
        id="domain.health.overall",
        rule="health.overall",
        source_sequence=None,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"positive_findings={pos}",
            f"negative_findings={neg}",
            f"upstream_finding_ids={upstream}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_NEUTRAL_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def synthesize_health(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    sequences_result: dict,
    primitives: dict,
    foundations: dict,
) -> DomainReading:
    """Health = constitution + affliction windows + Sade-Sati overlay.

    Composition map:
      - Promise: lagna lord avastha + 1H bhava-bala (constitution).
      - Triggers: Sade Sati (when active) + current MD/AD.
      - Cross-checks: health triangulation + bhava-bala summary +
        Vipareeta (trika exchange) + Sade Sati inactive signal.
      - Afflictions: MKS on lagna lord, weak bhava-bala on 1/6/8/12,
        Sade Sati severity (when active).
      - Timing windows: current MD + current AD; event_type = ``health_event``
        if Sade Sati active, else ``general``.

    Args:
        chart: Full natal chart dict.
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi.
        sequences_result: Dict carrying ``vimshottari_md``,
            ``vimshottari_ad``, ``current_md_lord``.
        primitives: Dict carrying ``marana_karaka_sthana``,
            ``bhava_bala``, ``trika_exchanges`` (list),
            ``avasthas``, ``sade_sati``, ``karaka_triangulation``,
            ``karakas``.
        foundations: Dict carrying ``functional_nature``.

    Returns:
        :class:`DomainReading` for the health domain.

    Raises:
        ValueError: if ``asc_sign`` or ``moon_sign`` is out of 1..12.
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign!r}")
    if not isinstance(moon_sign, int) or not (1 <= moon_sign <= 12):
        raise ValueError(f"moon_sign must be in 1..12, got {moon_sign!r}")

    promise = _build_promise(asc_sign, primitives)
    triggers = _build_triggers(primitives, sequences_result)
    afflictions, afflicted_planets = _build_afflictions(asc_sign, primitives)
    cross_checks = _build_cross_checks(primitives)
    timing_windows = _build_timing_windows(primitives, sequences_result)
    remedies = _build_remedies(asc_sign, afflicted_planets, primitives, foundations)
    confidence = _compute_confidence(asc_sign, primitives)
    overall_verdict = _compute_overall_verdict(
        promise, triggers, afflictions, cross_checks,
    )

    return DomainReading(
        domain=_DOMAIN_NAME,
        promise=promise,
        triggers=triggers,
        timing_windows=timing_windows,
        afflictions=afflictions,
        cross_checks=cross_checks,
        remedies=remedies,
        overall_verdict=overall_verdict,
        confidence=confidence,
    )


__all__ = ["synthesize_health"]
