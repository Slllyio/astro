"""Doctrine source: Composition of divisional_readings.d9_navamsha,
computations.marriage_trigger (UL+7L+D9+transit), computations.arudha_upapada
(UL/UL_2), computations.karaka_triangulation (marriage), and
sequences.vimshottari_md/ad. Plus computations.remedies for marriage-aligned
karaka remediation.

Phase 5 Wave A domain synthesizer — MARRIAGE.

Architectural discipline (spec Section 1)
-----------------------------------------

Domains are **pure synthesizers**. This module composes upstream
Finding objects BY ID; it does not redo D9 / whole-sign math. The
marriage_trigger primitive (already a compound finding) MUST appear
in ``triggers``; the upstream UL pada Finding MUST be referenced from
``promise`` or ``cross_checks`` to clear the architectural-purity gate
(``test_marriage_domain_references_d9_finding_ids`` +
``test_marriage_domain_references_upapada``).

Timing windows derive from the current/next AD periods × the trigger
active flag, classified as ``"marriage"`` per the schema's
``TimingWindow.event_type`` literal.

Public API
==========

    synthesize_marriage(chart, asc_sign, moon_sign,
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


_DOMAIN_NAME: Final[str] = "marriage"
_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=composition of D9 + marriage_trigger + arudha_upapada + "
    "karaka_triangulation + vimshottari (Phase 5 Wave A)"
)

# Marriage-relevant karaka planets.
_MARRIAGE_PLANETS: Final[frozenset[str]] = frozenset(
    {"Venus", "Jupiter"}
)

_NEUTRAL_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seventh_house_sign(asc_sign: int) -> int:
    return ((asc_sign - 1) + 6) % 12 + 1


def _ul_finding(primitives: Mapping[str, Any]) -> Finding | None:
    padas = primitives.get("arudha_padas")
    if isinstance(padas, Mapping):
        return padas.get("ul")
    return None


# ---------------------------------------------------------------------------
# Promise
# ---------------------------------------------------------------------------


def _build_promise(
    asc_sign: int,
    primitives: Mapping[str, Any],
) -> Finding:
    """Marriage promise — D9 7L + UL + Venus/Jupiter as karaka indicators."""
    d9_findings: Mapping[str, Finding] = primitives.get("d9_findings", {})
    seventh_lord_finding = d9_findings.get("d9.seventh_house_lord")
    venus_d9 = d9_findings.get("d9.planet_in_venus")
    jupiter_d9 = d9_findings.get("d9.planet_in_jupiter")
    ul = _ul_finding(primitives)

    refs: list[str] = []
    if seventh_lord_finding is not None:
        refs.append(seventh_lord_finding.id)
    if venus_d9 is not None:
        refs.append(venus_d9.id)
    if jupiter_d9 is not None:
        refs.append(jupiter_d9.id)
    if ul is not None:
        refs.append(ul.id)

    # Direction: positive if D9 7L direction == positive, else neutral.
    direction = "neutral"
    if seventh_lord_finding is not None and seventh_lord_finding.direction == "positive":
        direction = "positive"

    parts: list[str] = []
    if seventh_lord_finding is not None:
        parts.append(seventh_lord_finding.verdict)
    if ul is not None:
        parts.append(ul.verdict)
    verdict = "Marriage promise: " + ("; ".join(parts) if parts else "indicative")
    verdict = verdict[:140]

    return Finding(
        id="domain.marriage.promise",
        rule="marriage.promise",
        source_sequence=None,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"upstream_refs={refs}",
            f"asc_sign={asc_sign}",
            f"seventh_house_sign={_seventh_house_sign(asc_sign)}",
            "composition=d9.seventh_house_lord + arudha_upapada.ul + d9.planet_in_venus/jupiter",
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
    """The marriage_trigger primitive + current MD/AD as marriage triggers."""
    triggers: list[Finding] = []

    # 1. Compound marriage trigger primitive (UL+7L+D9+transit).
    trig = primitives.get("marriage_trigger")
    if trig is not None:
        triggers.append(
            Finding(
                id="domain.marriage.trigger.compound",
                rule="marriage.trigger.compound",
                source_sequence=None,
                classification="trigger",
                direction=trig.direction,
                verdict=("Marriage compound trigger — " + trig.verdict)[:140],
                evidence=[
                    f"upstream_trigger_id={trig.id}",
                    f"compound_direction={trig.direction}",
                    "composition=practitioner.marriage_trigger.compound",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 2. Current MD as a marriage-context trigger.
    md_result = sequences_result.get("vimshottari_md")
    if md_result is not None:
        cur_md = md_result.current_md_judgment
        triggers.append(
            Finding(
                id="domain.marriage.trigger.current_md",
                rule="marriage.trigger.current_md",
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

    # 3. First AD of current MD.
    ad_result = sequences_result.get("vimshottari_ad")
    if ad_result is not None and ad_result.current_md_ads:
        first_ad = ad_result.current_md_ads[0]
        triggers.append(
            Finding(
                id="domain.marriage.trigger.current_ad",
                rule="marriage.trigger.current_ad",
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
# Cross-checks
# ---------------------------------------------------------------------------


def _build_cross_checks(primitives: Mapping[str, Any]) -> list[Finding]:
    cross_checks: list[Finding] = []

    # 1. D9 lagna anchor (the dharma frame).
    d9_findings: Mapping[str, Finding] = primitives.get("d9_findings", {})
    d9_lagna = d9_findings.get("d9.lagna")
    if d9_lagna is not None:
        cross_checks.append(
            Finding(
                id="domain.marriage.cross_check.d9_lagna",
                rule="marriage.cross_check.d9_lagna",
                source_sequence=None,
                classification="primitive",
                direction=d9_lagna.direction,
                verdict=("D9 dharma anchor — " + d9_lagna.verdict)[:140],
                evidence=[
                    f"upstream_d9_id={d9_lagna.id}",
                    "composition=d9.lagna",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 2. Upapada Lagna — spouse description anchor.
    ul = _ul_finding(primitives)
    if ul is not None:
        cross_checks.append(
            Finding(
                id="domain.marriage.cross_check.upapada",
                rule="marriage.cross_check.upapada",
                source_sequence=None,
                classification="primitive",
                direction="neutral",
                verdict=("Upapada Lagna — " + ul.verdict)[:140],
                evidence=[
                    f"upstream_ul_id={ul.id}",
                    "composition=arudha_upapada.ul (spouse-description anchor)",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 3. Karaka triangulation (marriage row).
    triangulation: Mapping[str, Finding] = primitives.get("karaka_triangulation", {})
    tri = triangulation.get("marriage")
    if tri is not None:
        cross_checks.append(
            Finding(
                id="domain.marriage.cross_check.triangulation",
                rule="marriage.cross_check.triangulation",
                source_sequence=None,
                classification="primitive",
                direction=tri.direction,
                verdict=("Karaka triangulation — " + tri.verdict)[:140],
                evidence=[
                    f"upstream_triangulation_id={tri.id}",
                    "composition=foundation.karaka_triangulation.marriage",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    return cross_checks


# ---------------------------------------------------------------------------
# Afflictions
# ---------------------------------------------------------------------------


def _build_afflictions(
    primitives: Mapping[str, Any],
) -> tuple[list[Finding], list[str]]:
    """Afflictions on marriage-relevant planets (Venus, Jupiter) — MKS hits."""
    afflictions: list[Finding] = []
    afflicted_planets: list[str] = []

    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    for planet, mks_finding in mks.items():
        if planet in _MARRIAGE_PLANETS:
            afflictions.append(
                Finding(
                    id=f"domain.marriage.affliction.mks_{planet.lower()}",
                    rule="marriage.affliction.mks",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=(
                        f"Marriage MKS: {planet} — {mks_finding.verdict}"
                    )[:140],
                    evidence=[
                        f"planet={planet}",
                        f"upstream_mks_finding_id={mks_finding.id}",
                        "composition=practitioner.mks (marriage karaka)",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )
            if planet not in afflicted_planets:
                afflicted_planets.append(planet)

    return afflictions, afflicted_planets


# ---------------------------------------------------------------------------
# Timing windows
# ---------------------------------------------------------------------------


def _build_timing_windows(
    primitives: Mapping[str, Any],
    sequences_result: Mapping[str, Any],
) -> list[TimingWindow]:
    """Timing windows: current/next AD windows, classified ``marriage``.

    Per spec, when the compound trigger is active the windows are
    marked as marriage event_type; otherwise as ``general`` so consumers
    still see the candidate window.
    """
    trigger = primitives.get("marriage_trigger")
    trigger_active = bool(trigger is not None and trigger.direction == "positive")
    event_type = "marriage" if trigger_active else "general"

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
                + ([trigger.id] if trigger is not None else []),
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
                + ([trigger.id] if trigger is not None else []),
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
        logger.debug("generate_remedies failed for marriage: %s", exc)
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
    asc_sign: int,
) -> ConfidenceScore:
    """3-vote rule for marriage: 7H D9 indicators, 7L favourable, Venus karaka.

    - house: D9 7L finding direction positive (proxy for 7H favour).
    - lord:  D9 lagna lord finding direction positive.
    - karaka: Venus NOT in MKS.
    """
    d9_findings: Mapping[str, Finding] = primitives.get("d9_findings", {})
    seventh_lord = d9_findings.get("d9.seventh_house_lord")
    house_indicator = bool(seventh_lord is not None and seventh_lord.direction == "positive")

    lagna_lord = d9_findings.get("d9.lagna_lord")
    lord_indicator = bool(lagna_lord is not None and lagna_lord.direction == "positive")

    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    karaka_indicator = "Venus" not in mks

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
        tone = "marriage promise supported by trigger + D9"
    elif neg > pos:
        direction = "negative"
        tone = "marriage impediments dominate"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "marriage signals neutral"
    else:
        direction = "mixed"
        tone = "marriage signals mixed"

    verdict = f"Marriage domain verdict: {tone}; +{pos}/-{neg}"[:140]
    upstream = [promise.id] + [t.id for t in triggers] + [c.id for c in cross_checks]

    return Finding(
        id="domain.marriage.overall",
        rule="marriage.overall",
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


def synthesize_marriage(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    sequences_result: dict,
    primitives: dict,
    foundations: dict,
) -> DomainReading:
    """Marriage promise + timing trigger windows + spouse description.

    Composition map:
      - Promise: D9 7L + UL + Venus/Jupiter in D9.
      - Triggers: marriage_trigger primitive (compound), current MD, first AD.
      - Cross-checks: D9 lagna, UL, karaka triangulation (marriage).
      - Afflictions: MKS hits on Venus/Jupiter.
      - Timing windows: current MD + current AD; event_type = ``marriage``
        if trigger active, else ``general``.

    Args:
        chart: Full natal chart dict.
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi.
        sequences_result: Dict carrying ``vimshottari_md``,
            ``vimshottari_ad``, ``current_md_lord``.
        primitives: Dict carrying ``arudha_padas``, ``karakas``,
            ``karaka_triangulation``, ``d9_findings``,
            ``marriage_trigger``, ``marana_karaka_sthana`` (optional).
        foundations: Dict carrying ``functional_nature``.

    Returns:
        :class:`DomainReading` for the marriage domain.

    Raises:
        ValueError: if ``asc_sign`` or ``moon_sign`` is out of 1..12.
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign!r}")
    if not isinstance(moon_sign, int) or not (1 <= moon_sign <= 12):
        raise ValueError(f"moon_sign must be in 1..12, got {moon_sign!r}")

    promise = _build_promise(asc_sign, primitives)
    triggers = _build_triggers(primitives, sequences_result)
    cross_checks = _build_cross_checks(primitives)
    afflictions, afflicted_planets = _build_afflictions(primitives)
    timing_windows = _build_timing_windows(primitives, sequences_result)
    remedies = _build_remedies(asc_sign, afflicted_planets, primitives, foundations)
    confidence = _compute_confidence(primitives, asc_sign)
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


__all__ = ["synthesize_marriage"]
