"""Bhāvāt Bhāvam + Karaka chains — Gap J.

BPHS Ch.10 (and elaborated in Phaladeepika Ch.13): every bhava can be
read from its own position as the "Lagna" of a sub-chart. The 9th
house counted FROM the 9H gives the dharma's dharma (= 5H from natal
Lagna); the 5th house counted FROM the 7H gives the spouse's children
(= 11H from natal Lagna).

Beyond simple arithmetic, this technique gives:

1. **Recursive bhava analysis** — every bhava is the "1H" of its own
   12-bhava sub-system. Father (9H) has his own siblings (3rd-from-9H
   = 11H), career (10th-from-9H = 6H natal), etc.

2. **Karaka chains** — natural karakas (Sun for 1H, Moon for 4H,
   Jupiter for 5H/9H, etc.) themselves sit in some bhava. That bhava
   becomes the "context" for the karaka's reading. Sun in 10H = vitality
   through career; Sun in 4H = vitality through home.

3. **Bhāva-from-Moon** and **Bhāva-from-Sun** — Raman's twin-Lagna
   rule: every bhava reading should be cross-checked from Moon-as-Lagna
   (emotional reading) AND Sun-as-Lagna (vitality reading).

## Why this matters

The current bhava judge reads each bhava ONLY from natal Lagna. A
chart can have a strong 9H from Lagna but weak 9th-from-9H (= 5H),
meaning the dharma promise has shaky foundations. The judge can't see
that yet.

This module is a pure-arithmetic primitive — no doctrine ambiguity.
Downstream consumers compose readings using these primitives.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart


# Natural karakas per bhava — BPHS Ch.6.
# (Same as bhava_judge._BHAVA_KARAKAS but reproduced for module independence.)
_NATURAL_KARAKAS: Final[Mapping[int, tuple[str, ...]]] = {
    1:  ("Sun",),
    2:  ("Jupiter",),
    3:  ("Mars",),
    4:  ("Moon", "Mercury"),
    5:  ("Jupiter",),
    6:  ("Mars", "Saturn"),
    7:  ("Venus",),
    8:  ("Saturn",),
    9:  ("Jupiter", "Sun"),
    10: ("Sun", "Mercury", "Jupiter", "Saturn"),
    11: ("Jupiter",),
    12: ("Saturn", "Ketu"),
}


@dataclass(frozen=True)
class BhavaFromBhava:
    """Result of counting N houses from a base bhava."""
    base_bhava: int
    distance: int               # 1-12 inclusive
    derived_bhava: int          # 1-12, natal-Lagna-frame
    natural_karaka_of_derived: tuple[str, ...]
    interpretation_hint: str    # human-readable phrase


@dataclass(frozen=True)
class KarakaChain:
    """A natural karaka's placement chain.

    Example: for 1H (Tanu), the karaka is Sun. If Sun sits in 10H natally,
    then Sun-as-karaka delivers via 10H affairs.
    """
    bhava: int                  # the bhava whose karaka we're tracing
    karaka: str
    karaka_natal_house: int     # where the karaka sits in this chart
    chain_phrase: str           # e.g., "vitality (Sun) via career (10H)"


# Standard 12-bhava interpretation phrases — used to generate
# Bhāvat-Bhāvam hint text.
_BHAVA_PHRASES: Final[Mapping[int, str]] = {
    1:  "self / body / vitality",
    2:  "wealth / family / voice",
    3:  "siblings / courage / short journeys",
    4:  "mother / home / comforts",
    5:  "children / intellect / prior karma",
    6:  "enemies / disease / debt / service",
    7:  "spouse / partnerships / open enemies",
    8:  "longevity / transformation / hidden",
    9:  "father / dharma / fortune / higher learning",
    10: "career / status / action",
    11: "gains / income / networks / elder sibling",
    12: "loss / expenditure / moksha / foreign",
}

# Karaka domain phrases — for chain interpretation.
_KARAKA_PHRASES: Final[Mapping[str, str]] = {
    "Sun": "vitality / authority",
    "Moon": "emotional substrate / mother / public mind",
    "Mars": "energy / siblings / courage",
    "Mercury": "intellect / communication / commerce",
    "Jupiter": "wisdom / expansion / dharma / wealth",
    "Venus": "love / spouse / luxury / arts",
    "Saturn": "discipline / longevity / karma-yoga",
    "Rahu": "ambition / novelty / foreign",
    "Ketu": "renunciation / moksha / past karma",
}


def bhava_from_bhava(base_bhava: int, distance: int) -> BhavaFromBhava:
    """The Nth bhava counted from a base bhava (inclusive).

    Args:
        base_bhava: 1..12 — the starting bhava (counted as 1).
        distance: 1..12 — inclusive count forward.

    Returns:
        BhavaFromBhava with the derived bhava in natal-Lagna frame,
        its karakas, and a human-readable hint phrase.

    Example:
        9th-from-9H = bhava_from_bhava(9, 9) → derived=5
        "father's father / dharma's dharma → children / prior karma"
    """
    if not 1 <= base_bhava <= 12:
        raise ValueError(f"base_bhava must be 1..12, got {base_bhava}")
    if not 1 <= distance <= 12:
        raise ValueError(f"distance must be 1..12, got {distance}")
    derived = ((base_bhava - 1 + distance - 1) % 12) + 1
    karakas = _NATURAL_KARAKAS.get(derived, ())
    base_phrase = _BHAVA_PHRASES[base_bhava]
    derived_phrase = _BHAVA_PHRASES[derived]
    hint = (
        f"{distance}{_ord_suffix(distance)}-from-{base_bhava}H ({base_phrase}) "
        f"= {derived}H ({derived_phrase})"
    )
    return BhavaFromBhava(
        base_bhava=base_bhava, distance=distance,
        derived_bhava=derived, natural_karaka_of_derived=karakas,
        interpretation_hint=hint,
    )


def _ord_suffix(n: int) -> str:
    """Ordinal suffix: 1→'st', 2→'nd', 3→'rd', else 'th'."""
    if n % 100 in (11, 12, 13):
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def karaka_chains_for_bhava(bhava: int, chart: Chart) -> tuple[KarakaChain, ...]:
    """For the given bhava, trace each of its natural karakas to where
    they sit in the chart, producing the "karaka delivers via..." reading.

    Example:
        Cancer Lagna, asking about 1H (self/vitality).
        Karaka = Sun. If Sun sits in 10H natally:
        → KarakaChain(bhava=1, karaka="Sun",
                       karaka_natal_house=10,
                       chain_phrase="vitality / authority (Sun) via career / status (10H)")
    """
    if not 1 <= bhava <= 12:
        raise ValueError(f"bhava must be 1..12, got {bhava}")
    karakas = _NATURAL_KARAKAS.get(bhava, ())
    out: list[KarakaChain] = []
    for karaka in karakas:
        natal_house = chart.house_of(karaka)
        if natal_house is None:
            continue
        karaka_phrase = _KARAKA_PHRASES.get(karaka, karaka)
        house_phrase = _BHAVA_PHRASES.get(natal_house, f"{natal_house}H")
        chain = (
            f"{karaka_phrase} ({karaka}) "
            f"delivers via {house_phrase} ({natal_house}H)"
        )
        out.append(KarakaChain(
            bhava=bhava, karaka=karaka,
            karaka_natal_house=natal_house,
            chain_phrase=chain,
        ))
    return tuple(out)


def bhava_from_moon(natal_bhava: int, moon_house: int) -> int:
    """The same bhava read from Chandra Lagna (Moon-as-Lagna).

    Raman's twin-Lagna rule (Notable Horoscopes): every bhava reading
    should be cross-checked from Moon's position. Example: if Moon sits
    in natal 4H, then the natal 7H is the 4th-from-Moon = home/mother
    reading from emotional substrate.

    Args:
        natal_bhava: 1..12 — the bhava in natal-Lagna frame.
        moon_house: 1..12 — Moon's natal house.

    Returns:
        The same bhava expressed from Moon's frame (1..12).
    """
    if not (1 <= natal_bhava <= 12 and 1 <= moon_house <= 12):
        raise ValueError("natal_bhava and moon_house must be 1..12")
    # If Moon sits in house H natally, then natal bhava B is at distance
    # (B - H) % 12 + 1 from Moon (inclusive).
    return ((natal_bhava - moon_house) % 12) + 1


def bhava_from_sun(natal_bhava: int, sun_house: int) -> int:
    """Same as bhava_from_moon but anchored on Sun (vitality reading)."""
    if not (1 <= natal_bhava <= 12 and 1 <= sun_house <= 12):
        raise ValueError("natal_bhava and sun_house must be 1..12")
    return ((natal_bhava - sun_house) % 12) + 1


def triple_lagna_view(natal_bhava: int, chart: Chart) -> dict[str, int]:
    """Read a bhava simultaneously from Lagna, Chandra Lagna, Surya Lagna.

    Returns:
        {"from_lagna": int, "from_moon": int, "from_sun": int} — each
        is the bhava-equivalent in that frame.
    """
    moon_house = chart.house_of("Moon")
    sun_house = chart.house_of("Sun")
    out: dict[str, int] = {"from_lagna": natal_bhava}
    if moon_house is not None:
        out["from_moon"] = bhava_from_moon(natal_bhava, moon_house)
    if sun_house is not None:
        out["from_sun"] = bhava_from_sun(natal_bhava, sun_house)
    return out


# Common Bhāvāt Bhāvam relationships astrologers query.
COMMON_BHAVAT_BHAVAM: Final[tuple[tuple[int, int, str], ...]] = (
    (9, 9, "father's father / dharma's dharma → 5H natal"),
    (7, 7, "spouse's spouse → 1H natal (self via marriage)"),
    (4, 4, "mother's home / inherited dwelling → 7H natal"),
    (10, 10, "career's career / boss's boss → 7H natal"),
    (5, 5, "children's children (grandchildren) → 9H natal"),
    (11, 11, "elder sibling's elder sibling → 9H natal"),
    (9, 5, "father's intellect (5th from 9H) → 1H natal"),
    (7, 10, "spouse's career (10th from 7H) → 4H natal"),
    (10, 9, "career's dharma (9th from 10H) → 6H natal"),
    (4, 7, "mother's spouse (= father, 7th from 4H) → 10H natal"),
)


def common_chains() -> tuple[BhavaFromBhava, ...]:
    """Pre-computed common Bhāvāt Bhāvam relationships astrologers query."""
    return tuple(bhava_from_bhava(b, d) for b, d, _ in COMMON_BHAVAT_BHAVAM)
