"""BPHS dignity computation — Naisargika, Temporal, and Compound friendship.

This module is the *authority* for planetary dignity primitives that the
yoga catalog and Shadbala layers consume. It deliberately encodes only the
classical Parashara conventions:

- Own signs (sva-kshetra): BPHS 3.20
- Exaltation (uchcha) signs: BPHS 3.40 — single sign per planet
- Debilitation (neecha): exactly 6 signs (180°) from exaltation
- Naisargika friendship matrix: BPHS 3.55 — asymmetric for some pairs
- Temporal (situational) friendship: BPHS 3.56-57 — derived from chart positions
- Compound (Pancha-vidha) relation: BPHS 3.58 — combines the above

Sign indices are 1-indexed (1=Aries, 12=Pisces) to match the project-wide
convention used by ``app.core.ephemeris_engine``.

Rahu/Ketu inclusion follows the most-common modern BPHS extension
(Mantreshwara, Phaladeepika derivatives). Tradition varies; the table here
is conservative and easy to override by editing ``NAISARGIKA_FRIENDSHIP``.
"""
from __future__ import annotations

from typing import Literal, TypedDict

# --------------------------------------------------------------------------- #
# Sign-level constants                                                        #
# --------------------------------------------------------------------------- #

# Own signs (sva-kshetra) per BPHS 3.20. The luminaries own one sign each;
# the five star-planets own two each (one diurnal, one nocturnal).
OWN_SIGNS: dict[str, set[int]] = {
    "Sun":     {5},        # Leo
    "Moon":    {4},        # Cancer
    "Mars":    {1, 8},     # Aries, Scorpio
    "Mercury": {3, 6},     # Gemini, Virgo
    "Jupiter": {9, 12},    # Sagittarius, Pisces
    "Venus":   {2, 7},     # Taurus, Libra
    "Saturn":  {10, 11},   # Capricorn, Aquarius
}

# Exaltation (uchcha) signs per BPHS 3.40.
EXALTATION: dict[str, int] = {
    "Sun":     1,    # Aries
    "Moon":    2,    # Taurus
    "Mars":    10,   # Capricorn
    "Mercury": 6,    # Virgo
    "Jupiter": 4,    # Cancer
    "Venus":   12,   # Pisces
    "Saturn":  7,    # Libra
}

# Debilitation (neecha): 180° / 6 signs away from exaltation.
DEBILITATION: dict[str, int] = {
    planet: ((sign - 1 + 6) % 12) + 1
    for planet, sign in EXALTATION.items()
}

# Moolatrikona (root-trine) absolute-longitude ranges in degrees per BPHS 3.34.
# Within each planet's own-sign, a specific degree range carries the higher
# Moolatrikona status. Outside this range but still in the own-sign, the
# placement is "own non-MT".
#   Sun:     Leo 0–20°       → 120–140°
#   Moon:    Taurus 4–30°    → 34–60°
#   Mars:    Aries 0–12°     → 0–12°
#   Mercury: Virgo 16–20°    → 166–170°  (Virgo 20–30° is exaltation)
#   Jupiter: Sagittarius 0–10° → 240–250°
#   Venus:   Libra 0–15°     → 180–195°
#   Saturn:  Aquarius 0–20°  → 300–320°
# Rahu/Ketu: no classical Moolatrikona (omitted; is_moolatrikona returns False).
MOOLATRIKONA_RANGES: dict[str, tuple[float, float]] = {
    "Sun":     (120.0, 140.0),
    "Moon":    ( 34.0,  60.0),
    "Mars":    (  0.0,  12.0),
    "Mercury": (166.0, 170.0),
    "Jupiter": (240.0, 250.0),
    "Venus":   (180.0, 195.0),
    "Saturn":  (300.0, 320.0),
}

# Sign rulers — 1-indexed signs map to their owner from the seven lights.
SIGN_RULERS: dict[int, str] = {
    1: "Mars",     2: "Venus",   3: "Mercury", 4: "Moon",
    5: "Sun",      6: "Mercury", 7: "Venus",   8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


# --------------------------------------------------------------------------- #
# Naisargika (natural / innate) friendship                                    #
# --------------------------------------------------------------------------- #

class _Friendship(TypedDict):
    friends: set[str]
    neutrals: set[str]
    enemies: set[str]


NAISARGIKA_FRIENDSHIP: dict[str, _Friendship] = {
    "Sun": {
        "friends":  {"Moon", "Mars", "Jupiter"},
        "neutrals": {"Mercury"},
        "enemies":  {"Venus", "Saturn"},
    },
    "Moon": {
        "friends":  {"Sun", "Mercury"},
        "neutrals": {"Mars", "Jupiter", "Venus", "Saturn"},
        "enemies":  set(),
    },
    "Mars": {
        "friends":  {"Sun", "Moon", "Jupiter"},
        "neutrals": {"Venus", "Saturn"},
        "enemies":  {"Mercury"},
    },
    "Mercury": {
        "friends":  {"Sun", "Venus"},
        "neutrals": {"Mars", "Jupiter", "Saturn"},
        "enemies":  {"Moon"},
    },
    "Jupiter": {
        "friends":  {"Sun", "Moon", "Mars"},
        "neutrals": {"Saturn"},
        "enemies":  {"Mercury", "Venus"},
    },
    "Venus": {
        "friends":  {"Mercury", "Saturn"},
        "neutrals": {"Mars", "Jupiter"},
        "enemies":  {"Sun", "Moon"},
    },
    "Saturn": {
        "friends":  {"Mercury", "Venus"},
        "neutrals": {"Jupiter"},
        "enemies":  {"Sun", "Moon", "Mars"},
    },
    # Modern BPHS-derived extension for the lunar nodes. Sources: Mantreshwara,
    # Phaladeepika lineage. Several alternative conventions exist; this is the
    # most widely cited.
    "Rahu": {
        "friends":  {"Mercury", "Venus", "Saturn"},
        "neutrals": {"Jupiter"},
        "enemies":  {"Sun", "Moon", "Mars"},
    },
    "Ketu": {
        "friends":  {"Mars", "Venus", "Saturn"},
        "neutrals": {"Mercury", "Jupiter"},
        "enemies":  {"Sun", "Moon"},
    },
}

# Houses (counted from the other planet) that BPHS 3.56 designates as
# temporal-friend positions: 2nd, 3rd, 4th, 10th, 11th, 12th. All others
# (1st, 5th, 6th, 7th, 8th, 9th) are temporal-enemy.
_TEMPORAL_FRIEND_HOUSES: frozenset[int] = frozenset({2, 3, 4, 10, 11, 12})


# --------------------------------------------------------------------------- #
# Type aliases                                                                #
# --------------------------------------------------------------------------- #

NaisargikaRelation = Literal["friend", "neutral", "enemy", "own"]
TemporalRelation = Literal["friend", "enemy"]
CompoundRelation = Literal[
    "adhi_mitra", "mitra", "sama", "shatru", "adhi_shatru", "own"
]
DignityState = Literal[
    "exalted", "own", "debilitated", "friendly", "neutral", "inimical"
]

# Compound dignity state — extends DignityState with 5-tier compound
# friendship resolution (adhi_mitra > mitra > sama > shatru > adhi_shatru).
# Used by Phase-2 Saptavargaja-bala for finer-grained virupa scoring.
CompoundDignityState = Literal[
    "exalted", "own", "moolatrikona", "debilitated",
    "adhi_mitra", "mitra", "sama", "shatru", "adhi_shatru",
]


# --------------------------------------------------------------------------- #
# Public API — relationships                                                  #
# --------------------------------------------------------------------------- #

def naisargika_relation(p1: str, p2: str) -> NaisargikaRelation:
    """Return p1's natural (innate) view of p2.

    Asymmetric for several pairs — most famously Mars views Saturn as
    neutral, but Saturn views Mars as enemy. Self-pairs return ``"own"``.

    Raises ``ValueError`` for unknown planet names.
    """
    if p1 not in NAISARGIKA_FRIENDSHIP:
        raise ValueError(f"unknown planet: {p1!r}")
    if p2 not in NAISARGIKA_FRIENDSHIP:
        raise ValueError(f"unknown planet: {p2!r}")
    if p1 == p2:
        return "own"
    entry = NAISARGIKA_FRIENDSHIP[p1]
    if p2 in entry["friends"]:
        return "friend"
    if p2 in entry["neutrals"]:
        return "neutral"
    if p2 in entry["enemies"]:
        return "enemy"
    raise ValueError(
        f"planet {p2!r} missing from naisargika table for {p1!r}"
    )


def temporal_relation(chart: dict, p1: str, p2: str) -> TemporalRelation:
    """Return p1's situational view of p2 based on their chart positions.

    Counts whole-sign distance from p1's sign to p2's sign. Houses 2, 3, 4,
    10, 11, 12 from p1 confer ``"friend"``; houses 1, 5, 6, 7, 8, 9 confer
    ``"enemy"``. Per BPHS 3.56.

    ``chart`` is a mapping ``{planet_name: {"sign": int, ...}}``. The
    function reads only the ``sign`` field on each entry.
    """
    p1_entry = chart.get(p1)
    p2_entry = chart.get(p2)
    if not p1_entry or not p2_entry:
        raise ValueError(f"chart missing planet {p1!r} or {p2!r}")
    s1 = p1_entry.get("sign")
    s2 = p2_entry.get("sign")
    if not isinstance(s1, int) or not (1 <= s1 <= 12):
        raise ValueError(f"{p1!r} sign invalid: {s1!r}")
    if not isinstance(s2, int) or not (1 <= s2 <= 12):
        raise ValueError(f"{p2!r} sign invalid: {s2!r}")
    house_from_p1 = ((s2 - s1) % 12) + 1
    return "friend" if house_from_p1 in _TEMPORAL_FRIEND_HOUSES else "enemy"


def compound_relation(chart: dict, p1: str, p2: str) -> CompoundRelation:
    """Five-fold (Pancha-vidha) compound relation per BPHS 3.58.

    +-----------------+----------------+----------------+
    | Naisargika \\ T | Temporal Friend | Temporal Enemy |
    +=================+================+================+
    | friend          | adhi_mitra     | sama           |
    | neutral         | mitra          | shatru         |
    | enemy           | sama           | adhi_shatru    |
    +-----------------+----------------+----------------+

    Self-pairs return ``"own"``.
    """
    if p1 == p2:
        return "own"
    nais = naisargika_relation(p1, p2)
    if nais == "own":
        return "own"
    temp = temporal_relation(chart, p1, p2)
    match (nais, temp):
        case ("friend", "friend"):
            return "adhi_mitra"
        case ("friend", "enemy"):
            return "sama"
        case ("neutral", "friend"):
            return "mitra"
        case ("neutral", "enemy"):
            return "shatru"
        case ("enemy", "friend"):
            return "sama"
        case ("enemy", "enemy"):
            return "adhi_shatru"
        case _:  # pragma: no cover — Literal types exhaust the above.
            raise ValueError(
                f"unhandled compound input: naisargika={nais!r}, "
                f"temporal={temp!r}"
            )


# --------------------------------------------------------------------------- #
# Public API — dignity helpers                                                #
# --------------------------------------------------------------------------- #

def is_own_sign(planet: str, sign: int) -> bool:
    """True when ``planet`` occupies one of its own signs (sva-kshetra)."""
    return sign in OWN_SIGNS.get(planet, set())


def is_exalted(planet: str, sign: int) -> bool:
    """True when ``planet`` is in its exaltation sign (uchcha)."""
    return EXALTATION.get(planet) == sign


def is_debilitated(planet: str, sign: int) -> bool:
    """True when ``planet`` is in its debilitation sign (neecha)."""
    return DEBILITATION.get(planet) == sign


def is_moolatrikona(planet: str, longitude: float) -> bool:
    """True when ``planet`` is in its Moolatrikona (root-trine) range.

    Moolatrikona is a longitude-specific degree range within the planet's
    own sign that carries higher dignity than plain own-sign (45 virupa in
    Saptavargaja-bala vs 30 for plain own; per BPHS 27.19-22).

    Rahu/Ketu return ``False`` — no classical Moolatrikona assignment.
    """
    rng = MOOLATRIKONA_RANGES.get(planet)
    if rng is None:
        return False
    lon = longitude % 360.0
    return rng[0] <= lon < rng[1]


def dignity_state(planet: str, sign: int) -> DignityState:
    """Return ``planet``'s static dignity at ``sign``.

    Priority (highest first):

        exalted > own > debilitated > friendly > neutral > inimical

    ``friendly`` / ``neutral`` / ``inimical`` are inferred from the
    naisargika relation between the planet and the sign's ruler. The
    Moolatrikona range is intentionally omitted here — it depends on the
    exact degree within the sign and lives in the longitude-aware
    Shadbala layer.
    """
    if is_exalted(planet, sign):
        return "exalted"
    if is_own_sign(planet, sign):
        return "own"
    if is_debilitated(planet, sign):
        return "debilitated"
    ruler = SIGN_RULERS[sign]
    nais = naisargika_relation(planet, ruler)
    if nais == "friend":
        return "friendly"
    if nais == "enemy":
        return "inimical"
    return "neutral"


def dignity_state_compound(
    planet: str,
    sign: int,
    chart: dict,
    *,
    longitude: float | None = None,
) -> CompoundDignityState:
    """Return ``planet``'s compound dignity at ``sign`` given the full chart.

    Priority order (BPHS 27.18-22, full 9-tier):
        moolatrikona > own > exalted > debilitated >
        adhi_mitra > mitra > sama > shatru > adhi_shatru

    Compound tiers (adhi_mitra .. adhi_shatru) come from
    ``compound_relation(planet, sign_ruler, chart)``, which combines the
    naisargika friendship (innate) with the temporal friendship (chart-
    dependent). This is the canonical BPHS 27 5-tier resolution.

    ``longitude`` enables Moolatrikona detection; omit for sign-only
    callers who don't have the longitude handy.

    ``chart`` must include both the ``planet`` entry (at ``sign``) and
    the sign-ruler's entry, each carrying a ``sign`` field.
    """
    if longitude is not None and is_moolatrikona(planet, longitude):
        return "moolatrikona"
    if is_own_sign(planet, sign):
        return "own"
    if is_exalted(planet, sign):
        return "exalted"
    if is_debilitated(planet, sign):
        return "debilitated"
    ruler = SIGN_RULERS[sign]
    if planet == ruler:
        return "own"
    compound = compound_relation(chart, planet, ruler)
    if compound == "own":
        return "own"
    return compound  # type: ignore[return-value]


__all__ = [
    "OWN_SIGNS",
    "EXALTATION",
    "DEBILITATION",
    "MOOLATRIKONA_RANGES",
    "SIGN_RULERS",
    "NAISARGIKA_FRIENDSHIP",
    "NaisargikaRelation",
    "TemporalRelation",
    "CompoundRelation",
    "DignityState",
    "CompoundDignityState",
    "naisargika_relation",
    "temporal_relation",
    "compound_relation",
    "is_own_sign",
    "is_exalted",
    "is_debilitated",
    "is_moolatrikona",
    "dignity_state",
    "dignity_state_compound",
]
