"""Doctrine source: Composition of divisional_readings.d2_hora,
computations.yogas_extended (Lakshmi, Saraswati, Daridra, Chamara,
Adhi), computations.karaka_triangulation (wealth row), 2H+11H
bhava_bala (two-engine retention/inflow model), Jupiter/Venus avastha,
sequences.vimshottari_md/ad, and computations.remedies.

Phase 5 Wave B domain synthesizer — WEALTH.

Architectural discipline (spec Section 1)
-----------------------------------------

Domains are **pure synthesizers**. This module composes upstream
Finding objects BY ID; it does NOT redo D2 / yoga / bhava-bala math.
Every cross-check / promise Finding lists the upstream finding ids it
draws on in its ``evidence`` field so the architectural-purity gate
(``test_wealth_domain_references_d2_finding_ids`` +
``test_wealth_domain_references_bhava_bala_2h_or_11h``) passes.

Two-engine retention/inflow model (per practitioner research)
-------------------------------------------------------------

- **2H = retention** (assets, savings, accumulated wealth).
- **11H = inflow** (income streams, gains).
- Strong 11H + weak 2H pattern surfaces the "high earner / no savings"
  signal in the cross_checks.

The 7 fields of a :class:`DomainReading` are populated as follows:

  - **promise**       — D2 lagna-lord Hora + 2H/11H bhava-bala stance.
  - **triggers**      — current MD + first AD overall verdicts.
  - **afflictions**   — MKS on Jupiter/Venus (dhana karakas), Daridra
                        yoga (if present), weak 2H/11H bhava-bala.
  - **cross_checks**  — karaka triangulation (wealth), retention vs
                        inflow stance, Lakshmi/Saraswati/Chamara/Adhi
                        positive yogas.
  - **timing_windows** — current MD + first AD; event_type =
                         ``wealth_event`` when a positive dhana yoga is
                         present, else ``general``.
  - **remedies**      — for any afflicted Jupiter/Venus via
                        :func:`generate_remedies`.
  - **confidence**    — 3-vote rule: 2H/11H bhava-bala (house), 2L/11L
                        favourable placement (lord), Jupiter NOT in MKS
                        (karaka).

Public API
==========

    synthesize_wealth(chart, asc_sign, moon_sign,
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


_DOMAIN_NAME: Final[str] = "wealth"
_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=composition of D2 hora + dhana yogas + 2H/11H bhava_bala + "
    "Jupiter/Venus avasthas + vimshottari (Phase 5 Wave B)"
)

# Wealth-relevant karaka planets (dhana karakas).
_WEALTH_PLANETS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus"})

# Positive dhana yoga slug prefixes (per yogas_extended ids).
_POSITIVE_DHANA_YOGA_PREFIXES: Final[tuple[str, ...]] = (
    "practitioner.yogas_extended.lakshmi.",
    "practitioner.yogas_extended.saraswati.",
    "practitioner.yogas_extended.chamara.",
    "practitioner.yogas_extended.adhi.",
)

_DARIDRA_YOGA_PREFIX: Final[str] = "practitioner.yogas_extended.daridra."


_NEUTRAL_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _second_house_sign(asc_sign: int) -> int:
    return ((asc_sign - 1) + 1) % 12 + 1


def _eleventh_house_sign(asc_sign: int) -> int:
    return ((asc_sign - 1) + 10) % 12 + 1


def _collect_yogas_by_prefix(
    primitives: Mapping[str, Any], prefixes: tuple[str, ...],
) -> list[Finding]:
    yogas = primitives.get("yogas_extended") or []
    out: list[Finding] = []
    for y in yogas:
        if any(y.id.startswith(p) for p in prefixes):
            out.append(y)
    return out


# ---------------------------------------------------------------------------
# Promise
# ---------------------------------------------------------------------------


def _build_promise(
    asc_sign: int,
    primitives: Mapping[str, Any],
) -> Finding:
    """Wealth promise — D2 lagna-lord Hora + 2H + 11H bhava-bala stance."""
    d2_findings: Mapping[str, Finding] = primitives.get("d2_findings", {})
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})

    ll_hora = d2_findings.get("d2.lagna_lord_in_hora")
    h2 = bhava_bala.get(2)
    h11 = bhava_bala.get(11)

    refs: list[str] = []
    if ll_hora is not None:
        refs.append(ll_hora.id)
    if h2 is not None:
        refs.append(h2.id)
    if h11 is not None:
        refs.append(h11.id)

    # Direction: positive if either 2H or 11H is positive AND neither is
    # negative; negative if either is negative AND neither is positive.
    pos_count = sum(
        1 for h in (h2, h11) if h is not None and h.direction == "positive"
    )
    neg_count = sum(
        1 for h in (h2, h11) if h is not None and h.direction == "negative"
    )
    if pos_count >= 1 and neg_count == 0:
        direction = "positive"
    elif neg_count >= 1 and pos_count == 0:
        direction = "negative"
    elif pos_count and neg_count:
        direction = "mixed"
    else:
        direction = "neutral"

    parts: list[str] = []
    if ll_hora is not None:
        parts.append(ll_hora.verdict)
    if h2 is not None:
        parts.append(f"2H(retention): {h2.verdict}")
    if h11 is not None:
        parts.append(f"11H(inflow): {h11.verdict}")
    verdict = "Wealth promise: " + ("; ".join(parts) if parts else "indicative")
    verdict = verdict[:140]

    return Finding(
        id="domain.wealth.promise",
        rule="wealth.promise",
        source_sequence=None,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"upstream_refs={refs}",
            f"asc_sign={asc_sign}",
            f"second_house_sign={_second_house_sign(asc_sign)}",
            f"eleventh_house_sign={_eleventh_house_sign(asc_sign)}",
            "composition=d2.lagna_lord_in_hora + bhava_bala[2H] + bhava_bala[11H]",
            "model=two_engine_retention_inflow (2H=retention, 11H=inflow)",
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
                id="domain.wealth.trigger.current_md",
                rule="wealth.trigger.current_md",
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
                id="domain.wealth.trigger.current_ad",
                rule="wealth.trigger.current_ad",
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
    """MKS on Jupiter/Venus + Daridra yoga + weak 2H/11H bhava-bala."""
    afflictions: list[Finding] = []
    afflicted_planets: list[str] = []

    # 1. MKS on dhana karakas (Jupiter / Venus).
    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    for planet, mks_finding in mks.items():
        if planet in _WEALTH_PLANETS:
            afflictions.append(
                Finding(
                    id=f"domain.wealth.affliction.mks_{planet.lower()}",
                    rule="wealth.affliction.mks",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=(
                        f"Dhana karaka {planet} in MKS — {mks_finding.verdict}"
                    )[:140],
                    evidence=[
                        f"planet={planet}",
                        f"upstream_mks_finding_id={mks_finding.id}",
                        "composition=practitioner.mks (dhana karaka)",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )
            if planet not in afflicted_planets:
                afflicted_planets.append(planet)

    # 2. Daridra yoga (poverty indicator).
    daridra_list = _collect_yogas_by_prefix(primitives, (_DARIDRA_YOGA_PREFIX,))
    for d in daridra_list:
        afflictions.append(
            Finding(
                id="domain.wealth.affliction.daridra_yoga",
                rule="wealth.affliction.daridra_yoga",
                source_sequence=None,
                classification="affliction",
                direction="negative",
                verdict=("Daridra Yoga — " + d.verdict)[:140],
                evidence=[
                    f"upstream_yoga_id={d.id}",
                    "composition=practitioner.yogas_extended.daridra",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 3. Weak 2H / 11H bhava-bala (retention or inflow failure).
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    for house, engine in ((2, "retention"), (11, "inflow")):
        bh = bhava_bala.get(house)
        if bh is not None and bh.direction == "negative":
            afflictions.append(
                Finding(
                    id=f"domain.wealth.affliction.weak_h{house}_{engine}",
                    rule="wealth.affliction.weak_bhava",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=(
                        f"Weak {house}H ({engine}) — " + bh.verdict
                    )[:140],
                    evidence=[
                        f"house={house}",
                        f"engine={engine}",
                        f"upstream_bhava_bala_id={bh.id}",
                        "composition=foundation.bhava_bala (2H retention / 11H inflow)",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )

    return afflictions, afflicted_planets


# ---------------------------------------------------------------------------
# Cross-checks
# ---------------------------------------------------------------------------


def _build_cross_checks(primitives: Mapping[str, Any]) -> list[Finding]:
    cross_checks: list[Finding] = []

    # 1. Karaka triangulation (wealth row).
    triangulation: Mapping[str, Finding] = primitives.get("karaka_triangulation", {})
    tri = triangulation.get("wealth")
    if tri is not None:
        cross_checks.append(
            Finding(
                id="domain.wealth.cross_check.triangulation",
                rule="wealth.cross_check.triangulation",
                source_sequence=None,
                classification="primitive",
                direction=tri.direction,
                verdict=("Wealth triangulation — " + tri.verdict)[:140],
                evidence=[
                    f"upstream_triangulation_id={tri.id}",
                    "composition=foundation.karaka_triangulation.wealth",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 2. Two-engine retention vs inflow stance (per practitioner research).
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    h2 = bhava_bala.get(2)
    h11 = bhava_bala.get(11)
    if h2 is not None or h11 is not None:
        h2_dir = h2.direction if h2 is not None else "unknown"
        h11_dir = h11.direction if h11 is not None else "unknown"
        if h2_dir == "positive" and h11_dir == "positive":
            stance = "retention + inflow both strong"
            direction = "positive"
        elif h11_dir == "positive" and h2_dir == "negative":
            stance = "high earner / weak savings (11H>2H)"
            direction = "mixed"
        elif h2_dir == "positive" and h11_dir == "negative":
            stance = "retains but inflow weak (2H>11H)"
            direction = "mixed"
        elif h2_dir == "negative" and h11_dir == "negative":
            stance = "both engines weak"
            direction = "negative"
        else:
            stance = "neutral two-engine stance"
            direction = "neutral"
        upstream_ids = [
            (h2.id if h2 is not None else "none"),
            (h11.id if h11 is not None else "none"),
        ]
        cross_checks.append(
            Finding(
                id="domain.wealth.cross_check.two_engine_stance",
                rule="wealth.cross_check.two_engine_stance",
                source_sequence=None,
                classification="primitive",
                direction=direction,
                verdict=(f"Two-engine stance — {stance}")[:140],
                evidence=[
                    f"stance={stance}",
                    f"h2_direction={h2_dir}",
                    f"h11_direction={h11_dir}",
                    f"upstream_bhava_bala_ids={upstream_ids}",
                    "composition=foundation.bhava_bala[2H,11H] (retention vs inflow)",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 3. Positive dhana yogas (Lakshmi / Saraswati / Chamara / Adhi).
    dhana_yogas = _collect_yogas_by_prefix(
        primitives, _POSITIVE_DHANA_YOGA_PREFIXES,
    )
    for y in dhana_yogas:
        # Slug short-form: ``lakshmi``, ``saraswati`` etc.
        try:
            short = y.id.split(".")[2]
        except IndexError:
            short = "dhana"
        cross_checks.append(
            Finding(
                id=f"domain.wealth.cross_check.{short}_yoga",
                rule=f"wealth.cross_check.{short}_yoga",
                source_sequence=None,
                classification="primitive",
                direction="positive",
                verdict=(f"{short.title()} Yoga — " + y.verdict)[:140],
                evidence=[
                    f"upstream_yoga_id={y.id}",
                    f"yoga={short}",
                    f"composition=practitioner.yogas_extended.{short}",
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
) -> list[TimingWindow]:
    dhana_yogas = _collect_yogas_by_prefix(
        primitives, _POSITIVE_DHANA_YOGA_PREFIXES,
    )
    event_type = "wealth_event" if dhana_yogas else "general"
    seed_ids = [y.id for y in dhana_yogas]

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
                triggering_finding_ids=[cur_md.overall_verdict.id] + seed_ids,
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
                triggering_finding_ids=[first_ad.overall_verdict.id] + seed_ids,
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
        logger.debug("generate_remedies failed for wealth: %s", exc)
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
    """3-vote rule for wealth: 2H/11H bhava-bala (house), 2L/11L (lord),
    Jupiter not in MKS (karaka).
    """
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    h2 = bhava_bala.get(2)
    h11 = bhava_bala.get(11)
    house_indicator = bool(
        (h2 is not None and h2.direction == "positive")
        or (h11 is not None and h11.direction == "positive")
    )

    # 2L / 11L favourable — proxy via dhana yogas presence (Lakshmi etc).
    dhana_yogas = _collect_yogas_by_prefix(
        primitives, _POSITIVE_DHANA_YOGA_PREFIXES,
    )
    lord_indicator = bool(dhana_yogas)

    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    karaka_indicator = "Jupiter" not in mks

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
        tone = "wealth promise constructively supported"
    elif neg > pos:
        direction = "negative"
        tone = "wealth impediments dominate"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "wealth signals neutral"
    else:
        direction = "mixed"
        tone = "wealth signals mixed"

    verdict = f"Wealth domain verdict: {tone}; +{pos}/-{neg}"[:140]
    upstream = [promise.id] + [t.id for t in triggers] + [c.id for c in cross_checks]

    return Finding(
        id="domain.wealth.overall",
        rule="wealth.overall",
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


def synthesize_wealth(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    sequences_result: dict,
    primitives: dict,
    foundations: dict,
) -> DomainReading:
    """Wealth = 2H retention + 11H inflow + Dhana yogas + D2 hora.

    Composition map:
      - Promise: D2 lagna-lord Hora + 2H + 11H bhava-bala.
      - Triggers: current MD + first AD overall verdicts.
      - Cross-checks: karaka triangulation (wealth), two-engine stance
        (retention vs inflow), Lakshmi/Saraswati/Chamara/Adhi positive
        yogas.
      - Afflictions: MKS on Jupiter/Venus (dhana karakas), Daridra yoga
        (if present), weak 2H / 11H bhava-bala.
      - Timing windows: current MD + first AD; event_type =
        ``wealth_event`` when any positive dhana yoga is present, else
        ``general``.

    Args:
        chart: Full natal chart dict.
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi.
        sequences_result: Dict carrying ``vimshottari_md``,
            ``vimshottari_ad``, ``current_md_lord``.
        primitives: Dict carrying ``karakas``, ``karaka_triangulation``,
            ``marana_karaka_sthana``, ``bhava_bala``, ``avasthas``,
            ``d2_findings``, ``yogas_extended``.
        foundations: Dict carrying ``functional_nature``.

    Returns:
        :class:`DomainReading` for the wealth domain.

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


__all__ = ["synthesize_wealth"]
