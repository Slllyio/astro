"""Tier-0 primitive: interpretive reader for the five panchanga limbs.

Computes the natal panchanga (tithi/vara/nakshatra/yoga/karana) by
delegating to the canonical helpers in ``app.core.panchanga`` and
``app.core.nakshatra``, then emits one Finding per element with the
classical direction (positive/negative/neutral/mixed) layered in.

Doctrine choices encoded here:

| Limb       | Classical positive / negative tradition encoded |
|------------|-------------------------------------------------|
| Tithi      | Rikta tithis (4, 9, 14 in each paksha) and Amavasya (30) are negative. Purnima (15) and Shukla Panchami (5) are positive. Others neutral. |
| Vara       | Tuesday / Saturday / Sunday are malefic (Mars/Saturn/Sun) -> negative. Monday/Wednesday/Thursday/Friday are benefic (Moon/Mercury/Jupiter/Venus) -> positive. |
| Yoga       | Inauspicious yogas (Vishkambha, Atiganda, Shoola, Ganda, Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti) -> negative. Auspicious (Priti, Ayushman, Saubhagya, Shobhana, Sukarma, Dhriti, Vriddhi, Dhruva, Harshana, Siddhi, Variyana, Shiva, Siddha, Sadhya, Shubha, Shukla, Brahma, Indra) -> positive. |
| Karana     | Vishti (Bhadra) is universally inauspicious -> negative. The four fixed (Shakuni/Chatushpada/Naga/Kimstughna) traditionally apply to the lunar wane -> neutral. Movable benefics -> positive. |
| Nakshatra  | Direction is neutral here; the gandanta junction module already flags the afflictive boundary cases. |

The verdicts are human-readable, compact (well under the 140-char
schema limit) and explicit about paksha (Shukla / Krishna) for tithi.

Public API:
    ``read_panchanga(birth_jd, moon_lon, sun_lon, weekday) -> dict[str, Finding]``
"""
from __future__ import annotations

import logging
from typing import Final

from app.core.nakshatra import nakshatra_for_longitude
from app.core.panchanga import (
    KARANA_CHATUSHPADA,
    KARANA_KIMSTUGHNA,
    KARANA_NAGA,
    KARANA_SHAKUNI,
    PAKSHA_KRISHNA,
    PAKSHA_SHUKLA,
    TITHI_NAMES,
    VARA_NAMES,
    YOGA_NAMES,
    _karana_info,
    _tithi_info,
    _vara_info,
    _yoga_info,
)
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# 3-vote envelope (panchanga findings carry no 3-pillar judgment).
_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# Classical valence lookups.
# Tithi names that are universally read as inauspicious (in either paksha).
_NEGATIVE_TITHI_NAMES: Final[frozenset[str]] = frozenset(
    {
        "Chaturthi",   # 4 -- Rikta
        "Navami",      # 9 -- Rikta
        "Chaturdashi", # 14 -- Rikta
        "Amavasya",    # 30 -- new moon
    }
)
_POSITIVE_TITHI_NAMES: Final[frozenset[str]] = frozenset(
    {
        "Panchami",    # 5
        "Purnima",     # 15 -- full moon
    }
)


# Vara: 0=Sunday .. 6=Saturday per ``app.core.panchanga._vara_info``.
# Sun (0) / Tuesday (2) / Saturday (6) ruled by malefics.
_NEGATIVE_VARA_INDICES: Final[frozenset[int]] = frozenset({0, 2, 6})
# Monday (1) / Wednesday (3) / Thursday (4) / Friday (5) ruled by benefics.
_POSITIVE_VARA_INDICES: Final[frozenset[int]] = frozenset({1, 3, 4, 5})


# Inauspicious yogas (per Muhurta tradition).
_NEGATIVE_YOGA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "Vishkambha", "Atiganda", "Shoola", "Ganda",
        "Vyaghata", "Vajra", "Vyatipata", "Parigha", "Vaidhriti",
    }
)


# Karana: Vishti = inauspicious; the 4 fixed are neutral; movable
# karanas other than Vishti are auspicious in tradition.
_NEUTRAL_FIXED_KARANAS: Final[frozenset[str]] = frozenset(
    {KARANA_KIMSTUGHNA, KARANA_SHAKUNI, KARANA_CHATUSHPADA, KARANA_NAGA}
)


# ---------------------------------------------------------------------------
# Per-element finding builders
# ---------------------------------------------------------------------------


def _tithi_finding(sun_lon: float, moon_lon: float) -> Finding:
    info = _tithi_info(sun_lon, moon_lon)
    paksha = info["paksha"]
    name = info["name"]
    index = info["index"]  # 0..29
    tithi_num = index + 1  # 1..30 human-friendly

    if name in _POSITIVE_TITHI_NAMES:
        direction = "positive"
    elif name in _NEGATIVE_TITHI_NAMES:
        direction = "negative"
    else:
        direction = "neutral"

    return Finding(
        id="primitive.panchanga.tithi",
        rule="tithi",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=f"Born on {paksha} {name} (tithi {tithi_num})",
        evidence=[
            f"sun_lon={sun_lon:.4f}",
            f"moon_lon={moon_lon:.4f}",
            f"paksha={paksha}",
            f"tithi_index={index}",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def _vara_finding(birth_jd: float, weekday: int) -> Finding:
    if not 0 <= weekday <= 6:
        raise ValueError(f"weekday must be 0..6, got {weekday}")

    name = VARA_NAMES[weekday]
    if weekday in _POSITIVE_VARA_INDICES:
        direction = "positive"
    elif weekday in _NEGATIVE_VARA_INDICES:
        direction = "negative"
    else:  # never triggers — 0..6 partition exactly
        direction = "neutral"

    return Finding(
        id="primitive.panchanga.vara",
        rule="vara",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=f"Born on {name} (vara {weekday})",
        evidence=[f"jd={birth_jd:.4f}", f"weekday_index={weekday}"],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def _nakshatra_finding(moon_lon: float) -> Finding:
    info = nakshatra_for_longitude(moon_lon)
    name = info["name"]
    pada = info["pada"]
    lord = info["lord"]

    return Finding(
        id="primitive.panchanga.nakshatra",
        rule="nakshatra",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=f"Moon in {name} pada {pada} (lord {lord})",
        evidence=[
            f"moon_lon={moon_lon:.4f}",
            f"nakshatra_index={info['index']}",
            f"pada={pada}",
            f"lord={lord}",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def _yoga_finding(sun_lon: float, moon_lon: float) -> Finding:
    info = _yoga_info(sun_lon, moon_lon)
    name = info["name"]
    index = info["index"]  # 0..26

    direction = "negative" if name in _NEGATIVE_YOGA_NAMES else "positive"

    return Finding(
        id="primitive.panchanga.yoga",
        rule="yoga",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=f"Yoga {name} (panchanga yoga {index + 1})",
        evidence=[
            f"sun_lon={sun_lon:.4f}",
            f"moon_lon={moon_lon:.4f}",
            f"yoga_index={index}",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def _karana_finding(sun_lon: float, moon_lon: float) -> Finding:
    info = _karana_info(sun_lon, moon_lon)
    name = info["name"]
    index = info["index"]  # 0..59

    if name == "Vishti":
        direction = "negative"
    elif name in _NEUTRAL_FIXED_KARANAS:
        direction = "neutral"
    else:  # the other six movables (Bava, Balava, Kaulava, Taitila, Garaja, Vanija)
        direction = "positive"

    return Finding(
        id="primitive.panchanga.karana",
        rule="karana",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=f"Karana {name} (half-tithi {index + 1})",
        evidence=[
            f"sun_lon={sun_lon:.4f}",
            f"moon_lon={moon_lon:.4f}",
            f"karana_index={index}",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def read_panchanga(
    birth_jd: float,
    moon_lon: float,
    sun_lon: float,
    weekday: int,
) -> dict[str, Finding]:
    """Compute all five panchanga limbs and emit interpretive Findings.

    Args:
        birth_jd: Julian Day at birth (used for the vara evidence string;
            the weekday is supplied separately to avoid the caller having
            to recompute ``int(jd + 1.5) % 7``).
        moon_lon: Sidereal Lahiri Moon longitude in degrees [0, 360).
        sun_lon: Sidereal Lahiri Sun longitude in degrees [0, 360).
        weekday: 0..6 with 0=Sunday .. 6=Saturday, matching the formula
            in ``app.core.panchanga._vara_info``.

    Returns:
        A dict with exactly the five keys ``{"tithi", "vara", "nakshatra",
        "yoga", "karana"}``, each mapped to a
        ``primitive.panchanga.<element>`` Finding.

    Raises:
        ValueError: if ``weekday`` is not in 0..6.
    """
    return {
        "tithi": _tithi_finding(sun_lon, moon_lon),
        "vara": _vara_finding(birth_jd, weekday),
        "nakshatra": _nakshatra_finding(moon_lon),
        "yoga": _yoga_finding(sun_lon, moon_lon),
        "karana": _karana_finding(sun_lon, moon_lon),
    }


# Silence unused-import lint: TITHI_NAMES kept as an explicit export so
# downstream consumers can introspect the classical naming if needed
# without pulling in the private ``_tithi_info``.
__all__ = [
    "read_panchanga",
    "PAKSHA_SHUKLA",
    "PAKSHA_KRISHNA",
    "TITHI_NAMES",
    "YOGA_NAMES",
    "VARA_NAMES",
]
