"""Doctrine source: Composition of sequences.career_executive,
divisional_readings.d10_dashamsha, sequences.vimshottari_md/ad,
computations.karakas, computations.karaka_triangulation,
computations.marana_karaka_sthana, and computations.remedies.

Phase 5 Wave A domain synthesizer — CAREER.

Architectural discipline (spec Section 1)
-----------------------------------------

Domains are **pure synthesizers**. This module composes upstream
Finding objects BY ID; it does NOT redo D-chart or whole-sign math.
Every cross-check Finding lists the upstream finding ids it draws on
in its ``evidence`` field so the architectural-purity gate
(``test_career_domain_references_d10_finding_ids``) passes.

The 7 fields of a :class:`DomainReading` are populated as follows:

  - **promise**       — the latent career capability, drawn primarily
                        from the D10 5-pillar concordance + Career
                        Executive Step 1 (Vargottama AmK).
  - **triggers**      — current MD + AD judgments (their overall
                        verdicts) re-emitted as career-context triggers.
  - **afflictions**   — MKS hits on career-relevant planets (Sun,
                        Mercury, Mars, Saturn, AmK) + Gandanta knot +
                        Vimsopaka-gate failures from Sequence 2.
  - **timing_windows** — current MD (career_shift) and first AD where
                        triggers fire (per spec's TimingWindow event_type).
  - **cross_checks**  — 5-pillar concordance, karaka triangulation,
                        and the Career Executive overall verdict.
  - **remedies**      — generated for any afflicted career-relevant
                        planet via :func:`generate_remedies`.
  - **confidence**    — 3-vote rule: 10H favourable indicators,
                        10L (10th house lord) favourable placement,
                        Sun (career karaka) favourable state.

Public API
==========

    synthesize_career(chart, asc_sign, moon_sign,
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


_DOMAIN_NAME: Final[str] = "career"
_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=composition of D10 + career_executive + vimshottari + karakas (Phase 5 Wave A)"
)

# Career-relevant planets — afflictions on these are surfaced.
_CAREER_PLANETS: Final[frozenset[str]] = frozenset(
    {"Sun", "Mercury", "Mars", "Saturn"}
)

# Default "neutral" confidence used while pillars are not yet wired.
_NEUTRAL_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_amk_planet(primitives: Mapping[str, Any]) -> str | None:
    amk_planet = primitives.get("amk_planet")
    if isinstance(amk_planet, str) and amk_planet:
        return amk_planet
    karakas = primitives.get("karakas")
    if isinstance(karakas, Mapping):
        amk = karakas.get("amatyakaraka")
        if amk is not None:
            for line in amk.evidence:
                if line.startswith("planet="):
                    return line.split("=", 1)[1]
    return None


def _planet_sign(d1_chart: Mapping[str, Mapping[str, object]], planet: str) -> int | None:
    entry = d1_chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if isinstance(sign, int) and 1 <= sign <= 12:
        return sign
    return None


def _tenth_house_sign(asc_sign: int) -> int:
    return ((asc_sign - 1) + 9) % 12 + 1


# ---------------------------------------------------------------------------
# Promise
# ---------------------------------------------------------------------------


def _build_promise(
    asc_sign: int,
    primitives: Mapping[str, Any],
    sequences_result: Mapping[str, Any],
) -> Finding:
    """The career promise — latent capability per D10 + Vargottama AmK."""
    d10_findings: Mapping[str, Finding] = primitives.get("d10_findings", {})
    pillars: Finding | None = d10_findings.get("d10.career_5_pillars")
    amk_planet = _get_amk_planet(primitives)

    refs: list[str] = []
    if pillars is not None:
        refs.append(pillars.id)

    career_exec = sequences_result.get("career_executive")
    seq_step_id: str | None = None
    if career_exec is not None:
        amk_step = career_exec.steps.get("vargottama_amatya_karaka")
        if amk_step is not None:
            refs.append(amk_step.id)
            seq_step_id = amk_step.id

    # Determine direction by combining pillars direction with Sequence-2 Step-1.
    direction = "neutral"
    if pillars is not None and pillars.direction in {"positive", "negative"}:
        direction = pillars.direction
    if seq_step_id is not None and career_exec is not None:
        s = career_exec.steps["vargottama_amatya_karaka"]
        if s.direction == "positive":
            direction = "positive"

    parts: list[str] = []
    if pillars is not None:
        parts.append(pillars.verdict)
    if amk_planet is not None:
        parts.append(f"AmK={amk_planet}")
    verdict = "Career promise: " + ("; ".join(parts) if parts else "indicative")
    verdict = verdict[:140]

    return Finding(
        id="domain.career.promise",
        rule="career.promise",
        source_sequence=None,
        classification="promise",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"upstream_refs={refs}",
            f"amatyakaraka_planet={amk_planet or 'unknown'}",
            f"asc_sign={asc_sign}",
            f"tenth_house_sign={_tenth_house_sign(asc_sign)}",
            "composition=d10.career_5_pillars + seq_2.step_1.vargottama_amatya_karaka",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_NEUTRAL_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------


def _build_triggers(sequences_result: Mapping[str, Any]) -> list[Finding]:
    """Current MD + first AD overall verdicts re-emitted as career triggers."""
    triggers: list[Finding] = []
    md_result = sequences_result.get("vimshottari_md")
    current_md_lord = sequences_result.get("current_md_lord", "unknown")

    if md_result is not None:
        cur_md = md_result.current_md_judgment
        triggers.append(
            Finding(
                id="domain.career.trigger.current_md",
                rule="career.trigger.current_md",
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
                    f"current_md_lord={current_md_lord}",
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
                id="domain.career.trigger.next_ad",
                rule="career.trigger.next_ad",
                source_sequence=None,
                classification="trigger",
                direction=first_ad.overall_verdict.direction,
                verdict=(
                    f"Next/current AD {first_ad.ad_lord} ({first_ad.start_date} "
                    f"-> {first_ad.end_date}): {first_ad.overall_verdict.direction}"
                )[:140],
                evidence=[
                    f"ad_lord={first_ad.ad_lord}",
                    f"md_lord={first_ad.md_lord}",
                    f"ad_start_date={first_ad.start_date}",
                    f"ad_end_date={first_ad.end_date}",
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
    sequences_result: Mapping[str, Any],
) -> tuple[list[Finding], list[str]]:
    """MKS afflictions on career-relevant planets + sequence-step warnings.

    Returns (afflictions, afflicted_planets) — afflicted_planets feeds the
    remedies generator.
    """
    afflictions: list[Finding] = []
    afflicted_planets: list[str] = []

    mks: Mapping[str, Finding] = primitives.get("marana_karaka_sthana", {})
    amk_planet = _get_amk_planet(primitives)

    for planet, mks_finding in mks.items():
        if planet in _CAREER_PLANETS or planet == amk_planet:
            afflictions.append(
                Finding(
                    id=f"domain.career.affliction.mks_{planet.lower()}",
                    rule="career.affliction.mks",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=f"Career MKS: {planet} — {mks_finding.verdict}"[:140],
                    evidence=[
                        f"planet={planet}",
                        f"upstream_mks_finding_id={mks_finding.id}",
                        "composition=practitioner.mks (career-relevant planet)",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )
            if planet not in afflicted_planets:
                afflicted_planets.append(planet)

    # Sequence 2 Gandanta + Vimsopaka gate failures.
    career_exec = sequences_result.get("career_executive")
    if career_exec is not None:
        gandanta_step = career_exec.steps.get("gandanta_knots")
        if gandanta_step is not None and gandanta_step.direction == "negative":
            afflictions.append(
                Finding(
                    id="domain.career.affliction.gandanta",
                    rule="career.affliction.gandanta",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=("Career Gandanta knot — " + gandanta_step.verdict)[:140],
                    evidence=[
                        f"upstream_seq_id={gandanta_step.id}",
                        "composition=seq_2.step_2.gandanta_knots",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )

        vims_step = career_exec.steps.get("vimsopaka_strength")
        if vims_step is not None and vims_step.direction == "negative":
            afflictions.append(
                Finding(
                    id="domain.career.affliction.vimsopaka_gate",
                    rule="career.affliction.vimsopaka_gate",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=("Career Vimsopaka gate fail — " + vims_step.verdict)[:140],
                    evidence=[
                        f"upstream_seq_id={vims_step.id}",
                        "composition=seq_2.step_3.vimsopaka_strength",
                        _DOCTRINE_SENTINEL,
                    ],
                    confidence=_NEUTRAL_CONFIDENCE,
                )
            )

        bottle_step = career_exec.steps.get("gulika_saturn_bottlenecks")
        if bottle_step is not None and bottle_step.direction == "negative":
            afflictions.append(
                Finding(
                    id="domain.career.affliction.bottleneck",
                    rule="career.affliction.bottleneck",
                    source_sequence=None,
                    classification="affliction",
                    direction="negative",
                    verdict=("Career bottleneck — " + bottle_step.verdict)[:140],
                    evidence=[
                        f"upstream_seq_id={bottle_step.id}",
                        "composition=seq_2.step_4.gulika_saturn_bottlenecks",
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


def _build_cross_checks(
    primitives: Mapping[str, Any],
    sequences_result: Mapping[str, Any],
) -> list[Finding]:
    """Cross-check findings that REFERENCE upstream finding ids."""
    cross_checks: list[Finding] = []

    # Career Executive overall verdict (Sequence 2).
    career_exec = sequences_result.get("career_executive")
    if career_exec is not None:
        ov = career_exec.overall_verdict
        cross_checks.append(
            Finding(
                id="domain.career.cross_check.executive_overall",
                rule="career.cross_check.executive_overall",
                source_sequence=None,
                classification="primitive",
                direction=ov.direction,
                verdict=("Career Executive 4-step verdict — " + ov.verdict)[:140],
                evidence=[
                    f"upstream_seq_id={ov.id}",
                    "composition=seq_2.overall",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # 5-pillar concordance from D10.
    d10_findings: Mapping[str, Finding] = primitives.get("d10_findings", {})
    pillars = d10_findings.get("d10.career_5_pillars")
    if pillars is not None:
        cross_checks.append(
            Finding(
                id="domain.career.cross_check.d10_pillars",
                rule="career.cross_check.d10_pillars",
                source_sequence=None,
                classification="primitive",
                direction=pillars.direction,
                verdict=("D10 5-pillar — " + pillars.verdict)[:140],
                evidence=[
                    f"upstream_d10_id={pillars.id}",
                    "composition=d10.career_5_pillars",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    # Karaka triangulation (career row).
    triangulation: Mapping[str, Finding] = primitives.get("karaka_triangulation", {})
    tri = triangulation.get("career")
    if tri is not None:
        cross_checks.append(
            Finding(
                id="domain.career.cross_check.triangulation",
                rule="career.cross_check.triangulation",
                source_sequence=None,
                classification="primitive",
                direction=tri.direction,
                verdict=("Karaka triangulation — " + tri.verdict)[:140],
                evidence=[
                    f"upstream_triangulation_id={tri.id}",
                    "composition=foundation.karaka_triangulation.career",
                    _DOCTRINE_SENTINEL,
                ],
                confidence=_NEUTRAL_CONFIDENCE,
            )
        )

    return cross_checks


# ---------------------------------------------------------------------------
# Timing windows
# ---------------------------------------------------------------------------


def _build_timing_windows(sequences_result: Mapping[str, Any]) -> list[TimingWindow]:
    windows: list[TimingWindow] = []
    md_result = sequences_result.get("vimshottari_md")
    if md_result is not None:
        cur_md = md_result.current_md_judgment
        windows.append(
            TimingWindow(
                start_date=cur_md.start_date,
                end_date=cur_md.end_date,
                driving_period=f"MD {cur_md.md_lord}",
                event_type="career_shift",
                confidence_band="indicative_only",
                triggering_finding_ids=[cur_md.overall_verdict.id],
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
                event_type="career_shift",
                confidence_band="indicative_only",
                triggering_finding_ids=[first_ad.overall_verdict.id],
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
    """Synthesize career-relevant remedies via the orchestrator."""
    if not afflicted_planets:
        return []

    # Lagna lord = sign ruler of asc_sign; 5L/9L for Trikona gating.
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
        remedy_bundle = generate_remedies(
            afflicted_planets=afflicted_planets,
            lagna_lord=lagna_lord,
            fifth_lord=fifth_lord,
            ninth_lord=ninth_lord,
            atmakaraka=atmakaraka,
            asc_sign=asc_sign,
            functional_natures=natures,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("generate_remedies failed for career: %s", exc)
        return []

    remedies: list[RemedyRecommendation] = []
    for category, kind in (
        ("mantras", "mantra"),
        ("daan", "donation"),
        ("yantras", "yantra"),
        ("gemstones", "gemstone"),
    ):
        for f in remedy_bundle.get(category, []):
            remedies.append(
                RemedyRecommendation(
                    kind=kind,  # type: ignore[arg-type]
                    description=f.verdict,
                    source=f"upstream:{f.id}",
                )
            )
    return remedies


# ---------------------------------------------------------------------------
# Overall verdict + confidence
# ---------------------------------------------------------------------------


def _compute_confidence(
    asc_sign: int,
    primitives: Mapping[str, Any],
    chart: Mapping[str, Any],
) -> ConfidenceScore:
    """3-vote rule for career: 10H pillars, 10L (tenth lord), Sun (karaka)."""
    d10_findings: Mapping[str, Finding] = primitives.get("d10_findings", {})
    pillars = d10_findings.get("d10.career_5_pillars")
    house_indicator = bool(pillars is not None and pillars.direction == "positive")

    # 10L: tenth-house lord. Favourable if its D10 placement is in own sign
    # OR vargottama (proxied via D10 lagna_lord finding direction).
    tenth_lord_finding = d10_findings.get("d10.tenth_house_lord")
    lord_indicator = bool(
        tenth_lord_finding is not None
        and "own sign" in (tenth_lord_finding.verdict or "").lower()
    )

    # Sun (career karaka) — proxied by Sun's avastha primitive when available;
    # absent that we check Sun is NOT in MKS (12H).
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
        tone = "career promise constructively supported"
    elif neg > pos:
        direction = "negative"
        tone = "career impediments dominate"
    elif pos == 0 and neg == 0:
        direction = "neutral"
        tone = "career signals neutral"
    else:
        direction = "mixed"
        tone = "career signals mixed"

    verdict = f"Career domain verdict: {tone}; +{pos}/-{neg}"[:140]
    upstream = [promise.id] + [t.id for t in triggers] + [c.id for c in cross_checks]

    return Finding(
        id="domain.career.overall",
        rule="career.overall",
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


def synthesize_career(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    sequences_result: dict,
    primitives: dict,
    foundations: dict,
) -> DomainReading:
    """Pure synthesis of career-related findings.

    Composes ``DomainReading`` per the spec — see module docstring for
    the mapping of upstream modules into the 7 schema fields. Performs
    NO chart math; every reference is by upstream finding id.

    Args:
        chart: Full natal chart dict (read for asc / Moon / d1 lookups
            via helpers; no chart math is recomputed here).
        asc_sign: 1-indexed natal ascendant rashi.
        moon_sign: 1-indexed natal Moon rashi.
        sequences_result: Dict carrying ``career_executive``,
            ``vimshottari_md``, ``vimshottari_ad``,
            ``current_md_lord``.
        primitives: Dict carrying ``karakas``, ``amk_planet``,
            ``karaka_triangulation``, ``marana_karaka_sthana``,
            ``d10_findings``, ``arudha_padas``.
        foundations: Dict carrying ``functional_nature`` (for remedies
            gemstone gating).

    Returns:
        :class:`DomainReading` for the career domain.

    Raises:
        ValueError: if ``asc_sign`` or ``moon_sign`` is out of 1..12.
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign!r}")
    if not isinstance(moon_sign, int) or not (1 <= moon_sign <= 12):
        raise ValueError(f"moon_sign must be in 1..12, got {moon_sign!r}")

    promise = _build_promise(asc_sign, primitives, sequences_result)
    triggers = _build_triggers(sequences_result)
    afflictions, afflicted_planets = _build_afflictions(primitives, sequences_result)
    cross_checks = _build_cross_checks(primitives, sequences_result)
    timing_windows = _build_timing_windows(sequences_result)
    remedies = _build_remedies(asc_sign, afflicted_planets, primitives, foundations)
    confidence = _compute_confidence(asc_sign, primitives, chart)
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


__all__ = ["synthesize_career"]
