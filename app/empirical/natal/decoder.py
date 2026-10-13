"""Deterministic chart → seven-facet trait decode.

Pure composition: every statement is looked up in the lexicon and carries its
source placement (so a reader can always answer "why does it say that?"), its
provenance tag, and machine-readable basis keys. No randomness, no model, no
hidden state — ``decode(chart) == decode(chart)`` is a tested invariant.

**Degradation contract.** When houses are unavailable (unknown birth time or a
polar-latitude quadrant system), house-derived statements are simply not
generated — never substituted — and each facet is marked ``degraded`` with a
note naming the reason. The facets stay non-empty regardless, because the
sign-level vocabulary is total (``tests/empirical/test_natal_lexicon.py``).

Usage:
    from app.empirical.natal.decoder import decode
    reading = decode(assemble_chart(moment))
    reading.facets[0].statements[0].text
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.empirical.natal.chart import (
    NatalChart,
    REASON_POLAR,
    REASON_TIME_UNKNOWN,
    TRAIT_PLANETS,
)
from app.empirical.natal.lexicon import (
    ELEMENT_TEMPERAMENT,
    ELEMENTS,
    FACETS,
    MODALITIES,
    MODALITY_TEMPERAMENT,
    PLANET_ROLES,
    SIGN_PROFILES,
    SIGNS,
    TRADITION_BANNER,
    WESTERN_TRADITION,
    aspect_meaning,
    planet_in_house,
    planet_in_sign,
)

__all__ = ["Statement", "FacetSection", "NatalDecode", "decode"]

_ORDINALS: Final[tuple[str, ...]] = (
    "1st", "2nd", "3rd", "4th", "5th", "6th",
    "7th", "8th", "9th", "10th", "11th", "12th",
)

#: Human phrasings for the two houses-missing reasons.
_REASON_NOTES: Final[dict[str, str]] = {
    REASON_TIME_UNKNOWN: (
        "Birth time unknown — the ascendant, houses and house-based statements "
        "are omitted rather than guessed; positions are cast at local noon."
    ),
    REASON_POLAR: (
        "The requested quadrant house system is undefined at this polar "
        "latitude — house-based statements are omitted rather than substituted; "
        "the whole-sign system remains available by explicit choice."
    ),
}

_MOON_NOTE: Final[str] = (
    "The Moon changes sign during this civil day; with the birth time unknown, "
    "Moon-based statements may belong to either sign."
)

_WORK_AREA_DEGRADED_NOTE: Final[str] = (
    "The vocational houses (2nd, 6th, 10th) are unavailable for this chart; "
    "only sign placements inform this section."
)


@dataclass(frozen=True, slots=True)
class Statement:
    """One decoded trait sentence with its full audit trail.

    Attributes:
      text: The reading itself.
      source: The placement in words, e.g. "Mercury in Gemini in the 3rd
        house (placidus)".
      provenance: Always :data:`WESTERN_TRADITION` — no statement escapes the
        banner.
      basis: Machine keys, e.g. ``("planet_sign:Mercury:Gemini",)``.
    """

    text: str
    source: str
    provenance: str
    basis: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FacetSection:
    """All statements for one facet, with its degradation status."""

    facet: str
    statements: tuple[Statement, ...]
    degraded: bool
    notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NatalDecode:
    """The complete decode: chart, the seven facets in fixed order, disclosures."""

    chart: NatalChart
    facets: tuple[FacetSection, ...]
    disclosures: tuple[str, ...]


class _Accumulator:
    """Collects statements per facet in deterministic insertion order."""

    def __init__(self) -> None:
        self._by_facet: dict[str, list[Statement]] = {f: [] for f in FACETS}

    def add(self, facet: str, text: str, source: str, basis: tuple[str, ...]) -> None:
        self._by_facet[facet].append(
            Statement(text=text, source=source, provenance=WESTERN_TRADITION, basis=basis)
        )

    def add_meanings(
        self,
        meanings: dict[str, tuple[str, ...]],
        source: str,
        basis: tuple[str, ...],
    ) -> None:
        for facet, phrases in meanings.items():
            self.add(facet, "; ".join(phrases), source, basis)

    def statements(self, facet: str) -> tuple[Statement, ...]:
        return tuple(self._by_facet[facet])


def _sign_of(chart: NatalChart, body: str) -> str:
    return SIGNS[chart.positions[body].sign_index]


def _dominant_key(counts: dict[str, int], order: tuple[str, ...]) -> str:
    """The highest-count key; ties break by the fixed zodiacal order."""
    return max(order, key=lambda k: (counts.get(k, 0), -order.index(k)))


def decode(chart: NatalChart) -> NatalDecode:
    """Decode an assembled chart into the seven facets. Deterministic."""
    acc = _Accumulator()
    has_houses = chart.houses is not None

    # Planet-in-sign for every trait planet, in the fixed order.
    for planet in TRAIT_PLANETS:
        sign = _sign_of(chart, planet)
        source = f"{planet} in {sign}"
        if has_houses:
            house = chart.house_of_body[planet]
            source = f"{planet} in {sign} in the {_ORDINALS[house - 1]} house ({chart.house_system})"
        acc.add_meanings(planet_in_sign(planet, sign), source, (f"planet_sign:{planet}:{sign}",))

    # Planet-in-house, only when houses exist.
    if has_houses:
        for planet in TRAIT_PLANETS:
            house = chart.house_of_body[planet]
            source = f"{planet} in the {_ORDINALS[house - 1]} house ({chart.house_system})"
            acc.add_meanings(planet_in_house(planet, house), source, (f"planet_house:{planet}:{house}",))

    # Aspects among trait planets (nodes computed but never trait-decoded).
    trait_set = set(TRAIT_PLANETS)
    for asp in chart.aspects:
        if asp.body_a not in trait_set or asp.body_b not in trait_set:
            continue
        source = f"{asp.body_a} {asp.aspect} {asp.body_b} (orb {asp.orb:.1f} deg)"
        basis = (f"aspect:{asp.body_a}:{asp.body_b}:{asp.aspect}",)
        acc.add_meanings(aspect_meaning(asp.body_a, asp.body_b, asp.aspect), source, basis)

    # Retrograde personal planets, noted factually (a computed fact, but the
    # inward-emphasis gloss is tradition, so it carries the same provenance).
    for planet in ("Mercury", "Venus", "Mars"):
        if chart.positions[planet].is_retrograde:
            role = PLANET_ROLES[planet]
            acc.add(
                "characteristics",
                f"{planet} is retrograde — the tradition reads {role.function} as turned inward, reviewed before expressed",
                f"{planet} retrograde",
                (f"retrograde:{planet}",),
            )

    # Chart-level: ascendant and ruler (houses only).
    if has_houses:
        asc_sign = SIGNS[int(chart.houses.ascendant // 30.0)]
        profile = SIGN_PROFILES[asc_sign]
        acc.add(
            "personality",
            f"presents to the world as {', '.join(profile.keywords[:3])}",
            f"Ascendant in {asc_sign}",
            (f"ascendant:{asc_sign}",),
        )
        ruler = chart.chart_ruler
        acc.add(
            "personality",
            f"the chart's ruler is {ruler} ({PLANET_ROLES[ruler].function}) — its placement in "
            f"{_sign_of(chart, ruler)} colours the whole presentation",
            f"chart ruler {ruler}",
            (f"chart_ruler:{ruler}",),
        )

    # Chart-level: element and modality temperament.
    lead_element = _dominant_key(dict(chart.element_counts), ELEMENTS)
    lead_modality = _dominant_key(dict(chart.modality_counts), MODALITIES)
    acc.add(
        "personality",
        f"the temperament {ELEMENT_TEMPERAMENT[lead_element]}",
        f"weighted element balance (leading: {lead_element})",
        (f"balance:element:{lead_element}",),
    )
    acc.add(
        "attitude",
        f"by mode, this chart {MODALITY_TEMPERAMENT[lead_modality]}",
        f"weighted modality balance (leading: {lead_modality})",
        (f"balance:modality:{lead_modality}",),
    )

    # Chart-level: dominant planets.
    dominants = ", ".join(
        f"{p} ({PLANET_ROLES[p].function})" for p in chart.dominant_planets
    )
    acc.add(
        "personality",
        f"the chart is led by {dominants}",
        "dominant planets (documented additive score)",
        tuple(f"dominant:{p}" for p in chart.dominant_planets),
    )

    # Assemble facet sections with the degradation contract.
    reason_note = _REASON_NOTES.get(chart.houses_missing_reason or "", None)
    sections: list[FacetSection] = []
    for facet in FACETS:
        notes: list[str] = []
        degraded = not has_houses
        if degraded and reason_note:
            notes.append(reason_note)
        if degraded and facet == "work_area":
            notes.append(_WORK_AREA_DEGRADED_NOTE)
        if chart.moon_sign_ambiguous and any(
            "Moon" in b for s in acc.statements(facet) for b in s.basis
        ):
            notes.append(_MOON_NOTE)
        sections.append(
            FacetSection(
                facet=facet,
                statements=acc.statements(facet),
                degraded=degraded,
                notes=tuple(notes),
            )
        )

    disclosures: list[str] = [TRADITION_BANNER]
    if reason_note:
        disclosures.append(reason_note)
    if chart.moon_sign_ambiguous:
        disclosures.append(_MOON_NOTE)

    return NatalDecode(chart=chart, facets=tuple(sections), disclosures=tuple(disclosures))
