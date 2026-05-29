"""Desh-Kaal-Paristhiti modulation layer — Phase 8.

Wraps every prediction in context. Phases 1-7 produce *what the chart
says*; this layer says *what the chart says about THIS native NOW*.

## The 12-item checklist

Four questions per pillar:

**Desh (place):**
1. Birth latitude (Polar regions ≥66° invalid for whole-sign)
2. Birth longitude / timezone (sets Lagna precisely)
3. Current residence (home culture or diaspora?)
4. Climate Mahabhuta zone (Vata/Pitta/Kapha — modulates 6H/health readings)

**Kaal (time):**
5. Birth date (covers Yuga sub-period and ayanamsha)
6. Native's current age (Ashrama stage AND which bhava is life-relevant)
7. Active eclipse / Saturn-Jupiter mutation window at prediction date
8. Active dasha layer at prediction date (filled by Phase 5/Vimshottari)

**Paristhiti (circumstance):**
9. Ashrama stage (Brahmacharya / Grihastha / Vanaprastha / Sannyasa)
10. Marital status (single / married / widowed / divorced)
11. Profession / occupation domain
12. The specific Prashna asked (the question the reading answers)

Predictions with <8/12 populated are marked CONTEXT-INSUFFICIENT and
clarifying questions are surfaced.

## How modulation affects verdicts

The function ``apply_dkp_modulation`` takes a BhavaVerdict and a
DKPContext and returns a ``ModulatedVerdict`` with:
* The original verdict unchanged
* Context-derived emphasis (which bhava reading flavour is foreground)
* Confidence adjustment (LOW / MEDIUM / HIGH based on completeness + verdict strength)
* Clarifying questions when context insufficient
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Mapping

from app.core.bhava_judge import BhavaVerdict


class Ashrama(str):
    """The 4 life-stages of Vedic life. String-typed for serialisation."""
    BRAHMACHARYA = "brahmacharya"
    GRIHASTHA = "grihastha"
    VANAPRASTHA = "vanaprastha"
    SANNYASA = "sannyasa"


@dataclass(frozen=True)
class DKPContext:
    """The 12-field context input — all optional, completeness gates verdicts."""
    # Desh
    birth_latitude: float | None = None
    birth_longitude: float | None = None
    current_residence_country: str | None = None
    climate_mahabhuta: str | None = None  # vata/pitta/kapha
    # Kaal
    birth_date_iso: str | None = None
    age_years: float | None = None
    active_mundane_event: str | None = None  # e.g. "eclipse_in_progress"
    active_dasha_lord: str | None = None
    # Paristhiti
    ashrama: str | None = None
    marital_status: str | None = None  # single/married/widowed/divorced
    profession: str | None = None
    prashna: str | None = None


@dataclass(frozen=True)
class ModulatedVerdict:
    """A bhava verdict wrapped in DKP context."""
    underlying: BhavaVerdict
    confidence: str            # LOW / MEDIUM / HIGH
    context_completeness: int  # 0-12
    bhava_reading_focus: str   # which prediction flavour the context selects
    modulation_notes: tuple[str, ...]
    clarifying_questions: tuple[str, ...]


# Per-bhava reading-focus by Ashrama (BPHS Ch.5 — life-stage bhava emphasis).
_ASHRAMA_BHAVA_FOCUS: Final[Mapping[str, Mapping[int, str]]] = {
    Ashrama.BRAHMACHARYA: {  # student stage — emphasis on 2H/3H/4H/5H/9H
        2: "education-related material support",
        3: "self-effort and courage in learning",
        4: "parental support, schooling environment",
        5: "intellect, study, scholarship",
        7: "future relationships (not yet imminent)",
        9: "teacher, dharma instruction",
    },
    Ashrama.GRIHASTHA: {     # householder — emphasis on 2/4/5/7/10/11
        2: "wealth and family support",
        4: "home, residence, possessions",
        5: "children",
        7: "spouse and partnerships",
        10: "career and status",
        11: "income and gains",
    },
    Ashrama.VANAPRASTHA: {   # retired — emphasis on 8/9/12 + child-grandchild
        5: "grandchildren and lineage",
        8: "health and mortality concerns",
        9: "spiritual preparation",
        12: "moksha-orientation, foreign retreat",
    },
    Ashrama.SANNYASA: {      # renunciate — emphasis on 9/12
        9: "guru, ultimate dharma",
        12: "liberation, transcendence",
    },
}

# Per-bhava clarifying questions when context is insufficient for that bhava.
_BHAVA_CLARIFICATIONS: Final[Mapping[int, tuple[str, ...]]] = {
    1: ("What is the native's current vitality / general well-being?",),
    2: ("What is the native's current wealth/family-financial situation?",),
    4: ("Is the native's mother still living? What is the home situation?",),
    5: ("Does the native have children? At what life stage?",),
    7: ("What is the native's marital status?",),
    10: ("What is the native's profession or career domain?",),
    11: ("What income sources or major networks does the native rely on?",),
}


def context_completeness(ctx: DKPContext) -> int:
    """Count how many of the 12 fields are populated (not None)."""
    return sum(1 for v in (
        ctx.birth_latitude, ctx.birth_longitude,
        ctx.current_residence_country, ctx.climate_mahabhuta,
        ctx.birth_date_iso, ctx.age_years,
        ctx.active_mundane_event, ctx.active_dasha_lord,
        ctx.ashrama, ctx.marital_status,
        ctx.profession, ctx.prashna,
    ) if v is not None)


def _reading_focus_for_bhava(
    bhava: int, ctx: DKPContext,
) -> str:
    """What flavour of this bhava's reading is foregrounded for this native?"""
    if ctx.ashrama and ctx.ashrama in _ASHRAMA_BHAVA_FOCUS:
        focus_map = _ASHRAMA_BHAVA_FOCUS[ctx.ashrama]
        if bhava in focus_map:
            return focus_map[bhava]
    # Fallback: generic significations
    generic = {
        1: "self, vitality, body, identity",
        2: "wealth, family, voice",
        3: "siblings, courage, short journeys",
        4: "mother, home, comforts",
        5: "children, intellect, prior karma",
        6: "enemies, disease, debt, service",
        7: "spouse, partnerships, business",
        8: "longevity, transformation, hidden",
        9: "father, dharma, fortune, higher learning",
        10: "career, status, action",
        11: "gains, income, networks, elder siblings",
        12: "loss, expenditure, moksha, foreign",
    }
    return generic.get(bhava, "general affairs of this bhava")


def _confidence_label(
    completeness: int, verdict: BhavaVerdict,
) -> str:
    """LOW/MEDIUM/HIGH from completeness × verdict-strength composite."""
    if completeness < 6:
        return "LOW"
    if completeness < 9:
        if verdict.label in {"strong", "afflicted"}:
            return "MEDIUM"
        return "LOW"
    # completeness >= 9
    if verdict.label in {"strong", "afflicted"}:
        return "HIGH"
    return "MEDIUM"


def _modulation_notes(
    bhava: int, verdict: BhavaVerdict, ctx: DKPContext,
) -> tuple[str, ...]:
    """Per-context notes the Reading Composer should mention."""
    notes: list[str] = []
    if ctx.ashrama:
        focus = _reading_focus_for_bhava(bhava, ctx)
        notes.append(
            f"Ashrama={ctx.ashrama}: bhava {bhava} reads primarily as '{focus}'"
        )
    if ctx.age_years is not None:
        if bhava == 7 and ctx.age_years < 18:
            notes.append("Native is pre-adult — 7H marriage flavour deferred.")
        if bhava in {5} and ctx.age_years > 60:
            notes.append("Native is elder — 5H reads grandchildren/lineage flavour.")
        if bhava == 8 and ctx.age_years > 70:
            notes.append("Native is elder — 8H mortality theme elevated.")
    if ctx.active_mundane_event:
        notes.append(
            f"Active mundane condition: {ctx.active_mundane_event}. "
            "Predictions amplified during this window."
        )
    if ctx.marital_status:
        if bhava == 7 and ctx.marital_status in {"widowed", "divorced"}:
            notes.append(
                "Native's 7H promise has already manifested; reading focuses "
                "on re-partnership and aftermath rather than first marriage."
            )
    return tuple(notes)


def _clarifying_questions(
    bhava: int, ctx: DKPContext, completeness: int,
) -> tuple[str, ...]:
    """Which fields would lift confidence for this bhava?"""
    if completeness >= 9:
        return ()
    questions: list[str] = []
    if not ctx.ashrama:
        questions.append("What is the native's current life-stage / Ashrama?")
    if ctx.age_years is None:
        questions.append("What is the native's current age?")
    if bhava in _BHAVA_CLARIFICATIONS:
        questions.extend(_BHAVA_CLARIFICATIONS[bhava])
    if not ctx.prashna:
        questions.append("What is the specific question the native is asking?")
    return tuple(questions[:4])  # cap at 4


def apply_dkp_modulation(
    verdict: BhavaVerdict, ctx: DKPContext,
) -> ModulatedVerdict:
    """Wrap a bhava verdict in DKP context.

    The original verdict is preserved (verdict.underlying); the wrapper
    adds confidence labelling, reading-focus selection, contextual notes
    the Reading Composer will weave into prose, and clarifying questions
    when the context is insufficient.
    """
    completeness = context_completeness(ctx)
    confidence = _confidence_label(completeness, verdict)
    focus = _reading_focus_for_bhava(verdict.bhava, ctx)
    notes = _modulation_notes(verdict.bhava, verdict, ctx)
    questions = _clarifying_questions(verdict.bhava, ctx, completeness)
    return ModulatedVerdict(
        underlying=verdict,
        confidence=confidence,
        context_completeness=completeness,
        bhava_reading_focus=focus,
        modulation_notes=notes,
        clarifying_questions=questions,
    )
