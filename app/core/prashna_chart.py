"""Prashna (Horary) chart + verdict modules — Gap K.

Per Prashna Marga (Krishneeya Sanjana Kavi, ~1649 CE), Daivajna Vallabha,
Shatpanchashika. Prashna is the question-chart paradigm — cast for the
moment a question reaches the astrologer's ears, NOT the native's
birth time.

## Role reassignment from natal

In natal: Lagna = native, Moon = mind.
In prashna: Lagna = SUBJECT of the question (karya), Moon = QUESTIONER's
intent/mental state, 7H = OPPOSING party (in any contest), Sun =
authority/answer-giver in the matter.

## Construction protocol (PM 1.15-1.22)

  - TIME = moment the question REACHES the astrologer (for written/SMS:
    when astrologer READS; for voice: when astrologer HEARS)
  - PLACE = astrologer's physical location (NOT questioner's)
  - All planets at TRANSIT positions; Lagna ascendant at that time/place

## Verdict modules

For each of 7 question domains: marriage, career, lost-item, disease,
pregnancy, travel, litigation. Each combines:

  - Karya bhava + karya karaka rules (domain-specific)
  - Lagna modality (chara/sthira/dwiswabhava) for yes-quick / no /
    conditional timing
  - Pancha Mahabhuta of Lagna for element-based verdict bias
  - Aspect of malefics on Lagna for unfavorable / Jupiter aspect for favorable
  - Hora at question moment (multiplier on confidence)

Refusal protocol: during Rahu Kalam / Yamagandam / Bhadra karana, the
module returns "REFUSE" rather than a low-confidence verdict per
PM 1.24 — preserves doctrinal integrity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart


# Sign modality classification per BPHS Ch.2
_CHARA_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})    # movable
_STHIRA_SIGNS: Final[frozenset[int]] = frozenset({2, 5, 8, 11})   # fixed
_DUAL_SIGNS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})     # dwiswabhava

# Pancha Mahabhuta classification
_ELEMENT_OF_SIGN: Final[Mapping[int, str]] = {
    1: "fire", 5: "fire", 9: "fire",         # Aries, Leo, Sagittarius
    2: "earth", 6: "earth", 10: "earth",     # Taurus, Virgo, Capricorn
    3: "air", 7: "air", 11: "air",           # Gemini, Libra, Aquarius
    4: "water", 8: "water", 12: "water",     # Cancer, Scorpio, Pisces
}

# Natural benefic / malefic classification (CLAUDE.md lock)
_NATURAL_BENEFICS: Final[frozenset[str]] = frozenset(
    {"Jupiter", "Venus", "Mercury", "Moon"}
)
_NATURAL_MALEFICS: Final[frozenset[str]] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)


@dataclass(frozen=True)
class PrashnaVerdict:
    """Result of a prashna question verdict module."""
    question_domain: str        # "marriage" / "career" / "lost_item" / etc.
    karya_bhava: int            # which bhava represents the question
    verdict_label: str          # YES_QUICK / YES_DELAYED / NO / NO_DELAYED /
                                # CONDITIONAL_PARTIAL / UNCERTAIN / REFUSE
    confidence: float           # 0.0-1.0
    timing_estimate: str        # "days" / "months" / "years" / "uncertain"
    rationale: tuple[str, ...]  # chain of rules that fired
    refused_reason: str | None = None


def lagna_modality_verdict(lagna_sign: int) -> tuple[str, float, str]:
    """Per PM 4.7 + 4.20 — sign modality dictates timing/verdict.

    Returns (label, confidence, timing_estimate).
    """
    if not 1 <= lagna_sign <= 12:
        raise ValueError(f"lagna_sign must be 1..12, got {lagna_sign}")
    if lagna_sign in _CHARA_SIGNS:
        return ("YES_QUICK", 0.7, "days")
    if lagna_sign in _STHIRA_SIGNS:
        return ("NO_OR_LONG_DELAY", 0.6, "years")
    return ("CONDITIONAL_PARTIAL", 0.5, "months")


def element_of_lagna(lagna_sign: int) -> str:
    """Pancha Mahabhuta element of Lagna sign."""
    if not 1 <= lagna_sign <= 12:
        raise ValueError(f"lagna_sign must be 1..12")
    return _ELEMENT_OF_SIGN[lagna_sign]


def element_question_match(lagna_sign: int, question_domain: str) -> float:
    """Score how well the Lagna element matches the question domain.

    Returns multiplier 0.7-1.2 to apply to the verdict confidence.
    """
    element = element_of_lagna(lagna_sign)
    domain_element_affinity: Mapping[str, Mapping[str, float]] = {
        "marriage":    {"water": 1.2, "earth": 1.0, "fire": 0.85, "air": 0.9},
        "career":      {"fire": 1.2, "earth": 1.05, "air": 1.0, "water": 0.85},
        "lost_item":   {"earth": 1.2, "fire": 0.9, "air": 0.95, "water": 1.0},
        "disease":     {"water": 1.0, "earth": 1.05, "fire": 0.9, "air": 0.95},
        "pregnancy":   {"water": 1.2, "earth": 1.05, "fire": 0.85, "air": 0.85},
        "travel":      {"air": 1.2, "fire": 1.1, "water": 0.95, "earth": 0.85},
        "litigation":  {"fire": 1.15, "air": 1.0, "earth": 1.0, "water": 0.9},
    }
    return domain_element_affinity.get(question_domain, {}).get(element, 1.0)


def _check_lagna_aspects(chart: Chart) -> tuple[float, list[str]]:
    """Check benefic vs malefic aspects on Lagna at prashna moment.

    Returns (net_modifier, [rationale strings]).
    Benefic aspect: +0.15 each. Malefic aspect: -0.20 each.
    """
    # Whole-sign aspects: any planet in 7th from Lagna aspects Lagna
    rationale: list[str] = []
    modifier = 0.0
    seventh = 7  # 7th from Lagna is always natal house 7
    for p, h in chart.planet_houses.items():
        if h != seventh:
            continue
        if p in _NATURAL_BENEFICS:
            modifier += 0.15
            rationale.append(f"Benefic {p} aspects Lagna from 7H (+0.15)")
        elif p in _NATURAL_MALEFICS:
            modifier -= 0.20
            rationale.append(f"Malefic {p} aspects Lagna from 7H (-0.20)")
    return modifier, rationale


def _hora_modifier(hora_lord: str | None) -> float:
    """Hora at question moment modulates confidence.

    Per PM table:
      Jupiter hora: 1.15 — universally favorable
      Saturn hora: 0.85 — suppress confidence
      Sun hora: 1.0 (authority-question slight boost)
      Default: 1.0
    """
    if hora_lord is None:
        return 1.0
    return {
        "Jupiter": 1.15, "Venus": 1.10, "Mercury": 1.05,
        "Sun": 1.0, "Moon": 1.0, "Mars": 0.95, "Saturn": 0.85,
    }.get(hora_lord, 1.0)


def _check_refusal_window(
    is_rahu_kalam: bool, is_yamagandam: bool, is_bhadra: bool,
) -> str | None:
    """Per PM 1.24, refuse to read in inauspicious windows.

    Returns refusal reason string, or None if OK to proceed.
    """
    if is_rahu_kalam:
        return "REFUSE: Rahu Kalam — answers unreliable, deceptive"
    if is_yamagandam:
        return "REFUSE: Yamagandam — answers may indicate harm"
    if is_bhadra:
        return "REFUSE: Bhadra (Vishti) karana — uniformly inauspicious for prashna"
    return None


# ─── 7 Verdict Modules ─────────────────────────────────────────────


_KARYA_BHAVA: Final[Mapping[str, int]] = {
    "marriage": 7, "career": 10, "lost_item": 2, "disease": 6,
    "pregnancy": 5, "travel": 9, "litigation": 6,
}


def _build_verdict(
    chart: Chart, question_domain: str,
    domain_specific_score: float = 0.0,
    domain_specific_rationale: list[str] | None = None,
    hora_lord: str | None = None,
    is_rahu_kalam: bool = False,
    is_yamagandam: bool = False,
    is_bhadra: bool = False,
) -> PrashnaVerdict:
    """Compose a verdict from per-domain score + modality + element + aspects.

    All verdict modules share this synthesis pattern.
    """
    refusal = _check_refusal_window(is_rahu_kalam, is_yamagandam, is_bhadra)
    if refusal:
        return PrashnaVerdict(
            question_domain=question_domain,
            karya_bhava=_KARYA_BHAVA.get(question_domain, 1),
            verdict_label="REFUSE", confidence=0.0,
            timing_estimate="N/A",
            rationale=(refusal,),
            refused_reason=refusal,
        )

    label, base_conf, timing = lagna_modality_verdict(chart.asc_sign)
    element_mult = element_question_match(chart.asc_sign, question_domain)
    aspect_mod, aspect_rationale = _check_lagna_aspects(chart)
    hora_mult = _hora_modifier(hora_lord)

    final_score = (domain_specific_score + aspect_mod) * element_mult * hora_mult
    final_conf = min(1.0, base_conf + abs(final_score) * 0.5)

    # Adjust label based on net score
    if final_score >= 0.4:
        label = "YES_QUICK" if timing == "days" else "YES_DELAYED"
    elif final_score <= -0.4:
        label = "NO" if timing == "days" else "NO_DELAYED"

    rationale: list[str] = [
        f"Lagna sign {chart.asc_sign} → modality: {label} ({timing})",
        f"Element {element_of_lagna(chart.asc_sign)} match for {question_domain}: ×{element_mult:.2f}",
    ]
    rationale.extend(aspect_rationale)
    if hora_lord:
        rationale.append(f"Hora lord {hora_lord} modifier: ×{hora_mult:.2f}")
    if domain_specific_rationale:
        rationale.extend(domain_specific_rationale)

    return PrashnaVerdict(
        question_domain=question_domain,
        karya_bhava=_KARYA_BHAVA.get(question_domain, 1),
        verdict_label=label, confidence=final_conf,
        timing_estimate=timing,
        rationale=tuple(rationale),
    )


def prashna_marriage(
    chart: Chart, querent_gender: str = "M",
    hora_lord: str | None = None,
    is_rahu_kalam: bool = False, is_yamagandam: bool = False,
    is_bhadra: bool = False,
) -> PrashnaVerdict:
    """Marriage prashna per PM Ch.16.

    Karya = 7H + Venus (♀ for male querent) / Jupiter (♂ for female).
    """
    significator = "Jupiter" if querent_gender == "F" else "Venus"
    score = 0.0
    rationale: list[str] = []
    sig_h = chart.house_of(significator)
    if sig_h in {1, 7}:
        score += 0.35
        rationale.append(f"Significator {significator} in 1H/7H (+0.35)")
    moon_h = chart.house_of("Moon")
    ven_h = chart.house_of("Venus")
    if moon_h and ven_h and (moon_h == ven_h or ((moon_h - ven_h) % 12 == 6)):
        score += 0.20
        rationale.append("Moon-Venus conjunction or mutual aspect (+0.20)")
    return _build_verdict(
        chart, "marriage", score, rationale,
        hora_lord, is_rahu_kalam, is_yamagandam, is_bhadra,
    )


def prashna_career(
    chart: Chart, hora_lord: str | None = None,
    is_rahu_kalam: bool = False, is_yamagandam: bool = False,
    is_bhadra: bool = False,
) -> PrashnaVerdict:
    """Career/job prashna per PM Ch.18.

    Karya = 10H + Sun (authority) + Saturn (work) + Mercury (commerce).
    """
    score = 0.0
    rationale: list[str] = []
    sun_h = chart.house_of("Sun")
    if sun_h == 10 or sun_h == 1:
        score += 0.25
        rationale.append("Sun in 10H or aspecting Lagna (+0.25)")
    sat_h = chart.house_of("Saturn")
    if sat_h in {3, 6, 11}:
        score += 0.30
        rationale.append("Saturn well-placed (3/6/11) — stable employment (+0.30)")
    elif sat_h in {6, 8, 12}:
        score -= 0.30
        rationale.append("Saturn in dusthana — job loss risk (-0.30)")
    return _build_verdict(
        chart, "career", score, rationale,
        hora_lord, is_rahu_kalam, is_yamagandam, is_bhadra,
    )


def prashna_lost_item(
    chart: Chart, hora_lord: str | None = None,
    is_rahu_kalam: bool = False, is_yamagandam: bool = False,
    is_bhadra: bool = False,
) -> PrashnaVerdict:
    """Lost item prashna per PM Ch.11.

    Karya = 2H (movable wealth). Direction = sign of 2H lord.
    """
    score = 0.0
    rationale: list[str] = []
    # Find 2H lord — simplified: planet ruling the sign at house 2
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    l2 = next(
        (p for p, r in roles.items() if 2 in r.houses_ruled), None,
    )
    if l2 is None:
        return _build_verdict(chart, "lost_item", 0.0, ["2H lord not resolvable"],
                              hora_lord, is_rahu_kalam, is_yamagandam, is_bhadra)
    l2_h = chart.house_of(l2)
    if l2_h in {1, 2, 4, 5, 11}:
        score += 0.40
        rationale.append(f"2H lord {l2} in benefic house {l2_h} → RECOVERED soon (+0.40)")
    elif l2_h in {6, 8, 12}:
        score -= 0.45
        rationale.append(f"2H lord {l2} in dusthana {l2_h} → LOST PERMANENTLY (-0.45)")
    # Direction hint from 2H lord's sign
    DIRECTIONS = {1: "East", 5: "East", 9: "East",
                  2: "South", 6: "South", 10: "South",
                  3: "West", 7: "West", 11: "West",
                  4: "North", 8: "North", 12: "North"}
    sign_2L = chart.sign_of(l2)
    if sign_2L:
        rationale.append(f"Direction (sign of 2L): {DIRECTIONS.get(sign_2L, '?')}")
    return _build_verdict(
        chart, "lost_item", score, rationale,
        hora_lord, is_rahu_kalam, is_yamagandam, is_bhadra,
    )
