"""Doctrine source: D-16 lockfile — education routes through D24
Chaturvimsamsa. Composition of divisional_readings.d24_chaturvimsamsa
(PRIMARY per D-16) + divisional_readings.d9_navamsha (dharma/values
context overlay only; D24 dominates) + 4H + 5H bhava_bala +
Mercury (Buddhi karaka) avastha + Jupiter (Vidya karaka) avastha +
computations.karaka_triangulation (education row) +
sequences.vimshottari_md/ad + computations.remedies.

Phase 5 Wave B domain synthesizer — EDUCATION.

D-16 doctrine lock (``docs/doctrine-decisions.md``)
---------------------------------------------------

**Education routes through D24.** Per BPHS Vol.I Ch.6 v.21 (Vidya /
education chart per Chaturvimsamsa), the D24 is the canonical
divisional for formal learning, scholarship, and academic achievement.
This module is the *sole consumer* of
``computations/divisional_readings/d24_chaturvimsamsa.py``.

D9 (Navamsa — dharma/marriage) is consulted ONLY for a values overlay;
it does NOT contribute to education judgments. D4 (Chaturthamsa —
fixed assets) is not consulted at all.

The architectural-purity gate
``test_education_domain_references_d24_finding_ids`` enforces that
``domain.education.cross_checks`` references at least one ``d24.*``
upstream finding id — violating this is violating the D-16 lock.

Architectural discipline (spec Section 1)
-----------------------------------------

Domains are **pure synthesizers**. This module composes upstream
Finding objects BY ID; it does NOT redo D24 / bhava-bala math.

The 7 fields of a :class:`DomainReading` are populated as follows:

  - **promise**       — D24 lagna + 4H/5H bhava-bala + Mercury &
                        Jupiter avastha (Buddhi / Vidya karakas).
  - **triggers**      — current MD + first AD overall verdicts.
  - **afflictions**   — Mercury / Jupiter in MKS, weak 4H / 5H
                        bhava-bala.
  - **cross_checks**  — D24 lagna anchor + D24 4H lord + D24 5H lord +
                        karaka triangulation (education row) + D9
                        dharma overlay (context only).
  - **timing_windows** — current MD + first AD; event_type =
                         ``education_milestone`` when D24 + bhava-bala
                         all favourable, else ``general``.
  - **remedies**      — for any afflicted Mercury / Jupiter via
                        :func:`generate_remedies`.
  - **confidence**    — 3-vote rule: D24 lagna/4H favourable (house),
                        4L+5L favourable (lord), Mercury+Jupiter not in
                        MKS (karaka).

Public API
==========

    synthesize_education(chart, asc_sign, moon_sign,
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


_DOMAIN_NAME: Final[str] = "education"
_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=D-16 (D24 Chaturvimsamsa as Vidya chart per BPHS Vol.I Ch.6 v.21) "
    "+ 4H/5H bhava_bala + Mercury/Jupiter avasthas (Phase 5 Wave B)"
)

# Education-relevant karakas (Buddhi + Vidya).
_EDUCATION_KARAKAS: Final[tuple[str, ...]] = ("Mercury", "Jupiter")


_NEUTRAL_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fourth_house_sign(asc_sign: int) -> int:
    return ((asc_sign - 1) + 3) % 12 + 1


def _fifth_house_sign(asc_sign: int) -> int:
    return ((asc_sign - 1) + 4) % 12 + 1


# ---------------------------------------------------------------------------
# Promise
# ---------------------------------------------------------------------------


def _build_promise(
    asc_sign: int,
    primitives: Mapping[str, Any],
) -> Finding:
    """Education promise — D24 lagna + 4H/5H bhava-bala + Mercury/Jupiter."""
    d24_findings: Mapping[str, Finding] = primitives.get("d24_findings", {})
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    avasthas: Mapping[str, Finding] = primitives.get("avasthas", {})

    d24_lagna = d24_findings.get("d24.lagna")
    h4 = bhava_bala.get(4)
    h5 = bhava_bala.get(5)
    mercury_av = avasthas.get("Mercury")
    jupiter_av = avasthas.get("Jupiter")

    refs: list[str] = []
    if d24_lagna is not None:
        refs.append(d24_lagna.id)
    if h4 is not None:
        refs.append(h4.id)
    if h5 is not None:
        refs.append(h5.id)
    if mercury_av is not None:
        refs.append(mercury_av.id)
    if jupiter_av is not None:
        refs.append(jupiter_av.id)

    # Direction policy:
    #   positive iff (4H or 5H positive) AND (Mercury or Jupiter avastha
    #   positive) AND no key marker negative.
    pos_house = any(
        h is not None and h.direction == "positive" for h in (h4, h5)
    )
    neg_house = any(
        h is not None and h.direction == "negative" for h in (h4, h5)
    )
    pos_karaka = any(
        a is not None and a.direction == "positive"
        for a in (mercury_av, jupiter_av)
    )
    neg_karaka = any(
        a is not None and a.direction == "negative"
        for a in (mercury_av, jupiter_av)
    )

    if pos_house and pos_karaka and not (neg_house and neg_karaka):
        direction = "positive"
    elif neg_house and neg_karaka and not pos_house:
        direction = "negative"
    elif pos_house or pos_karaka:
        direction = "mixed" if (neg_house or neg_karaka) else "positive"
    elif neg_house or neg_karaka:
        direction = "negative"
    else:
        direction = "neutral"

    parts: list[str] = []
    if d24_lagna is not None:
        parts.append(d24_lagna.verdict)
    if h4 is not None:
        parts.append(f"4H: {h4.verdict}")
    if h5 is not None:
        parts.append(f"5H: {h5.verdict}")
    verdict = "Education promise: " + ("; ".join(parts) if parts else "indicative")
    verdict = verdict[:140]

    return Finding(
        id="domain.education.promise",
        rule="education.promise",
        source_sequence=None,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"upstream_refs={refs}",
            f"asc_sign={asc_sign}",
            f"fourth_house_sign={_fourth_house_sign(asc_sign)}",
            f"fifth_house_sign={_fifth_house_sign(asc_sign)}",
            "composition=d24.lagna + bhava_bala[4H,5H] + avasthas[Mercury,Jupiter]",
            "doctrine_lock=D-16 (D24 Chaturvimsamsa = Vidya chart)",
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
                id="domain.education.trigger.current_md",
                rule="education.trigger.current_md",
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
                id="domain.education.trigger.current_ad",
                rule="education.trigger.current_ad",
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
    """Mercury / Jupiter in MKS + weak 4H / 5H bhava-bala."""
    afflictions: list[Finding] = []
    afflicted_planets: list[str] = []

    # 1. MKS on Mercury (Buddhi karaka) / Jupiter (Vidya karaka).
    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    for planet in _EDUCATION_KARAKAS:
        mks_finding = mks.get(planet)
        if mks_finding is None:
            continue
        afflictions.append(
            Finding(
                id=f"domain.education.affliction.mks_{planet.lower()}",
                rule="education.affliction.mks",
                source_sequence=None,
                classification="affliction",
                direction="negative",
                verdict=(
                    f"Education karaka {planet} in MKS — {mks_finding.verdict}"
                )[:140],
                evidence=[
                    f"planet={planet}",
                    f"upstream_mks_finding_id={mks_finding.id}",
                    "composition=practitioner.mks (education karaka)",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )
        if planet not in afflicted_planets:
            afflicted_planets.append(planet)

    # 2. Weak 4H / 5H bhava-bala.
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    for house, label in ((4, "formal-education foundation"), (5, "intellectual capacity")):
        bh = bhava_bala.get(house)
        if bh is not None and bh.direction == "negative":
            afflictions.append(
                Finding(
                    id=f"domain.education.affliction.weak_h{house}",
                    rule="education.affliction.weak_bhava",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=(
                        f"{house}H ({label}) weak — " + bh.verdict
                    )[:140],
                    evidence=[
                        f"house={house}",
                        f"label={label}",
                        f"upstream_bhava_bala_id={bh.id}",
                        "composition=foundation.bhava_bala (4H/5H education)",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )

    return afflictions, afflicted_planets


# ---------------------------------------------------------------------------
# Cross-checks — D24 dominates per D-16 lock
# ---------------------------------------------------------------------------


def _build_cross_checks(primitives: Mapping[str, Any]) -> list[Finding]:
    """Cross-checks. D-16 lock: D24 ids MUST be present in evidence."""
    cross_checks: list[Finding] = []

    d24_findings: Mapping[str, Finding] = primitives.get("d24_findings", {})

    # 1. D24 lagna anchor — the education frame.
    d24_lagna = d24_findings.get("d24.lagna")
    if d24_lagna is not None:
        cross_checks.append(
            Finding(
                id="domain.education.cross_check.d24_lagna",
                rule="education.cross_check.d24_lagna",
                source_sequence=None,
                classification="primitive",
                direction=d24_lagna.direction,
                verdict=("D24 Vidya frame anchor — " + d24_lagna.verdict)[:140],
                evidence=[
                    f"upstream_d24_id={d24_lagna.id}",
                    "composition=d24.lagna (Vidya frame anchor)",
                    "doctrine_lock=D-16",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 2. D24 4H lord — formal-education foundation.
    d24_fourth = d24_findings.get("d24.fourth_house_lord")
    if d24_fourth is not None:
        cross_checks.append(
            Finding(
                id="domain.education.cross_check.d24_fourth_house_lord",
                rule="education.cross_check.d24_fourth_house_lord",
                source_sequence=None,
                classification="primitive",
                direction=d24_fourth.direction,
                verdict=(
                    "D24 4H lord (formal-education foundation) — " + d24_fourth.verdict
                )[:140],
                evidence=[
                    f"upstream_d24_id={d24_fourth.id}",
                    "composition=d24.fourth_house_lord",
                    "doctrine_lock=D-16",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 3. D24 5H lord — intellectual capacity / purva-punya.
    d24_fifth = d24_findings.get("d24.fifth_house_lord")
    if d24_fifth is not None:
        cross_checks.append(
            Finding(
                id="domain.education.cross_check.d24_fifth_house_lord",
                rule="education.cross_check.d24_fifth_house_lord",
                source_sequence=None,
                classification="primitive",
                direction=d24_fifth.direction,
                verdict=(
                    "D24 5H lord (intellectual capacity) — " + d24_fifth.verdict
                )[:140],
                evidence=[
                    f"upstream_d24_id={d24_fifth.id}",
                    "composition=d24.fifth_house_lord",
                    "doctrine_lock=D-16",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 4. D24 Mercury (Buddhi karaka) placement.
    d24_mercury = d24_findings.get("d24.planet_in_mercury")
    if d24_mercury is not None:
        cross_checks.append(
            Finding(
                id="domain.education.cross_check.d24_mercury",
                rule="education.cross_check.d24_mercury",
                source_sequence=None,
                classification="primitive",
                direction=d24_mercury.direction,
                verdict=(
                    "D24 Mercury (Buddhi karaka) placement — " + d24_mercury.verdict
                )[:140],
                evidence=[
                    f"upstream_d24_id={d24_mercury.id}",
                    "composition=d24.planet_in_mercury (Buddhi karaka)",
                    "doctrine_lock=D-16",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 5. D24 Jupiter (Vidya karaka) placement.
    d24_jupiter = d24_findings.get("d24.planet_in_jupiter")
    if d24_jupiter is not None:
        cross_checks.append(
            Finding(
                id="domain.education.cross_check.d24_jupiter",
                rule="education.cross_check.d24_jupiter",
                source_sequence=None,
                classification="primitive",
                direction=d24_jupiter.direction,
                verdict=(
                    "D24 Jupiter (Vidya karaka) placement — " + d24_jupiter.verdict
                )[:140],
                evidence=[
                    f"upstream_d24_id={d24_jupiter.id}",
                    "composition=d24.planet_in_jupiter (Vidya karaka)",
                    "doctrine_lock=D-16",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 6. Karaka triangulation (education row).
    triangulation: Mapping[str, Finding] = primitives.get("karaka_triangulation", {})
    tri = triangulation.get("education")
    if tri is not None:
        cross_checks.append(
            Finding(
                id="domain.education.cross_check.triangulation",
                rule="education.cross_check.triangulation",
                source_sequence=None,
                classification="primitive",
                direction=tri.direction,
                verdict=("Education triangulation — " + tri.verdict)[:140],
                evidence=[
                    f"upstream_triangulation_id={tri.id}",
                    "composition=foundation.karaka_triangulation.education",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 7. D9 dharma overlay (CONTEXT ONLY — does NOT dominate per D-16).
    d9_findings: Mapping[str, Finding] = primitives.get("d9_findings", {})
    d9_lagna = d9_findings.get("d9.lagna")
    if d9_lagna is not None:
        cross_checks.append(
            Finding(
                id="domain.education.cross_check.d9_dharma_overlay",
                rule="education.cross_check.d9_dharma_overlay",
                source_sequence=None,
                classification="primitive",
                direction="neutral",  # context, not judgment
                verdict=(
                    "D9 dharma/values overlay (context only; D24 dominates) — "
                    + d9_lagna.verdict
                )[:140],
                evidence=[
                    f"upstream_d9_id={d9_lagna.id}",
                    "composition=d9.lagna (values overlay only, not primary)",
                    "doctrine_lock=D-16 (D24 dominates; D9 overlay context only)",
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
    """event_type=education_milestone when D24 lagna favourable + bhava-bala."""
    d24_findings: Mapping[str, Finding] = primitives.get("d24_findings", {})
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    d24_lagna = d24_findings.get("d24.lagna")
    h4 = bhava_bala.get(4)
    h5 = bhava_bala.get(5)

    favourable_promise = (
        (d24_lagna is None or d24_lagna.direction != "negative")
        and any(h is not None and h.direction == "positive" for h in (h4, h5))
        and not any(h is not None and h.direction == "negative" for h in (h4, h5))
    )

    seed_ids: list[str] = []
    if d24_lagna is not None:
        seed_ids.append(d24_lagna.id)
    if h4 is not None:
        seed_ids.append(h4.id)
    if h5 is not None:
        seed_ids.append(h5.id)

    windows: list[TimingWindow] = []
    md_result = sequences_result.get("vimshottari_md")
    if md_result is not None:
        cur_md = md_result.current_md_judgment
        event_type = (
            "education_milestone"
            if favourable_promise and cur_md.overall_verdict.direction == "positive"
            else "general"
        )
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
        event_type = (
            "education_milestone"
            if favourable_promise and first_ad.overall_verdict.direction == "positive"
            else "general"
        )
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
        logger.debug("generate_remedies failed for education: %s", exc)
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
    """3-vote rule for education: D24 lagna / 4H favourable (house),
    4L+5L favourable proxy (lord), Mercury+Jupiter not in MKS (karaka).
    """
    d24_findings: Mapping[str, Finding] = primitives.get("d24_findings", {})
    bhava_bala: Mapping[int, Finding] = primitives.get("bhava_bala", {})
    d24_lagna = d24_findings.get("d24.lagna")
    h4 = bhava_bala.get(4)

    house_indicator = bool(
        (d24_lagna is not None and d24_lagna.direction == "positive")
        or (h4 is not None and h4.direction == "positive")
    )

    d24_fourth = d24_findings.get("d24.fourth_house_lord")
    d24_fifth = d24_findings.get("d24.fifth_house_lord")
    lord_indicator = bool(
        (d24_fourth is not None and d24_fourth.direction == "positive")
        or (d24_fifth is not None and d24_fifth.direction == "positive")
    )

    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    karaka_indicator = all(p not in mks for p in _EDUCATION_KARAKAS)

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
        tone = "education promise constructively supported"
    elif neg > pos:
        direction = "negative"
        tone = "education impediments dominate"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "education signals neutral"
    else:
        direction = "mixed"
        tone = "education signals mixed"

    verdict = f"Education domain verdict: {tone}; +{pos}/-{neg}"[:140]
    upstream = [promise.id] + [t.id for t in triggers] + [c.id for c in cross_checks]

    return Finding(
        id="domain.education.overall",
        rule="education.overall",
        source_sequence=None,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"positive_findings={pos}",
            f"negative_findings={neg}",
            f"upstream_finding_ids={upstream}",
            "doctrine_lock=D-16 (D24 Chaturvimsamsa)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_NEUTRAL_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def synthesize_education(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    sequences_result: dict,
    primitives: dict,
    foundations: dict,
) -> DomainReading:
    """Education = D24 (D-16 primary) + 4H/5H + Mercury/Jupiter karakas.

    Per D-16 lockfile, education routes through D24 Chaturvimsamsa;
    D9 contributes a values overlay only (NOT primary).

    Composition map:
      - Promise: D24 lagna + 4H/5H bhava-bala + Mercury/Jupiter avastha.
      - Triggers: current MD + first AD overall verdicts.
      - Cross-checks: D24 lagna + D24 4L + D24 5L + D24 Mercury + D24
        Jupiter + karaka triangulation (education) + D9 dharma overlay.
      - Afflictions: Mercury / Jupiter in MKS, weak 4H / 5H bhava-bala.
      - Timing windows: current MD + first AD; event_type =
        ``education_milestone`` when D24+bhava-bala favourable AND dasha
        positive, else ``general``.

    Args:
        chart: Full natal chart dict.
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi.
        sequences_result: Dict carrying ``vimshottari_md``,
            ``vimshottari_ad``, ``current_md_lord``.
        primitives: Dict carrying ``karakas``, ``karaka_triangulation``,
            ``marana_karaka_sthana``, ``bhava_bala``, ``avasthas``,
            ``d24_findings`` (PRIMARY per D-16), ``d9_findings``
            (overlay only).
        foundations: Dict carrying ``functional_nature``.

    Returns:
        :class:`DomainReading` for the education domain.

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


__all__ = ["synthesize_education"]
