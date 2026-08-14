"""Birth moment → assembled natal chart, with honest nulls.

This module is pure assembly over ``app.empirical.western``: tropical
positions, house cusps, aspects, plus the chart-level derivations the decoder
needs (element/modality balance, chart ruler, dominant planets). It computes
nothing astronomical itself and never touches swisseph global state.

**The two honest nulls.** Houses can be missing for two different reasons and
the difference matters downstream:

* ``birth_time_unknown`` — the user has no birth time. Positions are cast at
  local noon (the convention that minimises the maximum error for the slow
  bodies), ``house_cusps`` is never called, and the Moon — which moves ~13° a
  day — is checked at both ends of the civil day: if its sign differs,
  ``moon_sign_ambiguous`` is True and every Moon-fed reading must say so.
* ``polar_latitude`` — a quadrant house system (Placidus, Koch, …) is
  undefined inside the polar circles. Following ``western.houses``, the miss
  is recorded and never papered over with a substituted system; the caller may
  explicitly choose ``whole_sign``, which is defined everywhere.

Usage:
    from app.empirical.natal.chart import BirthMoment, assemble_chart
    chart = assemble_chart(BirthMoment(1990, 7, 15, 12, 0, 12.97, 77.59, 5.5))
    chart.positions["Sun"].sign_index
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Mapping

from app.empirical.natal.lexicon import SIGN_RULERS, SIGNS
from app.empirical.western.aspects import Aspect, DEFAULT_ORBS, PTOLEMAIC, find_aspects
from app.empirical.western.houses import HouseCusps, house_cusps, house_of
from app.empirical.western.tropical import (
    DEFAULT_BODIES,
    Position,
    julian_day_ut,
    south_node_longitude,
    tropical_position,
    tropical_positions,
)

logger = logging.getLogger(__name__)

__all__ = [
    "BirthMoment",
    "NatalChart",
    "assemble_chart",
    "REASON_TIME_UNKNOWN",
    "REASON_POLAR",
    "BALANCE_WEIGHTS",
    "ASCENDANT_WEIGHT",
    "TRAIT_PLANETS",
]

REASON_TIME_UNKNOWN: Final[str] = "birth_time_unknown"
REASON_POLAR: Final[str] = "polar_latitude"

#: The ten trait-decoded planets, in the fixed iteration order. TrueNode is
#: computed and rendered but never trait-decoded (see ``lexicon``).
TRAIT_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
)

#: Element/modality balance weights. Luminaries and personal planets shape
#: temperament far more than the slow collective bodies, so they count double;
#: the node is excluded entirely. Pinned here so tests can assert the exact
#: arithmetic instead of a vibe.
BALANCE_WEIGHTS: Final[dict[str, int]] = {
    "Sun": 2, "Moon": 2, "Mercury": 2, "Venus": 2, "Mars": 2,
    "Jupiter": 1, "Saturn": 1, "Uranus": 1, "Neptune": 1, "Pluto": 1,
}

#: The rising sign's weight in the balance when houses are available.
ASCENDANT_WEIGHT: Final[int] = 2

_ELEMENT_KEYS: Final[tuple[str, ...]] = ("fire", "earth", "air", "water")
_MODALITY_KEYS: Final[tuple[str, ...]] = ("cardinal", "fixed", "mutable")


@dataclass(frozen=True, slots=True)
class BirthMoment:
    """A birth as the user states it — local clock time plus a fixed offset.

    Attributes:
      year..minute: Local civil date and clock time.
      latitude: Degrees, north positive.
      longitude: Degrees, east positive.
      tz_offset: Hours east of UTC (IST is +5.5). A fixed offset, not an IANA
        zone — matching ``app/api/report_routes.ReportRequest``.
      time_known: False when no birth time exists. The chart is then cast at
        local noon and everything time-derived (houses, ascendant, a precise
        Moon) is honestly absent or flagged.
    """

    year: int
    month: int
    day: int
    hour: int
    minute: int
    latitude: float
    longitude: float
    tz_offset: float
    time_known: bool = True

    @property
    def hour_local(self) -> float:
        """Decimal local clock hour actually used: noon when time is unknown."""
        if not self.time_known:
            return 12.0
        return self.hour + self.minute / 60.0

    @property
    def hour_ut(self) -> float:
        """Decimal UT hour. May fall outside [0, 24); ``swe.julday`` handles
        the day rollover arithmetically, so no manual date math is needed."""
        return self.hour_local - self.tz_offset


@dataclass(frozen=True, slots=True)
class NatalChart:
    """Everything computed about one birth, before any interpretation.

    Attributes:
      moment: The input.
      jd_ut: Julian Day (UT) the chart was cast for.
      positions: Tropical positions for :data:`DEFAULT_BODIES`.
      south_node: Derived south-node longitude.
      house_system: The system that was *requested*.
      houses: Cusps and angles, or ``None`` — see ``houses_missing_reason``.
      houses_missing_reason: ``birth_time_unknown`` | ``polar_latitude`` |
        ``None`` (houses present). Exactly one of ``houses`` /
        ``houses_missing_reason`` is ``None``.
      house_of_body: body → house 1..12; ``None`` exactly when houses are.
      aspects: Ptolemaic aspects under :data:`DEFAULT_ORBS`, all bodies.
      element_counts: Weighted fire/earth/air/water tallies.
      modality_counts: Weighted cardinal/fixed/mutable tallies.
      chart_ruler: Modern ruler of the rising sign; ``None`` without houses.
      dominant_planets: Top three by the documented score in
        :func:`_dominance_scores`.
      moon_sign_ambiguous: True only for unknown-time births whose Moon
        changes sign during the civil day.
    """

    moment: BirthMoment
    jd_ut: float
    positions: Mapping[str, Position]
    south_node: float
    house_system: str
    houses: HouseCusps | None
    houses_missing_reason: str | None
    house_of_body: Mapping[str, int] | None
    aspects: tuple[Aspect, ...]
    element_counts: Mapping[str, int]
    modality_counts: Mapping[str, int]
    chart_ruler: str | None
    dominant_planets: tuple[str, ...]
    moon_sign_ambiguous: bool


def _balance(
    positions: Mapping[str, Position],
    asc_sign_index: int | None,
) -> tuple[dict[str, int], dict[str, int]]:
    """Weighted element and modality tallies, all keys always present."""
    elements = {k: 0 for k in _ELEMENT_KEYS}
    modalities = {k: 0 for k in _MODALITY_KEYS}
    for body, weight in BALANCE_WEIGHTS.items():
        idx = positions[body].sign_index
        elements[_ELEMENT_KEYS[idx % 4]] += weight
        modalities[_MODALITY_KEYS[idx % 3]] += weight
    if asc_sign_index is not None:
        elements[_ELEMENT_KEYS[asc_sign_index % 4]] += ASCENDANT_WEIGHT
        modalities[_MODALITY_KEYS[asc_sign_index % 3]] += ASCENDANT_WEIGHT
    return elements, modalities


def _dominance_scores(
    positions: Mapping[str, Position],
    house_of_body: Mapping[str, int] | None,
    chart_ruler: str | None,
    aspects: tuple[Aspect, ...],
) -> dict[str, int]:
    """The documented additive dominance score.

    +2 chart ruler; +2 in an angular power house (1st or 10th); +1 in the
    other angular houses (4th or 7th); +1 per Ptolemaic aspect to a luminary
    (the other luminary, for the Sun and Moon themselves); +1 in domicile.
    House terms contribute nothing when houses are unavailable.
    """
    scores = {p: 0 for p in TRAIT_PLANETS}
    if chart_ruler in scores:
        scores[chart_ruler] += 2
    if house_of_body is not None:
        for planet in TRAIT_PLANETS:
            h = house_of_body[planet]
            if h in (1, 10):
                scores[planet] += 2
            elif h in (4, 7):
                scores[planet] += 1
    for asp in aspects:
        pair = {asp.body_a, asp.body_b}
        for planet in pair & set(TRAIT_PLANETS):
            if (pair - {planet}) & {"Sun", "Moon"}:
                scores[planet] += 1
    for planet in TRAIT_PLANETS:
        if SIGN_RULERS[SIGNS[positions[planet].sign_index]] == planet:
            scores[planet] += 1
    return scores


def _moon_sign_ambiguous(moment: BirthMoment) -> bool:
    """Whether the Moon changes sign between 00:00 and 24:00 local time."""
    jd_start = julian_day_ut(moment.year, moment.month, moment.day, 0.0 - moment.tz_offset)
    jd_end = julian_day_ut(moment.year, moment.month, moment.day, 24.0 - moment.tz_offset)
    return (
        tropical_position(jd_start, "Moon").sign_index
        != tropical_position(jd_end, "Moon").sign_index
    )


def assemble_chart(moment: BirthMoment, house_system: str = "placidus") -> NatalChart:
    """Cast and assemble the full natal chart for one birth.

    Raises:
      KeyError: unknown house system (propagated from ``western.houses``).
      ValueError: a calendar-invalid date that swisseph cannot place.
    """
    jd_ut = julian_day_ut(moment.year, moment.month, moment.day, moment.hour_ut)
    positions = tropical_positions(jd_ut, DEFAULT_BODIES)
    south_node = south_node_longitude(positions)

    houses: HouseCusps | None = None
    reason: str | None = None
    if not moment.time_known:
        reason = REASON_TIME_UNKNOWN
    else:
        houses = house_cusps(jd_ut, moment.latitude, moment.longitude, house_system)
        if houses is None:
            reason = REASON_POLAR

    house_map: dict[str, int] | None = None
    chart_ruler: str | None = None
    asc_sign_index: int | None = None
    if houses is not None:
        house_map = {
            body: house_of(pos.longitude, houses.cusps) for body, pos in positions.items()
        }
        asc_sign_index = int(houses.ascendant // 30.0)
        chart_ruler = SIGN_RULERS[SIGNS[asc_sign_index]]

    aspects = tuple(find_aspects(positions, orbs=DEFAULT_ORBS, aspects=PTOLEMAIC))
    elements, modalities = _balance(positions, asc_sign_index)

    scores = _dominance_scores(positions, house_map, chart_ruler, aspects)
    dominant = tuple(
        sorted(TRAIT_PLANETS, key=lambda p: (-scores[p], TRAIT_PLANETS.index(p)))[:3]
    )

    ambiguous = False if moment.time_known else _moon_sign_ambiguous(moment)

    return NatalChart(
        moment=moment,
        jd_ut=jd_ut,
        positions=positions,
        south_node=south_node,
        house_system=house_system,
        houses=houses,
        houses_missing_reason=reason,
        house_of_body=house_map,
        aspects=aspects,
        element_counts=elements,
        modality_counts=modalities,
        chart_ruler=chart_ruler,
        dominant_planets=dominant,
        moon_sign_ambiguous=ambiguous,
    )
