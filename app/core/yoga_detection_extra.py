"""Extra yoga detectors — five missing or buggy yogas corrected/extended.

This module supplements ``app.core.yoga_library`` with detectors that were
either absent or doctrinally incorrect in the base library. Each detector
is fully self-contained: it takes a ``Chart``, applies the canonical rule,
and returns a frozen dataclass result.

Detectors implemented here:

1. ``detect_sarala_dignified`` — 8L in own/exalt/Mooltrikona *anywhere*.
   Distinct from the Vipareeta-Raja "Sarala" (8L in dusthana). Source:
   Phaladeepika Ch.6.27 / BPHS Ch.40 / Jataka Parijata Ch.10.

2. ``detect_chandra_mangala_extended`` — Moon-Mars conjunction OR mutual
   7th-sign aspect. The base library only detected conjunction.
   Source: Phaladeepika Ch.6.20.

3. ``detect_adhi_yoga_strict`` — ALL THREE of Mercury, Jupiter, Venus in
   houses 6/7/8 from Moon. The base ``yoga_library.detect_adhi`` fired on
   ANY single benefic, which is doctrinally wrong.
   Source: BPHS Ch.78.4-5 / Phaladeepika Ch.6.36.

4. ``detect_saraswati_yoga_extended`` — Mercury + Jupiter + Venus all in
   kendra/trikona/2H from LAGNA *or* from MOON, with Jupiter dignified.
   The base library only checked from Lagna.
   Source: Phaladeepika Ch.6.40.

5. ``detect_pushkara_navamsa`` — planets in Pushkara (auspicious) navamsa
   padas per the BV Raman/Phaladeepika table. Uses the D9 longitude from
   ``app.core.shodashavarga.compute_divisional_longitude``.

Usage:
    from app.core.yoga_detection_extra import (
        detect_sarala_dignified,
        detect_chandra_mangala_extended,
        detect_adhi_yoga_strict,
        detect_saraswati_yoga_extended,
        detect_pushkara_navamsa,
    )
    result = detect_sarala_dignified(chart)
    if result.active:
        print(result.eighth_lord, result.dignity)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart
from app.core.dignity import (
    EXALTATION,
    MOOLATRIKONA_RANGES,
    NAISARGIKA_FRIENDSHIP,
    OWN_SIGNS,
    is_exalted,
    is_moolatrikona,
    is_own_sign,
)
from app.core.shodashavarga import compute_divisional_longitude

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars",  2: "Venus",   3: "Mercury", 4: "Moon",
    5: "Sun",   6: "Mercury", 7: "Venus",   8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({1, 5, 9})
# Good houses for Saraswati: kendra + trikona + 2H.
_GOOD_HOUSES: Final[frozenset[int]] = _KENDRAS | _TRIKONAS | frozenset({2})

# Pushkara navamsa: BV Raman / Phaladeepika-aligned table.
# Keys are 1-based D1 sign numbers. Values are sets of 0-indexed pada numbers
# (0..8) that are auspicious for that sign.
# Rule: movable signs → padas 2 & 6 (1-indexed) = {1, 5} (0-indexed)
#       fixed signs   → padas 4 & 8 (1-indexed) = {3, 7}
#       dual signs    → padas 4 & 6 (1-indexed) = {3, 5}
_MOVABLE_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FIXED_SIGNS:   Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_DUAL_SIGNS:    Final[frozenset[int]] = frozenset({3, 6, 9, 12})

_PUSHKARA_PADAS: Final[Mapping[int, frozenset[int]]] = {
    sign: (
        frozenset({1, 5}) if sign in _MOVABLE_SIGNS
        else frozenset({3, 7}) if sign in _FIXED_SIGNS
        else frozenset({3, 5})
    )
    for sign in range(1, 13)
}

# All 9 grahas checked for Pushkara (7 visible + nodes).
_ALL_NINE: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
    "Rahu", "Ketu",
)

_NAVAMSA_SPAN: Final[float] = 30.0 / 9.0  # 3.333... degrees per pada


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SaralaDignifiedResult:
    """8th lord in own sign, exaltation, or Mooltrikona — anywhere in chart.

    Attributes:
        active: True iff the 8th lord satisfies at least one dignity condition.
        eighth_lord: Name of the 8th house lord for this Lagna.
        eighth_lord_sign: Sign the 8th lord actually occupies (1..12).
        dignity: Highest dignity attained: ``"exalted"`` | ``"mooltrikona"`` |
            ``"own"`` | ``""`` (inactive).
    """
    active: bool
    eighth_lord: str
    eighth_lord_sign: int
    dignity: str


@dataclass(frozen=True)
class ChandraMangalaResult:
    """Moon-Mars yoga via conjunction or mutual 7th-sign aspect.

    Attributes:
        active: True iff Moon and Mars are conjoined or opposing.
        mode: ``"conjunction"`` | ``"opposition"`` | ``""`` (inactive).
        moon_sign: Sign of Moon (1..12).
        mars_sign: Sign of Mars (1..12).
    """
    active: bool
    mode: str
    moon_sign: int
    mars_sign: int


@dataclass(frozen=True)
class AdhiYogaResult:
    """Strict Adhi Yoga — ALL THREE of Mercury, Jupiter, Venus in 6/7/8 from Moon.

    Attributes:
        active: True iff all three benefics are in the 6/7/8 from Moon.
        mercury_house_from_moon: Whole-sign house of Mercury from Moon (1..12).
        jupiter_house_from_moon: Whole-sign house of Jupiter from Moon (1..12).
        venus_house_from_moon: Whole-sign house of Venus from Moon (1..12).
    """
    active: bool
    mercury_house_from_moon: int
    jupiter_house_from_moon: int
    venus_house_from_moon: int


@dataclass(frozen=True)
class SaraswatiResult:
    """Saraswati Yoga — Mer + Jup + Ven all in kendra/trikona/2H from Lagna or Moon.

    Attributes:
        active: True iff the yoga fires from at least one axis.
        axis: Which axis triggered: ``"lagna"`` | ``"moon"`` | ``""`` (inactive).
            When both axes qualify, ``"lagna"`` is preferred.
        jupiter_dignity: Dignity of Jupiter when yoga is active:
            ``"exalted"`` | ``"moolatrikona"`` | ``"own"`` | ``"friend"`` | ``""``
            (inactive or not dignified).
    """
    active: bool
    axis: str
    jupiter_dignity: str


@dataclass(frozen=True)
class PushkaraResult:
    """Planets in Pushkara (auspicious) navamsa padas.

    Attributes:
        planets_in_pushkara: Tuple of planet names whose D1 pada is a Pushkara
            pada for their D1 sign type (sorted canonical order).
        details: One entry per Pushkara planet: (planet_name, d9_sign_1based,
            pada_index_0_8). The D9 sign is derived from
            ``compute_divisional_longitude(d1_lon, 9)``; pada is the 0-indexed
            position within the D1 sign's 9-pada sequence.
    """
    planets_in_pushkara: tuple[str, ...]
    details: tuple[tuple[str, int, int], ...]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _step_signs(from_sign: int, count: int) -> int:
    """Move ``count`` signs forward from ``from_sign`` (1-based, wraps at 12)."""
    return ((from_sign - 1 + count - 1) % 12) + 1


def _eighth_house_sign(asc_sign: int) -> int:
    """Return the 1-based zodiac sign of the 8th house from ``asc_sign``."""
    return _step_signs(asc_sign, 8)


def _house_from(reference_sign: int, planet_sign: int) -> int:
    """Whole-sign house of ``planet_sign`` counted from ``reference_sign``."""
    return ((planet_sign - reference_sign) % 12) + 1


def _jupiter_dignity(chart: Chart) -> str:
    """Return Jupiter's highest-priority dignity label for Saraswati check.

    Priority: exalted > moolatrikona > own > friend-sign > "".
    "friend-sign" means Jupiter is in a sign whose lord is Jupiter's
    natural (naisargika) friend.
    """
    jup_sign = chart.sign_of("Jupiter")
    jup_lon = chart.planet_lons.get("Jupiter")
    if jup_sign is None:
        return ""
    if is_exalted("Jupiter", jup_sign):
        return "exalted"
    if jup_lon is not None and is_moolatrikona("Jupiter", jup_lon):
        return "moolatrikona"
    if is_own_sign("Jupiter", jup_sign):
        return "own"
    # Friendly sign: the sign's lord is among Jupiter's natural friends.
    sign_lord = _SIGN_LORDS[jup_sign]
    if sign_lord in NAISARGIKA_FRIENDSHIP["Jupiter"]["friends"]:
        return "friend"
    return ""


def _all_in_good_houses_from(
    reference_sign: int, chart: Chart, planets: tuple[str, ...]
) -> bool:
    """True iff every planet in ``planets`` is in a good house from ``reference_sign``.

    Good houses: _GOOD_HOUSES = {1, 2, 4, 5, 7, 9, 10}.
    """
    for p in planets:
        p_sign = chart.sign_of(p)
        if p_sign is None:
            return False
        if _house_from(reference_sign, p_sign) not in _GOOD_HOUSES:
            return False
    return True


# ---------------------------------------------------------------------------
# Detector 1: Sarala Dignified
# ---------------------------------------------------------------------------

def detect_sarala_dignified(chart: Chart) -> SaralaDignifiedResult:
    """Detect Sarala (dignified variant) — 8L in own sign, exaltation, or Mooltrikona.

    This is the *auspicious* form of Sarala yoga (8L strong anywhere),
    distinct from the Vipareeta-Raja Sarala in ``yoga_library.py`` (8L
    in a dusthana). References: Phaladeepika Ch.6.27, BPHS Ch.40,
    Jataka Parijata Ch.10. Confers secret wisdom, longevity, and the
    ability to escape death-blows.

    Args:
        chart: Populated ``Chart`` with at least the 8H lord's sign and
            longitude. Raises ``ValueError`` if 8H lord absent.

    Returns:
        ``SaralaDignifiedResult`` with active flag, lord name, sign, and
        dignity label.
    """
    eighth_sign = _eighth_house_sign(chart.asc_sign)
    eighth_lord = _SIGN_LORDS[eighth_sign]
    lord_sign = chart.sign_of(eighth_lord)
    lord_lon = chart.planet_lons.get(eighth_lord)

    if lord_sign is None:
        raise ValueError(
            f"chart missing sign for 8H lord {eighth_lord!r} "
            f"(8H sign={eighth_sign})"
        )

    if is_exalted(eighth_lord, lord_sign):
        dignity = "exalted"
    elif lord_lon is not None and is_moolatrikona(eighth_lord, lord_lon):
        dignity = "moolatrikona"
    elif is_own_sign(eighth_lord, lord_sign):
        dignity = "own"
    else:
        dignity = ""

    active = bool(dignity)
    logger.debug(
        "SaralaDignified: 8H=%d 8L=%s sign=%d lon=%s dignity=%r active=%s",
        eighth_sign, eighth_lord, lord_sign, lord_lon, dignity, active,
    )
    return SaralaDignifiedResult(
        active=active,
        eighth_lord=eighth_lord,
        eighth_lord_sign=lord_sign,
        dignity=dignity,
    )


# ---------------------------------------------------------------------------
# Detector 2: Chandra-Mangala Extended
# ---------------------------------------------------------------------------

def detect_chandra_mangala_extended(chart: Chart) -> ChandraMangalaResult:
    """Chandra-Mangala Yoga — Moon-Mars conjunction OR mutual 7th-sign aspect.

    The base ``yoga_library.detect_chandra_mangal`` only fires on conjunction.
    This detector also recognises the mutual 7th aspect (Moon and Mars in
    whole-sign opposition — each is in the 7th sign from the other).
    Reference: Phaladeepika Ch.6.20.

    Args:
        chart: Populated ``Chart`` with Moon and Mars positions.

    Returns:
        ``ChandraMangalaResult`` carrying mode and sign data.
    """
    moon_sign = chart.sign_of("Moon")
    mars_sign = chart.sign_of("Mars")

    if moon_sign is None or mars_sign is None:
        return ChandraMangalaResult(
            active=False, mode="", moon_sign=moon_sign or 0, mars_sign=mars_sign or 0,
        )

    if moon_sign == mars_sign:
        mode = "conjunction"
    elif _house_from(moon_sign, mars_sign) == 7:
        # Mutual 7th: each sign is exactly 7 forward from the other.
        mode = "opposition"
    else:
        mode = ""

    active = bool(mode)
    logger.debug(
        "ChandraMangalaExt: moon=%d mars=%d mode=%r active=%s",
        moon_sign, mars_sign, mode, active,
    )
    return ChandraMangalaResult(
        active=active, mode=mode, moon_sign=moon_sign, mars_sign=mars_sign,
    )


# ---------------------------------------------------------------------------
# Detector 3: Adhi Yoga (strict — all three benefics required)
# ---------------------------------------------------------------------------

def detect_adhi_yoga_strict(chart: Chart) -> AdhiYogaResult:
    """Strict Adhi Yoga — ALL of Mercury, Jupiter, Venus in 6/7/8 from Moon.

    The canonical rule per BPHS Ch.78.4-5 and Phaladeepika Ch.6.36 requires
    *all three* natural benefics (Mercury, Jupiter, Venus) to be in houses
    6, 7, or 8 from Moon (in any combination of those three houses). The
    base ``yoga_library.detect_adhi`` fires on any single benefic, which is
    a significant doctrinal error — it would trigger even with one benefic
    in the 6th.

    Args:
        chart: Populated ``Chart`` with Moon, Mercury, Jupiter, Venus positions.

    Returns:
        ``AdhiYogaResult`` with the three house-from-moon values and active flag.

    Raises:
        ValueError: If Moon is absent from the chart.
    """
    moon_sign = chart.sign_of("Moon")
    if moon_sign is None:
        raise ValueError("chart missing Moon sign — Adhi Yoga cannot be computed")

    _adhi_set: Final[frozenset[int]] = frozenset({6, 7, 8})

    def _h(planet: str) -> int:
        s = chart.sign_of(planet)
        if s is None:
            return 0
        return _house_from(moon_sign, s)

    mer_h = _h("Mercury")
    jup_h = _h("Jupiter")
    ven_h = _h("Venus")

    active = (
        mer_h in _adhi_set
        and jup_h in _adhi_set
        and ven_h in _adhi_set
    )
    logger.debug(
        "AdhiStrict: moon=%d mer_h=%d jup_h=%d ven_h=%d active=%s",
        moon_sign, mer_h, jup_h, ven_h, active,
    )
    return AdhiYogaResult(
        active=active,
        mercury_house_from_moon=mer_h,
        jupiter_house_from_moon=jup_h,
        venus_house_from_moon=ven_h,
    )


# ---------------------------------------------------------------------------
# Detector 4: Saraswati Yoga Extended (from Lagna OR Moon)
# ---------------------------------------------------------------------------

def detect_saraswati_yoga_extended(chart: Chart) -> SaraswatiResult:
    """Saraswati Yoga — Mer + Jup + Ven in kendra/trikona/2H, Jupiter dignified.

    Extends the base ``yoga_library.detect_saraswati`` (which only checks
    house numbers from Lagna) by also examining the Moon-centred axis.
    Phaladeepika Ch.6.40 permits both reference points. Jupiter must be in
    own/friend/exaltation for the yoga to materialise; we extend the base
    library's own/exalt check to include friendly signs.

    Activation priority: Lagna axis is checked first; if active, ``axis``
    returns ``"lagna"`` even if the Moon axis would also qualify.

    Args:
        chart: Populated ``Chart`` with Lagna sign, Moon, Mercury, Jupiter,
            Venus positions.

    Returns:
        ``SaraswatiResult`` with active flag, triggering axis, and Jupiter
        dignity label.
    """
    jup_dignity = _jupiter_dignity(chart)
    jup_dignified = bool(jup_dignity)

    _trio: Final[tuple[str, ...]] = ("Mercury", "Jupiter", "Venus")

    # Check from Lagna (house numbers from chart.asc_sign).
    from_lagna = _all_in_good_houses_from(chart.asc_sign, chart, _trio)

    if from_lagna and jup_dignified:
        logger.debug(
            "SaraswatiExt: active from lagna=%d jup_dignity=%r",
            chart.asc_sign, jup_dignity,
        )
        return SaraswatiResult(active=True, axis="lagna", jupiter_dignity=jup_dignity)

    # Check from Moon (house distance from Moon's sign).
    moon_sign = chart.sign_of("Moon")
    if moon_sign is not None:
        from_moon = _all_in_good_houses_from(moon_sign, chart, _trio)
        if from_moon and jup_dignified:
            logger.debug(
                "SaraswatiExt: active from moon=%d jup_dignity=%r",
                moon_sign, jup_dignity,
            )
            return SaraswatiResult(
                active=True, axis="moon", jupiter_dignity=jup_dignity,
            )

    logger.debug("SaraswatiExt: inactive")
    return SaraswatiResult(active=False, axis="", jupiter_dignity="")


# ---------------------------------------------------------------------------
# Detector 5: Pushkara Navamsa
# ---------------------------------------------------------------------------

def detect_pushkara_navamsa(chart: Chart) -> PushkaraResult:
    """Detect planets in Pushkara (auspicious) navamsa padas.

    Uses the BV Raman / Phaladeepika-aligned table that classifies
    auspicious navamsa padas by D1 sign modality:

    * Movable signs (Aries, Cancer, Libra, Capricorn): padas 2 & 6
      (1-indexed) = indices 1 & 5 (0-indexed).
    * Fixed signs (Taurus, Leo, Scorpio, Aquarius): padas 4 & 8 = {3, 7}.
    * Dual signs (Gemini, Virgo, Sagittarius, Pisces): padas 4 & 6 = {3, 5}.

    The pada index (0-indexed, 0..8) is computed from the D1 longitude:
    ``int((d1_lon % 30) / (30 / 9))``.

    ``compute_divisional_longitude(d1_lon, 9)`` is also called to obtain
    the D9 sign number, which is stored in the ``details`` tuple for
    downstream interpretation.

    Checks all 9 grahas (7 visible planets plus Rahu and Ketu).

    Args:
        chart: Populated ``Chart`` with longitudes for all 9 grahas.

    Returns:
        ``PushkaraResult`` with the sorted tuple of Pushkara planet names
        and a ``details`` tuple of ``(planet, d9_sign_1based, pada_index)``.
    """
    pushkara: list[str] = []
    details: list[tuple[str, int, int]] = []

    for planet in _ALL_NINE:
        lon = chart.planet_lons.get(planet)
        if lon is None:
            continue

        lon = lon % 360.0
        d1_sign_0based = int(lon // 30)
        d1_sign_1based = d1_sign_0based + 1
        degree_in_d1_sign = lon - d1_sign_0based * 30.0

        pada = int(degree_in_d1_sign / _NAVAMSA_SPAN)
        if pada > 8:
            pada = 8  # clamp floating-point boundary

        pushkara_padas = _PUSHKARA_PADAS[d1_sign_1based]

        # D9 sign for the detail record.
        try:
            d9_lon = compute_divisional_longitude(lon, 9)
            d9_sign_1based = int(d9_lon // 30) % 12 + 1
        except Exception:  # pragma: no cover — engine guard
            d9_sign_1based = 0

        logger.debug(
            "Pushkara: %s lon=%.2f d1_sign=%d pada=%d pushkara_padas=%s d9_sign=%d",
            planet, lon, d1_sign_1based, pada, pushkara_padas, d9_sign_1based,
        )

        if pada in pushkara_padas:
            pushkara.append(planet)
            details.append((planet, d9_sign_1based, pada))

    return PushkaraResult(
        planets_in_pushkara=tuple(pushkara),
        details=tuple(details),
    )
