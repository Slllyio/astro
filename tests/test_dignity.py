"""Tests for `app.core.dignity` — BPHS friendship & dignity computation.

References:
- Brihat Parashara Hora Shastra (BPHS), Adhyaya 3.
- Naisargika friendship table: BPHS 3.55.
- Temporal friendship: BPHS 3.56-57.
- Compound (Pancha-vidha) relation: BPHS 3.58.
"""
from __future__ import annotations

import pytest

from app.core.dignity import (
    DEBILITATION,
    EXALTATION,
    MOOLATRIKONA_RANGES,
    NAISARGIKA_FRIENDSHIP,
    OWN_SIGNS,
    SIGN_RULERS,
    compound_relation,
    dignity_state,
    dignity_state_compound,
    is_debilitated,
    is_exalted,
    is_moolatrikona,
    is_own_sign,
    naisargika_relation,
    temporal_relation,
)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _chart(positions: dict[str, int]) -> dict:
    """Minimal chart: {planet -> {"sign": int}} mapping."""
    return {p: {"sign": s} for p, s in positions.items()}


# Canonical BPHS 3.55 naisargika friendship for the seven lights.
NAISARGIKA_TABLE: list[tuple[str, set[str], set[str], set[str]]] = [
    ("Sun",     {"Moon", "Mars", "Jupiter"},
                {"Mercury"},
                {"Venus", "Saturn"}),
    ("Moon",    {"Sun", "Mercury"},
                {"Mars", "Jupiter", "Venus", "Saturn"},
                set()),
    ("Mars",    {"Sun", "Moon", "Jupiter"},
                {"Venus", "Saturn"},
                {"Mercury"}),
    ("Mercury", {"Sun", "Venus"},
                {"Mars", "Jupiter", "Saturn"},
                {"Moon"}),
    ("Jupiter", {"Sun", "Moon", "Mars"},
                {"Saturn"},
                {"Mercury", "Venus"}),
    ("Venus",   {"Mercury", "Saturn"},
                {"Mars", "Jupiter"},
                {"Sun", "Moon"}),
    ("Saturn",  {"Mercury", "Venus"},
                {"Jupiter"},
                {"Sun", "Moon", "Mars"}),
]


# --------------------------------------------------------------------------- #
# Naisargika (natural) friendship                                             #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("planet,friends,neutrals,enemies", NAISARGIKA_TABLE)
def test_naisargika_friends(
    planet: str, friends: set[str], neutrals: set[str], enemies: set[str]
) -> None:
    for f in friends:
        assert naisargika_relation(planet, f) == "friend", (planet, f)


@pytest.mark.parametrize("planet,friends,neutrals,enemies", NAISARGIKA_TABLE)
def test_naisargika_neutrals(
    planet: str, friends: set[str], neutrals: set[str], enemies: set[str]
) -> None:
    for n in neutrals:
        assert naisargika_relation(planet, n) == "neutral", (planet, n)


@pytest.mark.parametrize("planet,friends,neutrals,enemies", NAISARGIKA_TABLE)
def test_naisargika_enemies(
    planet: str, friends: set[str], neutrals: set[str], enemies: set[str]
) -> None:
    for e in enemies:
        assert naisargika_relation(planet, e) == "enemy", (planet, e)


def test_naisargika_self_returns_own() -> None:
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        assert naisargika_relation(p, p) == "own"


def test_naisargika_asymmetric_mars_saturn() -> None:
    """Canonical BPHS asymmetry: Mars views Saturn as neutral, but Saturn
    views Mars as enemy. Critical to preserve — many Vipareeta RY tests
    depend on this asymmetry."""
    assert naisargika_relation("Mars", "Saturn") == "neutral"
    assert naisargika_relation("Saturn", "Mars") == "enemy"


def test_naisargika_invalid_planet_raises() -> None:
    with pytest.raises(ValueError):
        naisargika_relation("Pluto", "Sun")
    with pytest.raises(ValueError):
        naisargika_relation("Sun", "Eris")


def test_naisargika_rahu_ketu_convention() -> None:
    """Modern BPHS-derived extension for the nodes. Documented in module."""
    assert naisargika_relation("Rahu", "Saturn") == "friend"
    assert naisargika_relation("Rahu", "Sun") == "enemy"
    assert naisargika_relation("Rahu", "Jupiter") == "neutral"
    assert naisargika_relation("Ketu", "Mars") == "friend"
    assert naisargika_relation("Ketu", "Moon") == "enemy"
    assert naisargika_relation("Ketu", "Mercury") == "neutral"


def test_friendship_table_covers_all_lights() -> None:
    """Each of the 7 lights must have its other 6 lights partitioned across
    friends/neutrals/enemies (no gaps, no duplicates)."""
    seven = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    for p in seven:
        entry = NAISARGIKA_FRIENDSHIP[p]
        union = entry["friends"] | entry["neutrals"] | entry["enemies"]
        assert union == seven - {p}, p
        # Disjoint
        assert (
            entry["friends"].isdisjoint(entry["neutrals"])
            and entry["friends"].isdisjoint(entry["enemies"])
            and entry["neutrals"].isdisjoint(entry["enemies"])
        ), p


# --------------------------------------------------------------------------- #
# Temporal (situational) friendship                                           #
# --------------------------------------------------------------------------- #

def test_temporal_friend_when_in_2nd() -> None:
    """Sun in Aries, Moon in Taurus (2nd from Sun) -> temporal friend."""
    chart = _chart({"Sun": 1, "Moon": 2})
    assert temporal_relation(chart, "Sun", "Moon") == "friend"
    # From Moon, Sun is in 12th (also a friend distance) -> friend.
    assert temporal_relation(chart, "Moon", "Sun") == "friend"


def test_temporal_enemy_when_same_sign() -> None:
    """Co-located planets are 1st from each other -> temporal enemy."""
    chart = _chart({"Sun": 5, "Mars": 5})
    assert temporal_relation(chart, "Sun", "Mars") == "enemy"
    assert temporal_relation(chart, "Mars", "Sun") == "enemy"


@pytest.mark.parametrize("friend_distance", [2, 3, 4, 10, 11, 12])
def test_temporal_friend_distances(friend_distance: int) -> None:
    """All six BPHS temporal-friend distances must yield 'friend'."""
    other_sign = ((1 - 1 + friend_distance - 1) % 12) + 1
    chart = _chart({"Sun": 1, "Moon": other_sign})
    assert temporal_relation(chart, "Sun", "Moon") == "friend"


@pytest.mark.parametrize("enemy_distance", [1, 5, 6, 7, 8, 9])
def test_temporal_enemy_distances(enemy_distance: int) -> None:
    """All six BPHS temporal-enemy distances must yield 'enemy'."""
    other_sign = ((1 - 1 + enemy_distance - 1) % 12) + 1
    chart = _chart({"Sun": 1, "Moon": other_sign})
    assert temporal_relation(chart, "Sun", "Moon") == "enemy"


def test_temporal_invalid_chart_raises() -> None:
    with pytest.raises(ValueError):
        temporal_relation({"Sun": {"sign": 1}}, "Sun", "Moon")
    with pytest.raises(ValueError):
        temporal_relation({"Sun": {}, "Moon": {"sign": 2}}, "Sun", "Moon")


# --------------------------------------------------------------------------- #
# Compound (Pancha-vidha) relation                                            #
# --------------------------------------------------------------------------- #

def test_compound_adhi_mitra() -> None:
    """Naisargika friend + temporal friend -> adhi_mitra (great friend)."""
    chart = _chart({"Sun": 1, "Moon": 2})  # Moon 2nd from Sun, naturally friend
    assert compound_relation(chart, "Sun", "Moon") == "adhi_mitra"


def test_compound_friend_plus_enemy_is_sama() -> None:
    """Naisargika friend + temporal enemy -> sama (neutral)."""
    chart = _chart({"Sun": 1, "Moon": 1})  # same sign, naturally friend
    assert compound_relation(chart, "Sun", "Moon") == "sama"


def test_compound_neutral_plus_friend_is_mitra() -> None:
    """Naisargika neutral + temporal friend -> mitra (friend)."""
    chart = _chart({"Sun": 1, "Mercury": 2})  # 2nd from Sun, naturally neutral
    assert compound_relation(chart, "Sun", "Mercury") == "mitra"


def test_compound_neutral_plus_enemy_is_shatru() -> None:
    chart = _chart({"Sun": 1, "Mercury": 1})  # same sign, neutral
    assert compound_relation(chart, "Sun", "Mercury") == "shatru"


def test_compound_enemy_plus_friend_is_sama() -> None:
    """Naisargika enemy + temporal friend -> sama."""
    chart = _chart({"Sun": 1, "Saturn": 2})  # Saturn 2nd from Sun, naturally enemy
    assert compound_relation(chart, "Sun", "Saturn") == "sama"


def test_compound_adhi_shatru() -> None:
    """Naisargika enemy + temporal enemy -> adhi_shatru (great enemy)."""
    chart = _chart({"Sun": 1, "Saturn": 1})
    assert compound_relation(chart, "Sun", "Saturn") == "adhi_shatru"


def test_compound_self_returns_own() -> None:
    chart = _chart({"Sun": 5})
    assert compound_relation(chart, "Sun", "Sun") == "own"


# --------------------------------------------------------------------------- #
# Dignity helpers (own / exalted / debilitated / state)                       #
# --------------------------------------------------------------------------- #

# (planet, own_signs, exaltation_sign, debilitation_sign)
DIGNITY_TABLE: list[tuple[str, set[int], int, int]] = [
    ("Sun",     {5},      1,  7),
    ("Moon",    {4},      2,  8),
    ("Mars",    {1, 8},  10,  4),
    ("Mercury", {3, 6},   6, 12),
    ("Jupiter", {9, 12},  4, 10),
    ("Venus",   {2, 7},  12,  6),
    ("Saturn",  {10, 11}, 7,  1),
]


@pytest.mark.parametrize("planet,owns,exalt,debil", DIGNITY_TABLE)
def test_is_own_sign_canonical(
    planet: str, owns: set[int], exalt: int, debil: int
) -> None:
    for s in owns:
        assert is_own_sign(planet, s) is True, (planet, s)
    # A sign not in owns must be False (use exaltation sign which is never own)
    if exalt not in owns:
        assert is_own_sign(planet, exalt) is False


@pytest.mark.parametrize("planet,owns,exalt,debil", DIGNITY_TABLE)
def test_is_exalted_canonical(
    planet: str, owns: set[int], exalt: int, debil: int
) -> None:
    assert is_exalted(planet, exalt) is True
    assert is_exalted(planet, debil) is False


@pytest.mark.parametrize("planet,owns,exalt,debil", DIGNITY_TABLE)
def test_is_debilitated_canonical(
    planet: str, owns: set[int], exalt: int, debil: int
) -> None:
    assert is_debilitated(planet, debil) is True
    assert is_debilitated(planet, exalt) is False


def test_debilitation_is_180_from_exaltation() -> None:
    """The debilitation sign is always exactly 6 signs (180°) from exaltation."""
    for p, exalt in EXALTATION.items():
        expected = ((exalt - 1 + 6) % 12) + 1
        assert DEBILITATION[p] == expected, p


def test_dignity_state_priority_exalted_over_friendly() -> None:
    """Exaltation outranks friendly-sign placement."""
    # Sun in Aries: exalted AND ruled by Mars (Sun's friend).
    # Must report 'exalted', not 'friendly'.
    assert dignity_state("Sun", 1) == "exalted"


def test_dignity_state_own() -> None:
    """Own sign reported as 'own' (not 'friendly' even if ruler is self)."""
    assert dignity_state("Sun", 5) == "own"
    assert dignity_state("Mars", 1) == "own"
    assert dignity_state("Mars", 8) == "own"


def test_dignity_state_debilitated() -> None:
    """Debilitation sign reported even when sign ruler is friend."""
    # Sun in Libra (7): debilitated; ruler Venus is Sun's enemy.
    assert dignity_state("Sun", 7) == "debilitated"
    # Jupiter in Capricorn (10): debilitated; ruler Saturn is Jupiter's neutral.
    assert dignity_state("Jupiter", 10) == "debilitated"


def test_dignity_state_friendly() -> None:
    """Sun in Pisces (12) — ruled by Jupiter (Sun's friend) — friendly."""
    assert dignity_state("Sun", 12) == "friendly"


def test_dignity_state_inimical() -> None:
    """Sun in Taurus (2) — ruled by Venus (Sun's enemy) — inimical."""
    assert dignity_state("Sun", 2) == "inimical"


def test_dignity_state_neutral() -> None:
    """Sun in Gemini (3) — ruled by Mercury (Sun's neutral) — neutral."""
    assert dignity_state("Sun", 3) == "neutral"


# --------------------------------------------------------------------------- #
# Sign rulers (sanity)                                                        #
# --------------------------------------------------------------------------- #

def test_sign_rulers_complete() -> None:
    """Every sign 1..12 has a ruler from the seven lights."""
    seven = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    for s in range(1, 13):
        assert SIGN_RULERS[s] in seven, s


# --------------------------------------------------------------------------- #
# Moolatrikona (BPHS 3.34) — Phase-1 audit fix                                #
# --------------------------------------------------------------------------- #

# (planet, longitude inside MT range, longitude in own-sign but outside MT)
MOOLATRIKONA_TABLE: list[tuple[str, float, float]] = [
    ("Sun",     130.0, 145.0),  # Leo 10° MT vs Leo 25° own
    ("Moon",     45.0,  33.0),  # Taurus 15° MT vs Taurus 3° own (just below MT 4°)
    ("Mars",      5.0,  20.0),  # Aries 5° MT vs Aries 20° own (MT ends at 12°)
    ("Mercury", 168.0, 175.0),  # Virgo 18° MT vs Virgo 25° (exaltation territory)
    ("Jupiter", 245.0, 255.0),  # Sgr 5° MT vs Sgr 15° own
    ("Venus",   190.0, 200.0),  # Libra 10° MT vs Libra 20° own
    ("Saturn",  310.0, 325.0),  # Aqu 10° MT vs Aqu 25° own
]


@pytest.mark.parametrize("planet,lon_in_mt,lon_outside_mt", MOOLATRIKONA_TABLE)
def test_is_moolatrikona_in_range(
    planet: str, lon_in_mt: float, lon_outside_mt: float
) -> None:
    """Longitudes inside each planet's MT range return True."""
    assert is_moolatrikona(planet, lon_in_mt), (planet, lon_in_mt)


@pytest.mark.parametrize("planet,lon_in_mt,lon_outside_mt", MOOLATRIKONA_TABLE)
def test_is_moolatrikona_outside_range(
    planet: str, lon_in_mt: float, lon_outside_mt: float
) -> None:
    """Longitudes outside MT range — even within the own-sign — return False."""
    assert not is_moolatrikona(planet, lon_outside_mt), (planet, lon_outside_mt)


def test_is_moolatrikona_nodes_always_false() -> None:
    """Rahu and Ketu have no classical Moolatrikona; always False."""
    for lon in (0.0, 45.0, 130.0, 250.0, 350.0):
        assert not is_moolatrikona("Rahu", lon)
        assert not is_moolatrikona("Ketu", lon)


def test_moolatrikona_ranges_match_bphs() -> None:
    """Spot-check the canonical BPHS 3.34 MT ranges."""
    assert MOOLATRIKONA_RANGES["Sun"] == (120.0, 140.0)   # Leo 0-20°
    assert MOOLATRIKONA_RANGES["Moon"] == (34.0, 60.0)    # Taurus 4-30°
    assert MOOLATRIKONA_RANGES["Mars"] == (0.0, 12.0)     # Aries 0-12°
    assert MOOLATRIKONA_RANGES["Mercury"] == (166.0, 170.0)  # Virgo 16-20°
    assert MOOLATRIKONA_RANGES["Jupiter"] == (240.0, 250.0)  # Sgr 0-10°
    assert MOOLATRIKONA_RANGES["Venus"] == (180.0, 195.0)    # Libra 0-15°
    assert MOOLATRIKONA_RANGES["Saturn"] == (300.0, 320.0)   # Aqu 0-20°


def test_is_moolatrikona_longitude_normalised() -> None:
    """Longitudes outside [0, 360) are normalised modulo 360."""
    # Sun MT range is [120, 140); 130 + 360 should still be in MT.
    assert is_moolatrikona("Sun", 130.0 + 360.0)
    # Negative longitudes also handled.
    assert is_moolatrikona("Sun", -230.0)  # -230 % 360 = 130


# --------------------------------------------------------------------------- #
# Compound dignity (BPHS 27.18-22, 5-tier resolution) — Phase 2               #
# --------------------------------------------------------------------------- #

def test_dignity_state_compound_exalted() -> None:
    """Exalted state takes priority regardless of compound friendships."""
    chart = _chart({"Sun": 1, "Mars": 5})  # Sun in Aries (exalted)
    assert dignity_state_compound("Sun", 1, chart) == "exalted"


def test_dignity_state_compound_own_priority() -> None:
    """Own-sign takes priority over exaltation (Mercury in Virgo)."""
    chart = _chart({"Mercury": 6, "Sun": 1})  # Mercury in Virgo (own AND exalted)
    # Own is listed before exalted in priority order per BPHS.
    assert dignity_state_compound("Mercury", 6, chart) == "own"


def test_dignity_state_compound_moolatrikona_with_longitude() -> None:
    """Moolatrikona detected when longitude provided + in MT range.
    Sun at Leo 10° (longitude 130°, within MT range 0-20°)."""
    chart = _chart({"Sun": 5, "Mars": 7})
    assert dignity_state_compound(
        "Sun", 5, chart, longitude=130.0
    ) == "moolatrikona"


def test_dignity_state_compound_debilitated() -> None:
    chart = _chart({"Sun": 7, "Venus": 1})  # Sun in Libra (debilitated)
    assert dignity_state_compound("Sun", 7, chart) == "debilitated"


def test_dignity_state_compound_adhi_mitra() -> None:
    """Sun in Pisces (Jupiter-ruled). Jupiter is Sun's naisargika friend.
    Place Jupiter in 2nd house from Sun (temporal friend too) → adhi_mitra."""
    # Sun in Pisces (12); Jupiter in Aries (1) = 2nd from Sun = temporal friend.
    chart = _chart({"Sun": 12, "Jupiter": 1})
    assert dignity_state_compound("Sun", 12, chart) == "adhi_mitra"


def test_dignity_state_compound_sama_from_friend_plus_enemy_temporal() -> None:
    """Sun in Pisces (Jupiter friend) with Jupiter co-located in Pisces
    (1st from Sun = temporal enemy) → naisargika-friend + temporal-enemy
    = sama (downgraded to neutral)."""
    chart = _chart({"Sun": 12, "Jupiter": 12})
    assert dignity_state_compound("Sun", 12, chart) == "sama"


def test_dignity_state_compound_adhi_shatru() -> None:
    """Sun in Taurus (Venus enemy), Venus also in Taurus (1st = temporal
    enemy) → adhi_shatru (great enemy)."""
    chart = _chart({"Sun": 2, "Venus": 2})
    assert dignity_state_compound("Sun", 2, chart) == "adhi_shatru"


def test_dignity_state_compound_returns_one_of_9_tiers() -> None:
    """Smoke: compound state is always one of the 9 documented tiers."""
    valid = {"exalted", "own", "moolatrikona", "debilitated",
             "adhi_mitra", "mitra", "sama", "shatru", "adhi_shatru"}
    chart = _chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                    "Jupiter": 9, "Venus": 7, "Saturn": 10})
    for planet, sign in chart.items():
        state = dignity_state_compound(planet, sign["sign"], chart)
        assert state in valid, (planet, state)
