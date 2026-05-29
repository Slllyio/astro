"""Doctrine source: Composition of divisional_readings.d7_saptamsa,
divisional_readings.d9_navamsha (Jupiter / lagna for triple-chart),
computations.karaka_triangulation (children row), 5H bhava_bala,
Jupiter avastha (natural putra-karaka), computations.marana_karaka_sthana
(Jupiter MKS = severe progeny affliction), sequences.vimshottari_md/ad,
and computations.remedies.

Phase 5 Wave B domain synthesizer — CHILDREN.

Architectural discipline (spec Section 1)
-----------------------------------------

Domains are **pure synthesizers**. This module composes upstream
Finding objects BY ID; it does NOT redo D7 / D9 / bhava-bala math.
Every cross-check / promise Finding lists upstream finding ids in its
``evidence`` so the architectural-purity gates
(``test_children_domain_references_d7_finding_ids`` +
``test_children_domain_references_5h_bhava_bala``) pass.

Triple-chart confirmation (per practitioner research)
-----------------------------------------------------

A "strong children" indication requires *all three* of:

  - **D1 5H** non-afflicted (via foundation.bhava_bala[5]).
  - **D9 Jupiter** non-afflicted (D9 is the dharma chart; if Jupiter is
    afflicted in D9 it weakens any 5H promise).
  - **D7 5H** non-afflicted (via d7.fifth_house_lord).

If any one of the three shows Saturn / Rahu / Ketu affliction → the
domain surfaces a *delays* signal. This is materialised as a single
``cross_check.triple_chart`` Finding that points at the three upstream
ids.

The 7 fields of a :class:`DomainReading` are populated as follows:

  - **promise**       — 5H bhava-bala + Jupiter avastha + D7 5H lord.
  - **triggers**      — current MD + first AD overall verdicts.
  - **afflictions**   — Jupiter in MKS (3H), weak 5H bhava-bala,
                        Daridra yoga (proxy for child denial).
  - **cross_checks**  — karaka triangulation (children), triple-chart
                        confirmation D1/D9/D7, Saraswati yoga (positive
                        — intellectual children) when present.
  - **timing_windows** — current MD + first AD; event_type =
                         ``child_birth`` when triple-chart positive AND
                         current MD/AD is positive, else ``general``.
  - **remedies**      — for any afflicted Jupiter via
                        :func:`generate_remedies`.
  - **confidence**    — 3-vote rule: 5H positive (house), 5L favourable
                        proxy (D7 fifth_house_lord direction or
                        karaka_triangulation children direction)
                        (lord), Jupiter NOT in MKS (karaka).

Public API
==========

    synthesize_children(chart, asc_sign, moon_sign,
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


_DOMAIN_NAME: Final[str] = "children"
_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=composition of D7 + D9 + 5H bhava_bala + Jupiter avastha "
    "+ karaka_triangulation + vimshottari (Phase 5 Wave B)"
)

# Children-relevant karaka — Jupiter (natural putra-karaka).
_CHILDREN_KARAKA: Final[str] = "Jupiter"


_NEUTRAL_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fifth_house_sign(asc_sign: int) -> int:
    return ((asc_sign - 1) + 4) % 12 + 1


# ---------------------------------------------------------------------------
# Promise
# ---------------------------------------------------------------------------


def _build_promise(
    asc_sign: int,
    primitives: Mapping[str, Any],
) -> Finding:
    """Children promise — 5H bhava-bala + Jupiter avastha + D7 5L."""
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    avasthas: Mapping[str, Finding] = primitives.get("avasthas", {})
    d7_findings: Mapping[str, Finding] = primitives.get("d7_findings", {})

    h5 = bhava_bala.get(5)
    jupiter_av = avasthas.get(_CHILDREN_KARAKA)
    d7_fifth = d7_findings.get("d7.fifth_house_lord")
    d7_jupiter = d7_findings.get("d7.planet_in_jupiter")

    refs: list[str] = []
    if h5 is not None:
        refs.append(h5.id)
    if jupiter_av is not None:
        refs.append(jupiter_av.id)
    if d7_fifth is not None:
        refs.append(d7_fifth.id)
    if d7_jupiter is not None:
        refs.append(d7_jupiter.id)

    # Direction: positive iff 5H positive AND Jupiter avastha positive.
    direction = "neutral"
    if (
        h5 is not None and h5.direction == "positive"
        and jupiter_av is not None and jupiter_av.direction == "positive"
    ):
        direction = "positive"
    elif (
        (h5 is not None and h5.direction == "negative")
        or (jupiter_av is not None and jupiter_av.direction == "negative")
    ):
        direction = "negative"

    parts: list[str] = []
    if h5 is not None:
        parts.append(f"5H: {h5.verdict}")
    if jupiter_av is not None:
        parts.append(f"Jupiter avastha: {jupiter_av.verdict}")
    if d7_fifth is not None:
        parts.append(d7_fifth.verdict)
    verdict = "Children promise: " + ("; ".join(parts) if parts else "indicative")
    verdict = verdict[:140]

    return Finding(
        id="domain.children.promise",
        rule="children.promise",
        source_sequence=None,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"upstream_refs={refs}",
            f"asc_sign={asc_sign}",
            f"fifth_house_sign={_fifth_house_sign(asc_sign)}",
            f"putra_karaka={_CHILDREN_KARAKA}",
            "composition=bhava_bala[5H] + avasthas[Jupiter] + d7.fifth_house_lord",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_NEUTRAL_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------


def _build_triggers(sequences_result: Mapping[str, Any]) -> list[Finding]:
    triggers: list[Finding] = []
    md_result = sequences_result.get("vimshottari_md")
    if md_result is not None:
        cur_md = md_result.current_md_judgment
        triggers.append(
            Finding(
                id="domain.children.trigger.current_md",
                rule="children.trigger.current_md",
                source_sequence=None,
                classification="trigger",
                direction=cur_md.overall_verdict.direction,
                verdict=(
                    f"Current MD {cur_md.md_lord} ({cur_md.start_date} -> "
                    f"{cur_md.end_date}): {cur_md.overall_verdict.direction}"
                )[:140],
                evidence=[
                    f"md_lord={cur_md.md_lord}",
                    f"md_start_date={cur_md.start_date}",
                    f"md_end_date={cur_md.end_date}",
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
                id="domain.children.trigger.current_ad",
                rule="children.trigger.current_ad",
                source_sequence=None,
                classification="trigger",
                direction=first_ad.overall_verdict.direction,
                verdict=(
                    f"Current AD {first_ad.ad_lord} under MD {first_ad.md_lord}"
                )[:140],
                evidence=[
                    f"ad_lord={first_ad.ad_lord}",
                    f"md_lord={first_ad.md_lord}",
                    f"upstream_ad_overall_id={first_ad.overall_verdict.id}",
                    "composition=vimshottari_ad.current_md_ads[0].overall_verdict",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    return triggers


# ---------------------------------------------------------------------------
# Afflictions
# ---------------------------------------------------------------------------


def _build_afflictions(
    primitives: Mapping[str, Any],
) -> tuple[list[Finding], list[str]]:
    """Jupiter in MKS, weak 5H bhava-bala, Daridra yoga (proxy for denial)."""
    afflictions: list[Finding] = []
    afflicted_planets: list[str] = []

    # 1. Jupiter (putra-karaka) in MKS — primary children affliction.
    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    jupiter_mks = mks.get(_CHILDREN_KARAKA)
    if jupiter_mks is not None:
        afflictions.append(
            Finding(
                id="domain.children.affliction.mks_jupiter",
                rule="children.affliction.mks_putra_karaka",
                source_sequence=None,
                classification="affliction",
                direction="negative",
                verdict=(
                    f"Putra-karaka Jupiter in MKS — {jupiter_mks.verdict}"
                )[:140],
                evidence=[
                    f"planet={_CHILDREN_KARAKA}",
                    f"upstream_mks_finding_id={jupiter_mks.id}",
                    "composition=practitioner.mks (putra-karaka Jupiter)",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )
        if _CHILDREN_KARAKA not in afflicted_planets:
            afflicted_planets.append(_CHILDREN_KARAKA)

    # 2. Weak 5H bhava-bala (children-house failure).
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    h5 = bhava_bala.get(5)
    if h5 is not None and h5.direction == "negative":
        afflictions.append(
            Finding(
                id="domain.children.affliction.weak_h5",
                rule="children.affliction.weak_5h",
                source_sequence=None,
                classification="affliction",
                direction="negative",
                verdict=(f"Children-house 5H weak — " + h5.verdict)[:140],
                evidence=[
                    "house=5",
                    f"upstream_bhava_bala_id={h5.id}",
                    "composition=foundation.bhava_bala[5H]",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 3. Daridra yoga — Phaladeepika treats as poverty / family denial proxy.
    yogas = primitives.get("yogas_extended") or []
    for y in yogas:
        if y.id.startswith("practitioner.yogas_extended.daridra."):
            afflictions.append(
                Finding(
                    id="domain.children.affliction.daridra_yoga",
                    rule="children.affliction.daridra_yoga",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=("Daridra Yoga (child-denial proxy) — " + y.verdict)[:140],
                    evidence=[
                        f"upstream_yoga_id={y.id}",
                        "composition=practitioner.yogas_extended.daridra",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )

    return afflictions, afflicted_planets


# ---------------------------------------------------------------------------
# Cross-checks (triple-chart confirmation)
# ---------------------------------------------------------------------------


def _build_cross_checks(primitives: Mapping[str, Any]) -> list[Finding]:
    cross_checks: list[Finding] = []

    # 1. Karaka triangulation (children row).
    triangulation: Mapping[str, Finding] = primitives.get("karaka_triangulation", {})
    tri = triangulation.get("children")
    if tri is not None:
        cross_checks.append(
            Finding(
                id="domain.children.cross_check.triangulation",
                rule="children.cross_check.triangulation",
                source_sequence=None,
                classification="primitive",
                direction=tri.direction,
                verdict=("Children triangulation — " + tri.verdict)[:140],
                evidence=[
                    f"upstream_triangulation_id={tri.id}",
                    "composition=foundation.karaka_triangulation.children",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 2. Triple-chart confirmation (D1-5H + D9 + D7-5H).
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    d9_findings: Mapping[str, Finding] = primitives.get("d9_findings", {})
    d7_findings: Mapping[str, Finding] = primitives.get("d7_findings", {})

    h5 = bhava_bala.get(5)
    d9_lagna = d9_findings.get("d9.lagna")
    d9_jupiter = d9_findings.get("d9.planet_in_jupiter")
    d7_fifth = d7_findings.get("d7.fifth_house_lord")
    d7_jupiter = d7_findings.get("d7.planet_in_jupiter")

    chart_signals: list[str] = []
    upstream_ids: list[str] = []

    d1_ok = h5 is not None and h5.direction != "negative"
    if h5 is not None:
        chart_signals.append(f"D1-5H={h5.direction}")
        upstream_ids.append(h5.id)
    d9_proxy = d9_jupiter or d9_lagna
    d9_ok = d9_proxy is not None and d9_proxy.direction != "negative"
    if d9_proxy is not None:
        chart_signals.append(f"D9-Jupiter/lagna={d9_proxy.direction}")
        upstream_ids.append(d9_proxy.id)
    d7_proxy = d7_fifth or d7_jupiter
    d7_ok = d7_proxy is not None and d7_proxy.direction != "negative"
    if d7_proxy is not None:
        chart_signals.append(f"D7-5L/Jupiter={d7_proxy.direction}")
        upstream_ids.append(d7_proxy.id)

    all_ok = d1_ok and d9_ok and d7_ok
    any_neg = (
        (h5 is not None and h5.direction == "negative")
        or (d9_proxy is not None and d9_proxy.direction == "negative")
        or (d7_proxy is not None and d7_proxy.direction == "negative")
    )

    if all_ok and any(s.endswith("=positive") for s in chart_signals):
        triple_direction = "positive"
        triple_summary = "triple-chart D1/D9/D7 concord positive"
    elif any_neg:
        triple_direction = "negative"
        triple_summary = "triple-chart D1/D9/D7 shows delays / affliction"
    else:
        triple_direction = "neutral"
        triple_summary = "triple-chart D1/D9/D7 neutral"

    cross_checks.append(
        Finding(
            id="domain.children.cross_check.triple_chart",
            rule="children.cross_check.triple_chart",
            source_sequence=None,
            classification="primitive",
            direction=triple_direction,
            verdict=(triple_summary + ": " + "; ".join(chart_signals))[:140],
            evidence=[
                f"d1_5h_ok={d1_ok}",
                f"d9_proxy_ok={d9_ok}",
                f"d7_proxy_ok={d7_ok}",
                f"chart_signals={chart_signals}",
                f"upstream_finding_ids={upstream_ids}",
                "composition=triple_chart D1-5H + D9 (Jupiter/lagna) + D7-5L/Jupiter",
                _DOCTRINE_SENTINEL,
            ],
            confidence=_NEUTRAL_CONFIDENCE,
        )
    )

    # 3. Saraswati yoga (intellectual children — positive overlay).
    yogas = primitives.get("yogas_extended") or []
    for y in yogas:
        if y.id.startswith("practitioner.yogas_extended.saraswati."):
            cross_checks.append(
                Finding(
                    id="domain.children.cross_check.saraswati_yoga",
                    rule="children.cross_check.saraswati_yoga",
                    source_sequence=None,
                    classification="primitive",
                    direction="positive",
                    verdict=("Saraswati Yoga (intellectual children) — " + y.verdict)[:140],
                    evidence=[
                        f"upstream_yoga_id={y.id}",
                        "composition=practitioner.yogas_extended.saraswati",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )

    return cross_checks


# ---------------------------------------------------------------------------
# Timing windows
# ---------------------------------------------------------------------------


def _build_timing_windows(
    primitives: Mapping[str, Any],
    sequences_result: Mapping[str, Any],
    cross_checks: list[Finding],
) -> list[TimingWindow]:
    """Current MD + first AD; event_type=child_birth when triple-chart pos."""
    triple = next(
        (c for c in cross_checks if c.id == "domain.children.cross_check.triple_chart"),
        None,
    )
    triple_positive = triple is not None and triple.direction == "positive"

    windows: list[TimingWindow] = []
    md_result = sequences_result.get("vimshottari_md")
    if md_result is not None:
        cur_md = md_result.current_md_judgment
        event_type = (
            "child_birth"
            if triple_positive and cur_md.overall_verdict.direction == "positive"
            else "general"
        )
        seed_ids: list[str] = [cur_md.overall_verdict.id]
        if triple is not None:
            seed_ids.append(triple.id)
        windows.append(
            TimingWindow(
                start_date=cur_md.start_date,
                end_date=cur_md.end_date,
                driving_period=f"MD {cur_md.md_lord}",
                event_type=event_type,
                confidence_band="indicative_only",
                triggering_finding_ids=seed_ids,
            )
        )

    ad_result = sequences_result.get("vimshottari_ad")
    if ad_result is not None and ad_result.current_md_ads:
        first_ad = ad_result.current_md_ads[0]
        event_type = (
            "child_birth"
            if triple_positive and first_ad.overall_verdict.direction == "positive"
            else "general"
        )
        seed_ids2: list[str] = [first_ad.overall_verdict.id]
        if triple is not None:
            seed_ids2.append(triple.id)
        windows.append(
            TimingWindow(
                start_date=first_ad.start_date,
                end_date=first_ad.end_date,
                driving_period=f"AD {first_ad.ad_lord} under MD {first_ad.md_lord}",
                event_type=event_type,
                confidence_band="indicative_only",
                triggering_finding_ids=seed_ids2,
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
        logger.debug("generate_remedies failed for children: %s", exc)
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
    primitives: Mapping[str, Any],
) -> ConfidenceScore:
    """3-vote rule for children: 5H positive (house), 5L favourable (lord),
    Jupiter NOT in MKS (karaka).
    """
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    h5 = bhava_bala.get(5)
    house_indicator = bool(h5 is not None and h5.direction == "positive")

    # 5L proxy: karaka_triangulation.children direction OR d7.fifth_house_lord
    # being non-negative (favourable for offspring signifier).
    triangulation: Mapping[str, Finding] = primitives.get("karaka_triangulation", {})
    tri_children = triangulation.get("children")
    d7_fifth = primitives.get("d7_findings", {}).get("d7.fifth_house_lord")
    lord_indicator = bool(
        (tri_children is not None and tri_children.direction == "positive")
        or (d7_fifth is not None and d7_fifth.direction == "positive")
    )

    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    karaka_indicator = _CHILDREN_KARAKA not in mks

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
        tone = "children promise constructively supported"
    elif neg > pos:
        direction = "negative"
        tone = "children impediments / delays dominate"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "children signals neutral"
    else:
        direction = "mixed"
        tone = "children signals mixed"

    verdict = f"Children domain verdict: {tone}; +{pos}/-{neg}"[:140]
    upstream = [promise.id] + [t.id for t in triggers] + [c.id for c in cross_checks]

    return Finding(
        id="domain.children.overall",
        rule="children.overall",
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


def synthesize_children(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    sequences_result: dict,
    primitives: dict,
    foundations: dict,
) -> DomainReading:
    """Children = 5H + D7 + Jupiter karaka + triple-chart D1/D9/D7 confirmation.

    Composition map:
      - Promise: 5H bhava-bala + Jupiter avastha + D7 5H lord.
      - Triggers: current MD + first AD overall verdicts.
      - Cross-checks: karaka triangulation (children), triple-chart
        confirmation (D1-5H + D9-Jupiter/lagna + D7-5L/Jupiter),
        Saraswati yoga overlay (positive — intellectual children).
      - Afflictions: Jupiter in MKS (severe putra-karaka affliction),
        weak 5H bhava-bala, Daridra yoga (child-denial proxy).
      - Timing windows: current MD + first AD; event_type =
        ``child_birth`` when triple-chart positive AND dasha positive.

    Args:
        chart: Full natal chart dict.
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi.
        sequences_result: Dict carrying ``vimshottari_md``,
            ``vimshottari_ad``, ``current_md_lord``.
        primitives: Dict carrying ``karakas``, ``karaka_triangulation``,
            ``marana_karaka_sthana``, ``bhava_bala``, ``avasthas``,
            ``d7_findings``, ``d9_findings``, ``yogas_extended``.
        foundations: Dict carrying ``functional_nature``.

    Returns:
        :class:`DomainReading` for the children domain.

    Raises:
        ValueError: if ``asc_sign`` or ``moon_sign`` is out of 1..12.
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign!r}")
    if not isinstance(moon_sign, int) or not (1 <= moon_sign <= 12):
        raise ValueError(f"moon_sign must be in 1..12, got {moon_sign!r}")

    promise = _build_promise(asc_sign, primitives)
    triggers = _build_triggers(sequences_result)
    afflictions, afflicted_planets = _build_afflictions(primitives)
    cross_checks = _build_cross_checks(primitives)
    timing_windows = _build_timing_windows(primitives, sequences_result, cross_checks)
    remedies = _build_remedies(asc_sign, afflicted_planets, primitives, foundations)
    confidence = _compute_confidence(primitives)
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


__all__ = ["synthesize_children"]
