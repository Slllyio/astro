"""Three-Pillar Bhava Judge — Phase 6 of the astrologer's-lens framework.

Composes Phases 1-5 into the framework's core prediction primitive:
**given a chart and a target bhava, return a structured verdict on
whether that bhava's classical promise is alive, weak, or dead.**

## The three pillars (BPHS Ch.10)

A bhava's strength is judged by three independent tracks:

1. **Bhava itself** — natural benefic/malefic occupation, aspects on
   the bhava sign, drishti from natural malefics (negative) vs benefics
   (positive), argala intervention.
2. **Bhava lord** — the lord's dignity (own/exalt/debil), placement
   (dusthana vs Kendra/Trikona), Shadbala strength threshold,
   functional role (FB/FM/YK/Maraka/Badhakesh).
3. **Karaka** — the natural significator for that bhava (BPHS Ch.6).
   Dignity, placement, aspects.

## The AND-gate

A bhava promise is "strong" only when **≥2 pillars are positive AND
at least one confirmation arrives from yoga or argala**. This mirrors
the blueprint's ≥3-confirmation principle. Single-pillar positives
remain "weak promise present" but don't qualify as confirmed.

## Output

A ``BhavaVerdict`` dataclass carries the verdict label
(``strong/medium/weak/afflicted``), each pillar's score, the active
yoga overlay relevant to this bhava, and a list of ``Reasoning``
records — each tying a finding to its classical anchor (citation).
Phase 9 (Reading Composer) renders the verdict + reasonings into prose.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Mapping, Sequence

from app.core.chart_model import Chart
from app.core.dignity import (
    dignity_state, is_debilitated, is_exalted, is_moolatrikona, is_own_sign,
)
from app.core.drishti_argala import (
    argala_for_bhava, planets_aspecting_bhava,
)
from app.core.functional_roles import functional_roles
from app.core.shadbala_report import compute_planet_shadbala
from app.core.yoga_library import active_yogas

# Natural karakas per bhava (BPHS Ch.6). 10H has the 4-karaka rule.
# Doctrine review correction (2026-05-29): Mercury removed from 4H — BPHS
# Ch.6.6 assigns Moon alone as 4H matr-karaka; Mercury is the 10H buddhi-
# karaka per Ch.6.32 "four-karaka rule", not a 4H signifier.
_BHAVA_KARAKAS: Final[Mapping[int, tuple[str, ...]]] = {
    1:  ("Sun",),
    2:  ("Jupiter",),
    3:  ("Mars",),
    4:  ("Moon",),                       # Mercury removed per doctrine review
    5:  ("Jupiter",),
    6:  ("Mars", "Saturn"),
    7:  ("Venus",),
    8:  ("Saturn",),
    9:  ("Jupiter", "Sun"),
    10: ("Sun", "Mercury", "Jupiter", "Saturn"),
    11: ("Jupiter",),
    12: ("Saturn", "Ketu"),
}

# Natural classification — locked per CLAUDE.md.
_NATURAL_BENEFICS: Final[frozenset[str]] = frozenset({
    "Jupiter", "Venus", "Mercury", "Moon",
})
_NATURAL_MALEFICS: Final[frozenset[str]] = frozenset({
    "Sun", "Mars", "Saturn", "Rahu", "Ketu",
})

# Which yogas, when active, *strengthen* specific bhava themes.
# Conservative: only the most direct mappings.
_YOGA_TO_BHAVA: Final[Mapping[str, tuple[int, ...]]] = {
    "Gajakesari":             (2, 5, 9, 10, 11),
    "Budha-Aditya":           (3, 5, 10),
    "Saraswati":              (2, 4, 5),
    "Amala":                  (10,),
    "Adhi":                   (1,),
    "Sunapha":                (2, 11),
    "Anapha":                 (12,),
    "Raja Yoga":              (1, 5, 9, 10),
    "Vipareeta Raja":         (1, 6, 8, 11, 12),
    "Ruchaka":                (1, 3, 6, 10),
    "Bhadra":                 (1, 4, 7, 10),
    "Hamsa":                  (1, 2, 5, 9, 10),
    "Malavya":                (1, 7),
    "Sasa":                   (1, 6, 10, 11),
    "Chandra-Mangal":         (2, 11),
    "Lakshmi":                (2, 9, 10, 11),
    "Neecha Bhanga Raja":     (1, 5, 9, 10),
    "Dharma-Karma Adhipati":  (9, 10),
}

# Yogas that signal AFFLICTION (lower score, not raise).
_YOGA_AFFLICTS: Final[Mapping[str, tuple[int, ...]]] = {
    "Kemadruma":     (1, 4),
    "Daridra":       (2, 11),
    "Mangal Dosha":  (1, 2, 4, 7, 8, 12),
    "Kala Sarpa":    (1, 5, 9),
}

_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONA: Final[frozenset[int]] = frozenset({1, 5, 9})
_DUSTHANA: Final[frozenset[int]] = frozenset({6, 8, 12})


@dataclass(frozen=True)
class Reasoning:
    """One reasoning step tied to its classical anchor."""
    finding: str
    weight: float            # signed: + favourable, − afflicting
    reference: str           # e.g. "BPHS Ch.10" or "Phaladeepika 6"


@dataclass(frozen=True)
class PillarScore:
    """Score + reasoning for one of the three pillars."""
    label: str               # "bhava" | "lord" | "karaka"
    score: float             # in [-1, +1]; >0 favourable, <0 afflicting
    reasonings: tuple[Reasoning, ...]


@dataclass(frozen=True)
class BhavaVerdict:
    """Composed verdict for one bhava on one chart."""
    bhava: int
    pillars: tuple[PillarScore, ...]
    composite_score: float
    label: str               # "strong" | "medium" | "weak" | "afflicted"
    confirming_yogas: tuple[str, ...]
    afflicting_yogas: tuple[str, ...]
    n_positive_pillars: int
    n_negative_pillars: int
    notes: tuple[str, ...] = ()


# ─── Pillar 1: Bhava itself ──────────────────────────────────────────


def _bhava_occupants(bhava: int, chart: Chart) -> tuple[str, ...]:
    """Planets sitting in this bhava (sorted)."""
    return chart.planets_in_house(bhava)


def _score_pillar_bhava(bhava: int, chart: Chart) -> PillarScore:
    """Pillar 1: who occupies this bhava + who aspects it.

    Benefics in own + aspecting → +.
    Malefics in own + aspecting → −.
    The dusthana (6/8/12) bhavas invert: malefics are *protective*.
    """
    reasonings: list[Reasoning] = []
    score = 0.0

    occupants = _bhava_occupants(bhava, chart)
    benefic_count = sum(1 for p in occupants if p in _NATURAL_BENEFICS)
    malefic_count = sum(1 for p in occupants if p in _NATURAL_MALEFICS)
    is_dusthana_bhava = bhava in _DUSTHANA

    if benefic_count:
        if is_dusthana_bhava:
            score -= 0.15 * benefic_count
            reasonings.append(Reasoning(
                finding=f"Benefic(s) {[p for p in occupants if p in _NATURAL_BENEFICS]} in dusthana {bhava}",
                weight=-0.15 * benefic_count,
                reference="BPHS Ch.10 — benefics in 6/8/12 lose force",
            ))
        else:
            score += 0.2 * benefic_count
            reasonings.append(Reasoning(
                finding=f"Benefic(s) {[p for p in occupants if p in _NATURAL_BENEFICS]} in bhava {bhava}",
                weight=0.2 * benefic_count,
                reference="BPHS Ch.10",
            ))

    if malefic_count:
        if is_dusthana_bhava:
            score += 0.15 * malefic_count
            reasonings.append(Reasoning(
                finding=f"Malefic(s) {[p for p in occupants if p in _NATURAL_MALEFICS]} in dusthana {bhava} (Vipareeta protection)",
                weight=0.15 * malefic_count,
                reference="BPHS Ch.10 — malefics fortify the dusthanas",
            ))
        else:
            score -= 0.2 * malefic_count
            reasonings.append(Reasoning(
                finding=f"Malefic(s) {[p for p in occupants if p in _NATURAL_MALEFICS]} in bhava {bhava}",
                weight=-0.2 * malefic_count,
                reference="BPHS Ch.10",
            ))

    # Aspects on the bhava
    aspectors = planets_aspecting_bhava(bhava, chart.planet_houses)
    benefic_aspect = [p for p in aspectors if p in _NATURAL_BENEFICS]
    malefic_aspect = [p for p in aspectors if p in _NATURAL_MALEFICS]
    if benefic_aspect:
        score += 0.1 * len(benefic_aspect)
        reasonings.append(Reasoning(
            finding=f"Benefic aspect(s) on bhava {bhava} from {benefic_aspect}",
            weight=0.1 * len(benefic_aspect),
            reference="BPHS Ch.26",
        ))
    if malefic_aspect:
        score -= 0.1 * len(malefic_aspect)
        reasonings.append(Reasoning(
            finding=f"Malefic aspect(s) on bhava {bhava} from {malefic_aspect}",
            weight=-0.1 * len(malefic_aspect),
            reference="BPHS Ch.26",
        ))

    return PillarScore(
        label="bhava", score=max(-1.0, min(1.0, score)),
        reasonings=tuple(reasonings),
    )


# ─── Pillar 2: Bhava lord ────────────────────────────────────────────


def _score_pillar_lord(bhava: int, chart: Chart) -> PillarScore:
    """Pillar 2: the bhava lord's strength + placement."""
    reasonings: list[Reasoning] = []
    score = 0.0

    roles = functional_roles(chart.asc_sign)
    lord = next(
        (p for p, r in roles.items() if bhava in r.houses_ruled), None,
    )
    if lord is None:
        return PillarScore(label="lord", score=0.0, reasonings=())

    lord_sign = chart.sign_of(lord)
    lord_house = chart.house_of(lord)

    # Dignity
    if lord_sign is not None:
        if is_exalted(lord, lord_sign):
            score += 0.4
            reasonings.append(Reasoning(
                finding=f"{lord} (bhava {bhava} lord) exalted",
                weight=0.4, reference="BPHS Ch.6",
            ))
        elif is_own_sign(lord, lord_sign) or is_moolatrikona(lord, lord_sign):
            score += 0.25
            reasonings.append(Reasoning(
                finding=f"{lord} (bhava {bhava} lord) in own/mooltrikona sign",
                weight=0.25, reference="BPHS Ch.6",
            ))
        elif is_debilitated(lord, lord_sign):
            score -= 0.4
            reasonings.append(Reasoning(
                finding=f"{lord} (bhava {bhava} lord) debilitated",
                weight=-0.4, reference="BPHS Ch.6",
            ))

    # Placement
    if lord_house is not None:
        if lord_house in _KENDRA or lord_house in _TRIKONA:
            score += 0.15
            cat = "Kendra" if lord_house in _KENDRA else "Trikona"
            reasonings.append(Reasoning(
                finding=f"{lord} placed in {cat} (h.{lord_house})",
                weight=0.15, reference="BPHS Ch.10",
            ))
        elif lord_house in _DUSTHANA:
            score -= 0.25
            reasonings.append(Reasoning(
                finding=f"{lord} placed in dusthana (h.{lord_house})",
                weight=-0.25, reference="BPHS Ch.10",
            ))

    # Shadbala threshold check
    try:
        shadbala = compute_planet_shadbala(lord, chart)
        if shadbala.is_sufficient:
            score += 0.15
            reasonings.append(Reasoning(
                finding=f"{lord} clears Shadbala threshold ({shadbala.pinda_rupa:.2f}/{shadbala.threshold_virupa/60:.2f} rupas)",
                weight=0.15, reference="BPHS Ch.27",
            ))
        else:
            score -= 0.1
            reasonings.append(Reasoning(
                finding=f"{lord} below Shadbala threshold ({shadbala.pinda_rupa:.2f}/{shadbala.threshold_virupa/60:.2f} rupas)",
                weight=-0.1, reference="BPHS Ch.27",
            ))
    except ValueError:
        pass  # Rahu/Ketu — no Shadbala

    # Functional role overlay
    lord_role = roles.get(lord)
    if lord_role:
        if lord_role.is_yogakaraka:
            score += 0.2
            reasonings.append(Reasoning(
                finding=f"{lord} is Yogakaraka for this Lagna",
                weight=0.2, reference="BPHS Ch.3",
            ))
        if lord_role.is_functional_malefic and bhava not in _DUSTHANA:
            score -= 0.1
            reasonings.append(Reasoning(
                finding=f"{lord} is a Functional Malefic for this Lagna",
                weight=-0.1, reference="Functional benefic/malefic doctrine",
            ))
        if lord_role.is_badhakesh:
            score -= 0.15
            reasonings.append(Reasoning(
                finding=f"{lord} is Badhakesh (obstruction lord) for this Lagna",
                weight=-0.15, reference="Phaladeepika — Badhakesh",
            ))

    return PillarScore(
        label="lord", score=max(-1.0, min(1.0, score)),
        reasonings=tuple(reasonings),
    )


# ─── Pillar 3: Karaka ────────────────────────────────────────────────


def _score_pillar_karaka(bhava: int, chart: Chart) -> PillarScore:
    """Pillar 3: natural karaka(s) of this bhava — dignity + placement."""
    reasonings: list[Reasoning] = []
    score = 0.0

    karakas = _BHAVA_KARAKAS.get(bhava, ())
    if not karakas:
        return PillarScore(label="karaka", score=0.0, reasonings=())

    per_karaka_score = 0.0
    for k in karakas:
        k_sign = chart.sign_of(k)
        k_house = chart.house_of(k)
        if k_sign is None:
            continue
        # Dignity
        if is_exalted(k, k_sign):
            per_karaka_score += 0.3
            reasonings.append(Reasoning(
                finding=f"Karaka {k} for bhava {bhava} exalted",
                weight=0.3, reference="BPHS Ch.6",
            ))
        elif is_debilitated(k, k_sign):
            per_karaka_score -= 0.3
            reasonings.append(Reasoning(
                finding=f"Karaka {k} for bhava {bhava} debilitated",
                weight=-0.3, reference="BPHS Ch.6",
            ))
        elif is_own_sign(k, k_sign) or is_moolatrikona(k, k_sign):
            per_karaka_score += 0.2
            reasonings.append(Reasoning(
                finding=f"Karaka {k} for bhava {bhava} in own sign",
                weight=0.2, reference="BPHS Ch.6",
            ))
        # Placement — afflicted dusthana for non-mortality-bhava karaka
        if k_house in _DUSTHANA and bhava not in {6, 8, 12}:
            per_karaka_score -= 0.15
            reasonings.append(Reasoning(
                finding=f"Karaka {k} placed in dusthana (h.{k_house})",
                weight=-0.15, reference="BPHS Ch.10",
            ))

    # Average across karakas — 10H's 4-karaka rule produces dampened scores.
    score = per_karaka_score / max(len(karakas), 1)
    return PillarScore(
        label="karaka", score=max(-1.0, min(1.0, score)),
        reasonings=tuple(reasonings),
    )


# ─── Composer ───────────────────────────────────────────────────────


def _yoga_overlay(
    bhava: int, chart: Chart,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (confirming yoga names, afflicting yoga names) for this bhava."""
    active = active_yogas(chart)
    conf = tuple(
        y.name for y in active
        if y.name in _YOGA_TO_BHAVA and bhava in _YOGA_TO_BHAVA[y.name]
    )
    affl = tuple(
        y.name for y in active
        if y.name in _YOGA_AFFLICTS and bhava in _YOGA_AFFLICTS[y.name]
    )
    return conf, affl


def _argala_overlay(bhava: int, chart: Chart) -> tuple[Reasoning, ...]:
    """Argala intervention reasonings for the focal bhava."""
    out: list[Reasoning] = []
    for src in argala_for_bhava(bhava, chart.planet_houses):
        if src.is_blocked or not src.causing_planets:
            continue
        benefic_causers = [p for p in src.causing_planets if p in _NATURAL_BENEFICS]
        malefic_causers = [p for p in src.causing_planets if p in _NATURAL_MALEFICS]
        if benefic_causers and not malefic_causers:
            out.append(Reasoning(
                finding=f"Benefic argala on bhava {bhava} from h.{src.argala_house} ({benefic_causers})",
                weight=0.1, reference="Jaimini Ch.4",
            ))
        elif malefic_causers and not benefic_causers:
            out.append(Reasoning(
                finding=f"Malefic argala on bhava {bhava} from h.{src.argala_house} ({malefic_causers})",
                weight=-0.1, reference="Jaimini Ch.4",
            ))
    return tuple(out)


def _label_from_score(
    composite: float, n_pos: int, n_neg: int,
    confirming: tuple[str, ...],
) -> str:
    """Apply the ≥3-confirmation AND-gate to label the verdict.

    Strong requires composite > 0.3 AND ≥2 positive pillars AND ≥1
    confirming yoga/argala. Weak/afflicted maps to negative composites.
    """
    if composite > 0.3 and n_pos >= 2 and confirming:
        return "strong"
    if composite < -0.3 and n_neg >= 2:
        return "afflicted"
    if composite > 0.1:
        return "medium"
    if composite < -0.1:
        return "weak"
    return "medium"


def judge_bhava(chart: Chart, bhava: int) -> BhavaVerdict:
    """The framework's core call: judge one bhava on one chart.

    Composes Phases 1 (functional roles), 2 (drishti + argala),
    3 (yogas), 4 (Shadbala), and Phase 5 (Chara) is NOT used here —
    Phase 7 (Gochara) is where temporal activation comes in. This
    judge produces the static-promise verdict.
    """
    if not 1 <= bhava <= 12:
        raise ValueError(f"bhava must be 1..12, got {bhava}")

    p_bhava = _score_pillar_bhava(bhava, chart)
    p_lord = _score_pillar_lord(bhava, chart)
    p_karaka = _score_pillar_karaka(bhava, chart)

    pillars = (p_bhava, p_lord, p_karaka)
    confirming, afflicting = _yoga_overlay(bhava, chart)
    argala_reasonings = _argala_overlay(bhava, chart)

    # Composite blends the three pillars (equal weight) + yoga overlay + argala.
    composite = (p_bhava.score + p_lord.score + p_karaka.score) / 3.0
    composite += 0.1 * len(confirming) - 0.1 * len(afflicting)
    composite += sum(r.weight for r in argala_reasonings)
    composite = max(-1.0, min(1.0, composite))

    n_positive = sum(1 for p in pillars if p.score > 0.1)
    n_negative = sum(1 for p in pillars if p.score < -0.1)

    label = _label_from_score(composite, n_positive, n_negative, confirming)
    notes = ()
    if not confirming and composite > 0.3:
        notes = (
            "Composite favourable but no confirming yoga/argala — "
            "downgraded to 'medium' per the ≥3-confirmation rule.",
        )

    # Re-pack pillars with argala reasonings appended to the bhava pillar
    enriched_bhava = PillarScore(
        label="bhava", score=p_bhava.score,
        reasonings=p_bhava.reasonings + argala_reasonings,
    )
    return BhavaVerdict(
        bhava=bhava,
        pillars=(enriched_bhava, p_lord, p_karaka),
        composite_score=composite,
        label=label,
        confirming_yogas=confirming,
        afflicting_yogas=afflicting,
        n_positive_pillars=n_positive,
        n_negative_pillars=n_negative,
        notes=notes,
    )


def judge_all_bhavas(chart: Chart) -> dict[int, BhavaVerdict]:
    """Judge all 12 bhavas on one chart — Phase 9 input."""
    return {b: judge_bhava(chart, b) for b in range(1, 13)}
