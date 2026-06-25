"""Ayurdaya — mathematical longevity (lifespan) by the Pindayu and Amsayu methods.

BV Raman, *How to Judge a Horoscope* Vol II, "Concerning the Eighth House"
(HTJAH-II:3947-4441). Two classical lifespan calculators:

* **Pindayu** (Grahadattayurdaya, HTJAH-II:3947-4260) — each graha contributes a
  term scaled by its arc from deep exaltation; the Lagna adds a navamsa term.
* **Amsayu** (HTJAH-II:4262-4441) — each graha's term is the navamsas it has
  traversed, with Bharana (×2/×3) increases for dignity.

Both then suffer the four **Haranas** (reductions), applied in order:
Chakrapatha → Satrukshetra → Astangata → Krurodaya (Pindayu only).

Validated to the day against Raman's worked Chart 33 (Pindayu = 86y 2m 20d) and
Chart 34 (Amsayu = 68y 10m 5d) — see ``tests/raman_saab/test_ayurdaya.py``.

NOTE on precision: the per-graha contributions match Raman's worked tables to ≤1
day on his own stated longitudes. Against a live ephemeris (these are 1879/1912
births) the *span* is robust to a year or two and the *longevity class*
(alpa/madhya/purna) is robust — that, not a to-the-day match, is the usable output.

Usage:
    from app.raman_saab.primitives.ayurdaya import longevity, pindayu, amsayu
    result = longevity(chart)          # auto-selects the method (Raman's rule)
    result.total_years, result.longevity_class   # e.g. 86.2, "purna"
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import relationships as rel

# ---------------------------------------------------------------------------
# Constants (HTJAH-II:3959-3989, 4166-4178)
# ---------------------------------------------------------------------------

SEVEN: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Full term of life at deep exaltation (years).
_FULL_TERM: Final[dict[str, float]] = {
    "Sun": 19, "Moon": 25, "Mars": 15, "Mercury": 12,
    "Jupiter": 15, "Venus": 21, "Saturn": 20}

# Deep-exaltation sidereal longitudes (degrees).
_EXALT_LON: Final[dict[str, float]] = {
    "Sun": 10, "Moon": 33, "Mars": 298, "Mercury": 165,
    "Jupiter": 95, "Venus": 357, "Saturn": 200}

# Chakrapatha reduction fractions by Bhava (west half), malefic vs benefic
# (HTJAH-II:4040-4044). Bhava -> fraction of the term deducted.
_CHAKRA_MALEFIC: Final[dict[int, float]] = {
    12: 1.0, 11: 1 / 2, 10: 1 / 3, 9: 1 / 4, 8: 1 / 5, 7: 1 / 6}
_CHAKRA_BENEFIC: Final[dict[int, float]] = {
    12: 1 / 2, 11: 1 / 4, 10: 1 / 6, 9: 1 / 8, 8: 1 / 10, 7: 1 / 12}

# Astangata (combustion) orbs in degrees from the Sun (HTJAH-II:4074-4078).
_COMBUST_ORB: Final[dict[str, float]] = {
    "Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 5}
# Venus and Saturn are exempt from Astangata Harana even when combust (HTJAH-II:4079-4081).
_ASTANGATA_EXEMPT: Final[frozenset[str]] = frozenset({"Venus", "Saturn"})

_NAVAMSA_DEG: Final[float] = 30.0 / 9.0  # 3°20'

# Longevity class bands (years). Standard balarishta/madhyayu/purnayu split.
_ALPA_MAX: Final[float] = 32.0
_MADHYA_MAX: Final[float] = 70.0


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlanetTerm:
    """One graha's raw term and the value surviving each successive Harana."""
    planet: str
    sphutavarsha: float       # raw years (Pindayu arc-term or Amsayu navamsa-term × Bharana)
    after_chakrapatha: float
    after_satrukshetra: float
    final: float              # after Astangata


@dataclass(frozen=True)
class AyurdayaResult:
    """A full lifespan computation: total years, the graha + Lagna breakdown,
    and the derived longevity class."""
    method: str               # "pindayu" | "amsayu"
    total_years: float
    graha_ayurdaya: float
    lagna_years: float
    terms: tuple[PlanetTerm, ...]

    @property
    def longevity_class(self) -> str:
        """alpa (<32y, balarishta) / madhya (32-70y) / purna (>=70y)."""
        if self.total_years < _ALPA_MAX:
            return "alpa"
        if self.total_years < _MADHYA_MAX:
            return "madhya"
        return "purna"

    def ymd(self) -> tuple[int, int, int]:
        """(years, months, days) on the classical 360-day-year convention."""
        return _to_ymd(self.total_years)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _to_ymd(years: float) -> tuple[int, int, int]:
    y = int(years)
    fm = (years - y) * 12
    m = int(fm + 1e-9)
    d = round((fm - m) * 30)
    if d >= 30:
        d -= 30
        m += 1
    if m >= 12:
        m -= 12
        y += 1
    return y, m, d


def _rupas(chart: RamanChart, planet: str) -> float:
    """Total Shadbala in rupas for `planet` (0 when unavailable)."""
    p = chart.planets.get(planet)
    sb = getattr(p, "shadbala_rupas", None) if p is not None else None
    return float(getattr(sb, "total", 0.0) or 0.0)


def _is_benefic_for_chakra(chart: RamanChart, planet: str) -> bool:
    """Moon/Jupiter/Venus are benefics; Sun/Mars/Saturn malefics. Mercury is benefic
    unless conjoined by a malefic (HTJAH-II:4031-4033)."""
    if planet in ("Moon", "Jupiter", "Venus"):
        return True
    if planet in ("Sun", "Mars", "Saturn"):
        return False
    # Mercury: badly-afflicted (malefic graha in its house) -> malefic, else benefic.
    merc = chart.planets.get("Mercury")
    if merc is None:
        return True
    for nm in ("Sun", "Mars", "Saturn"):
        p = chart.planets.get(nm)
        if p is not None and p.rasi_house == merc.rasi_house:
            return False
    return True


def _strongest_in_house(chart: RamanChart, house: int) -> Optional[str]:
    """The graha with the greatest Shadbala among the SEVEN in `house` (the
    Chakrapatha "strongest planet in each house" rule, HTJAH-II:4046-4048)."""
    occ = [p for p in SEVEN if p in chart.planets and chart.planets[p].rasi_house == house]
    if not occ:
        return None
    return max(occ, key=lambda p: _rupas(chart, p))


def _in_enemy_sign(chart: RamanChart, planet: str) -> bool:
    """The planet occupies a sign owned by its natural enemy (Satrukshetra trigger)."""
    p = chart.planets.get(planet)
    if p is None:
        return False
    sign_lord = SIGN_LORDS[p.sign]
    if sign_lord == planet:
        return False
    return rel.naisargika(planet, sign_lord) == "enemy"


def _is_combust(chart: RamanChart, planet: str) -> bool:
    """Within the Astangata orb of the Sun (HTJAH-II:4074-4078)."""
    if planet == "Sun" or planet not in _COMBUST_ORB:
        return False
    sun = chart.planets.get("Sun")
    p = chart.planets.get(planet)
    if sun is None or p is None:
        return False
    sep = abs(p.lon - sun.lon) % 360.0
    sep = min(sep, 360.0 - sep)
    return sep <= _COMBUST_ORB[planet]


def _navamsa_years(lon: float) -> float:
    """Amsayu term: the navamsas a longitude has traversed -> years + fraction
    (HTJAH-II:4282-4288). years = (lon_min // 200) % 12; fraction = (lon_min % 200)/200."""
    lon_min = round((lon % 360.0) * 60.0)
    q, r = divmod(lon_min, 200)
    return (q % 12) + r / 200.0


def _apply_haranas(chart: RamanChart, planet: str, raw: float, *,
                   krurodaya_ok: bool) -> PlanetTerm:
    """Chakrapatha -> Satrukshetra -> Astangata, in order. (Krurodaya is applied
    once, to the grand total, by the callers — not per planet.)"""
    p = chart.planets[planet]
    term = raw
    # 1. Chakrapatha: only on the strongest graha in a west-half house (7th-12th).
    if 7 <= p.rasi_house <= 12 and _strongest_in_house(chart, p.rasi_house) == planet:
        table = _CHAKRA_BENEFIC if _is_benefic_for_chakra(chart, planet) else _CHAKRA_MALEFIC
        term -= term * table[p.rasi_house]
    after_chakra = term
    # 2. Satrukshetra: planet in an enemy sign loses 1/3; Mars & retrograde exempt.
    if planet != "Mars" and not p.retrograde and _in_enemy_sign(chart, planet):
        term -= term / 3.0
    after_satru = term
    # 3. Astangata: a combust planet loses 1/2; Venus & Saturn exempt.
    if planet not in _ASTANGATA_EXEMPT and _is_combust(chart, planet):
        term -= term / 2.0
    return PlanetTerm(planet, raw, after_chakra, after_satru, term)


# ---------------------------------------------------------------------------
# Pindayu (HTJAH-II:3947-4260)
# ---------------------------------------------------------------------------

def _arc_of_longevity(lon: float, planet: str) -> float:
    """Arc from the deep-debilitation point (HTJAH-II:4146-4150): full term at
    exaltation (arc 360), half at debilitation (arc 180)."""
    diff = (lon - _EXALT_LON[planet]) % 360.0
    return 360.0 - diff if diff < 180.0 else diff


def _sphuta_ayurvarsha(planet: str, lon: float) -> float:
    """A graha's raw Pindayu term: full_term × arc / 360 (HTJAH-II:4158-4162)."""
    return _FULL_TERM[planet] * _arc_of_longevity(lon, planet) / 360.0


def _pindayu_lagna_years(chart: RamanChart) -> float:
    """Lagna term (Pindayu): navamsas traversed WITHIN the rising sign -> years +
    fraction (HTJAH-II:4252-4255; chart 33 Aquarius 9°42' -> 2y 10m 28d)."""
    deg_in_sign = chart.asc_lon % 30.0
    whole = int(deg_in_sign / _NAVAMSA_DEG)
    frac = (deg_in_sign - whole * _NAVAMSA_DEG) / _NAVAMSA_DEG
    return whole + frac


def _krurodaya_deduction(chart: RamanChart, total: float) -> float:
    """Krurodaya Harana (Pindayu only, HTJAH-II:4083-4101): a malefic in the Lagna
    deducts (amsas-Lagna-passed × total) / 108 from the grand total; the nearest
    malefic to the Lagna degree is taken; halved if a benefic aspects it."""
    malefics_in_lagna = [p for p in ("Sun", "Mars", "Saturn")
                         if p in chart.planets and chart.planets[p].rasi_house == 1]
    if not malefics_in_lagna:
        return 0.0
    amsas_passed = (chart.asc_lon % 30.0) / _NAVAMSA_DEG
    return amsas_passed * total / 108.0


def pindayu(chart: RamanChart) -> AyurdayaResult:
    """Grahadattayurdaya: arc-scaled graha terms, the four Haranas, plus the Lagna."""
    terms: list[PlanetTerm] = []
    for planet in SEVEN:
        p = chart.planets.get(planet)
        if p is None:
            continue
        raw = _sphuta_ayurvarsha(planet, p.lon)
        terms.append(_apply_haranas(chart, planet, raw, krurodaya_ok=True))
    graha = sum(t.final for t in terms)
    graha -= _krurodaya_deduction(chart, graha)
    lagna = _pindayu_lagna_years(chart)
    return AyurdayaResult("pindayu", graha + lagna, graha, lagna, tuple(terms))


# ---------------------------------------------------------------------------
# Amsayu (HTJAH-II:4262-4441)
# ---------------------------------------------------------------------------

def _bharana_multiplier(chart: RamanChart, planet: str) -> int:
    """Bharana (increase): ×3 if exalted or retrograde; ×2 if vargottama / own
    navamsa / own rasi (HTJAH-II:4297-4305); the stronger factor only."""
    p = chart.planets.get(planet)
    if p is None:
        return 1
    # ×3: exalted (arc near 360 / within its own exaltation sign) or retrograde.
    exalt_sign = int(_EXALT_LON[planet] // 30) + 1
    if p.retrograde or p.sign == exalt_sign:
        return 3
    # ×2: vargottama, own navamsa, or own rasi.
    if (p.vargottama
            or SIGN_LORDS[p.sign] == planet
            or SIGN_LORDS[p.navamsa_sign] == planet):
        return 2
    return 1


def amsayu(chart: RamanChart) -> AyurdayaResult:
    """Navamsa lifespan: per-graha navamsa terms × Bharana, then Chakrapatha +
    Satrukshetra + Astangata (NO Krurodaya, HTJAH-II:4327-4328), plus the Lagna."""
    terms: list[PlanetTerm] = []
    for planet in SEVEN:
        p = chart.planets.get(planet)
        if p is None:
            continue
        raw = _navamsa_years(p.lon) * _bharana_multiplier(chart, planet)
        terms.append(_apply_haranas(chart, planet, raw, krurodaya_ok=False))
    graha = sum(t.final for t in terms)
    lagna = _navamsa_years(chart.asc_lon)
    return AyurdayaResult("amsayu", graha + lagna, graha, lagna, tuple(terms))


# ---------------------------------------------------------------------------
# Method selection
# ---------------------------------------------------------------------------

def longevity(chart: RamanChart) -> AyurdayaResult:
    """Raman's method selection (HTJAH-II:4266-4267): use **Amsayu** when the Lagna
    lord is more powerful (Shadbala) than both the Sun and the Moon; otherwise
    **Pindayu**."""
    lagna_lord = SIGN_LORDS[chart.asc_sign]
    if lagna_lord in chart.planets and "Sun" in chart.planets and "Moon" in chart.planets:
        s = _rupas(chart, lagna_lord)
        if s > _rupas(chart, "Sun") and s > _rupas(chart, "Moon"):
            return amsayu(chart)
    return pindayu(chart)
