"""KP sub table: the 249 sign/star/sub divisions of the zodiac.

Krishnamurti divides each of the 27 constellations (13°20') into nine subs in
the proportion of the Vimshottari dasa years, starting from the star lord's
own sub and continuing in dasa order (KPR3-SUB). The 27 x 9 = 243 subs become
249 divisions because six subs straddle a sign boundary and are split there.
Sub-subs repeat the same division inside each sub.

Pure arithmetic, exact rationals: no ephemeris and no global state.

Usage:
    from app.kp.subs import lords_of, horary_number_longitude
    lords_of(53.5)                  # sign/star/sub/sub-sub lords of 23°30' Taurus
    horary_number_longitude(206)    # 296.111... = Capricorn 26°06'40"
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Final

#: Vimshottari order, beginning with Ketu (lord of Aswini).
DASA_ORDER: Final[tuple[str, ...]] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
)
#: Vimshottari years per lord; total 120.
DASA_YEARS: Final[dict[str, int]] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
SIGN_NAMES: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
#: Classical sign rulership (KP keeps the seven-planet scheme; nodes own no sign).
SIGN_LORDS: Final[tuple[str, ...]] = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
)
STAR_NAMES: Final[tuple[str, ...]] = (
    "Aswini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra", "Punarvasu",
    "Pushya", "Aslesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Sravana", "Dhanishta", "Satabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
)

STAR_SPAN: Final[Fraction] = Fraction(40, 3)  # 13°20'
_FULL: Final[Fraction] = Fraction(360)


@dataclass(frozen=True, slots=True)
class Division:
    """One of the 249 KP divisions (a sub, cut at sign edges).

    ``number`` is the 1-based KP horary number; ``start``/``end`` are sidereal
    longitudes in degrees (exact rationals).
    """

    number: int
    start: Fraction
    end: Fraction
    sign_lord: str
    star_lord: str
    sub_lord: str


@dataclass(frozen=True, slots=True)
class Lords:
    """Sign, star, sub and sub-sub lords of one sidereal longitude."""

    longitude: float
    sign: str
    sign_lord: str
    star: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str


def _seq_from(lord: str) -> tuple[str, ...]:
    i = DASA_ORDER.index(lord)
    return DASA_ORDER[i:] + DASA_ORDER[:i]


def _split(start: Fraction, span: Fraction, first: str) -> list[tuple[Fraction, Fraction, str]]:
    """Divide ``[start, start+span)`` into nine parts in Vimshottari proportion."""
    out: list[tuple[Fraction, Fraction, str]] = []
    cur = start
    for lord in _seq_from(first):
        w = span * DASA_YEARS[lord] / 120
        out.append((cur, cur + w, lord))
        cur += w
    return out


@lru_cache(maxsize=1)
def subs() -> tuple[tuple[Fraction, Fraction, str, str], ...]:
    """The 243 subs as ``(start, end, star_lord, sub_lord)``."""
    rows = []
    for s in range(27):
        star_lord = DASA_ORDER[s % 9]
        for a, b, sub_lord in _split(STAR_SPAN * s, STAR_SPAN, star_lord):
            rows.append((a, b, star_lord, sub_lord))
    return tuple(rows)


@lru_cache(maxsize=1)
def divisions() -> tuple[Division, ...]:
    """The 249 KP divisions in zodiacal order, numbered 1..249."""
    out: list[Division] = []
    for a, b, star_lord, sub_lord in subs():
        cuts = [a]
        edge = (a // 30 + 1) * 30
        if a < edge < b:
            cuts.append(Fraction(edge))
        cuts.append(b)
        for x, y in zip(cuts, cuts[1:]):
            out.append(Division(len(out) + 1, x, y, SIGN_LORDS[int(x // 30)], star_lord, sub_lord))
    return tuple(out)


def horary_number_longitude(number: int) -> float:
    """Sidereal ascendant for a KP horary number: the commencement of that division."""
    if not 1 <= number <= 249:
        raise ValueError("KP horary number must be 1..249")
    return float(divisions()[number - 1].start)


def lords_of(longitude: float) -> Lords:
    """Sign, star, sub and sub-sub lords of a sidereal longitude.

    Uses floor division at boundaries (a point exactly on a boundary belongs to
    the division that begins there), matching the repo's nakshatra convention.
    """
    lon = Fraction(longitude).limit_denominator(10**9) % _FULL
    star_idx = int(lon // STAR_SPAN)
    star_lord = DASA_ORDER[star_idx % 9]
    for a, b, sub_lord in _split(STAR_SPAN * star_idx, STAR_SPAN, star_lord):
        if a <= lon < b:
            for c, d, ss in _split(a, b - a, sub_lord):
                if c <= lon < d:
                    sign = int(lon // 30)
                    return Lords(float(lon), SIGN_NAMES[sign], SIGN_LORDS[sign],
                                 STAR_NAMES[star_idx], star_lord, sub_lord, ss)
    raise AssertionError("unreachable: sub table covers the circle")  # pragma: no cover


def dms(longitude: float) -> str:
    """Format a sidereal longitude as ``Sign DD°MM'SS"``."""
    lon = longitude % 360.0
    sign = int(lon // 30)
    total = round((lon - sign * 30) * 3600)
    d, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{SIGN_NAMES[sign]} {d:02d}°{m:02d}'{s:02d}\""
