"""ChartBundle — the per-person feature layer for the Raman-method encoder.

One ``calculate_all_charts`` cast per person, unpacked into every primitive
``raman_method.py`` consumes:

- the run-3 ``Kundali`` (lagna, whole-sign houses, maraka/8th lords),
- a ``chart_model.Chart`` (for Shadbala / drishti helpers),
- per-planet **strength fractions** (Shodashavarga Vimsopaka rupas / 20 — the
  repo's D-3-locked scheme; Raman's own integrative dignity metric),
- Shadbala ratios (total/threshold virupa; graded, because the repo's
  Phase-2 partial Shadbala — Kala is Paksha-only, Cheshta is a retrograde
  proxy, Dig uses whole-sign — marks nearly every planet "insufficient",
  making the boolean non-discriminating; noted in the prereg),
- navamsa signs + navamsa lagna (whole-sign D9 houses),
- nakshatra dispositors, combustion flags, waxing-Moon flag,
- houses counted from the Moon (Chandra-lagna reference).

Nodes carry no Vimsopaka/Shadbala; their strength is their **dispositor's**
strength (pinned: Raman treats nodes as giving results of their dispositor
and associations). Every derived value is deterministic given the birth data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.core.chart_model import Chart
from app.core.ephemeris_engine import calculate_all_charts
from app.core.shadbala_report import compute_shadbala
from app.core.shodashavarga import compute_divisional_charts, compute_divisional_longitude
from app.core.vimsopaka_bala import vimsopaka_for_chart
from app.medini.ml.raman_saab.kundali import SIGN_RULER, Kundali, _nth_sign

GRAHAS: tuple[str, ...] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                           "Venus", "Saturn", "Rahu", "Ketu")
VISIBLE: tuple[str, ...] = GRAHAS[:7]

# Raman's natural malefics; Mercury/Moon conditionality is folded into the
# waxing flag + association terms in raman_method (kept out of the fixed sets).
NATURAL_MALEFICS: frozenset[str] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
NATURAL_BENEFICS: frozenset[str] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})


@dataclass(frozen=True)
class ChartBundle:
    """Everything raman_method needs for one person, from one cast."""
    person_id: str
    kundali: Kundali
    chart: Chart
    strength: Mapping[str, float]        # graha -> 0..1 (nodes: dispositor's)
    shadbala_ratio: Mapping[str, float]  # total/threshold virupa (visible 7);
                                         # graded — the Phase-2 partial Shadbala
                                         # marks nearly everyone insufficient,
                                         # so the boolean is non-discriminating
    navamsa_sign: Mapping[str, int]      # graha -> D9 sign 1..12
    navamsa_lagna: int                   # D9 lagna sign 1..12
    nakshatra_lord: Mapping[str, str]    # graha -> nakshatra dispositor
    combust: Mapping[str, bool]
    moon_waxing: bool
    lagna_lord: str

    def house_of(self, graha: str) -> int:
        return self.kundali.planet_house[graha]

    def house_from_moon(self, graha: str) -> int:
        moon_sign = self.chart.planet_signs["Moon"]
        return ((self.chart.planet_signs[graha] - moon_sign) % 12) + 1

    def navamsa_house(self, graha: str) -> int:
        return ((self.navamsa_sign[graha] - self.navamsa_lagna) % 12) + 1

    def sign_lord_of_house(self, house: int, *, from_moon: bool = False) -> str:
        """Whole-sign lord of the nth house from lagna (or from the Moon)."""
        base = (self.chart.planet_signs["Moon"] if from_moon
                else self.kundali.lagna_sign)
        return SIGN_RULER[_nth_sign(base, house)]

    def dispositor(self, graha: str) -> str:
        return SIGN_RULER[self.chart.planet_signs[graha]]


def _varga_signs_for_vimsopaka(d1: dict, divisional: dict) -> dict[str, dict[str, int]]:
    """Map compute_divisional_charts output ('D9_Navamsa') to Vimsopaka keys ('D9')."""
    per_planet: dict[str, dict[str, int]] = {}
    for planet in VISIBLE:
        signs = {"D1": int(d1[planet]["sign"])}
        for varga_name, chart in divisional.items():
            key = varga_name.split("_", 1)[0]
            if planet in chart:
                signs[key] = int(chart[planet]["sign"])
        per_planet[planet] = signs
    return per_planet


def build_bundle(
    year: int, month: int, day: int, hour: int, minute: int,
    tz_offset: float, lat: float, lon: float, *, person_id: str = "",
) -> ChartBundle | None:
    """Cast once and unpack; None on invalid/uncastable birth data."""
    if not (1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour < 24
            and 0 <= minute < 60 and -90.0 <= lat <= 90.0
            and -180.0 <= lon <= 180.0 and abs(tz_offset) <= 14.0
            and 1000 <= year <= 2100):
        return None
    try:
        cast = calculate_all_charts(year, month, day, hour, minute, tz_offset,
                                    latitude=lat, longitude=lon)
    except Exception:  # noqa: BLE001 — scraped data contains junk
        return None
    asc = cast.get("ascendant")
    if not asc:
        return None
    d1 = cast["d1"]
    if any(g not in d1 or "house" not in d1[g] for g in GRAHAS):
        return None

    lagna_sign = int(asc["sign"])
    planet_house = {g: int(d1[g]["house"]) for g in GRAHAS}
    planet_signs = {g: int(d1[g]["sign"]) for g in GRAHAS}
    planet_lons = {g: float(d1[g]["longitude"]) for g in GRAHAS}
    planet_retro = {g: bool(d1[g].get("is_retrograde", False)) for g in GRAHAS}

    kundali = Kundali(
        lagna_sign=lagna_sign,
        moon_longitude=planet_lons["Moon"],
        birth_jd=float(cast["birth_jd"]),
        planet_house=planet_house,
        maraka_lords=frozenset({SIGN_RULER[_nth_sign(lagna_sign, 2)],
                                SIGN_RULER[_nth_sign(lagna_sign, 7)]}),
        lord_8=SIGN_RULER[_nth_sign(lagna_sign, 8)],
        lord_2=SIGN_RULER[_nth_sign(lagna_sign, 2)],
        lord_7=SIGN_RULER[_nth_sign(lagna_sign, 7)],
    )
    chart = Chart(
        asc_sign=lagna_sign, asc_lon=float(asc["longitude"]),
        planet_signs=planet_signs, planet_houses=planet_house,
        planet_lons=planet_lons, planet_retrograde=planet_retro,
        person_id=person_id or None,
    )

    # Strength: full Shodashavarga Vimsopaka (D-3-locked scheme), 0..1.
    divisional = cast.get("divisional_charts") or compute_divisional_charts(d1)
    varga_signs = _varga_signs_for_vimsopaka(d1, divisional)
    vim = vimsopaka_for_chart(chart, varga_signs, scheme="shodashavargaja")
    strength: dict[str, float] = {
        p: vim[p].composite_rupas / 20.0 for p in VISIBLE if p in vim
    }
    # Nodes: dispositor's strength (pinned; see module docstring).
    for node in ("Rahu", "Ketu"):
        strength[node] = strength.get(SIGN_RULER[planet_signs[node]], 0.5)

    shad = compute_shadbala(chart)
    shadbala_ratio = {
        p: shad.per_planet[p].total_virupa / shad.per_planet[p].threshold_virupa
        for p in VISIBLE if p in shad.per_planet
    }

    d9 = cast["d9"]
    navamsa_sign = {g: int(d9[g]["sign"]) for g in GRAHAS if g in d9}
    nav_lagna = int(compute_divisional_longitude(float(asc["longitude"]), 9)
                    % 360.0 // 30) + 1

    nakshatra_lord = {
        g: str(d1[g].get("nakshatra", {}).get("lord", "")) for g in GRAHAS
    }
    sun_lon = planet_lons["Sun"]
    from app.core.planet_state import is_combust
    combust = {g: (is_combust(g, planet_lons[g], sun_lon)
                   if g not in ("Sun", "Rahu", "Ketu") else False)
               for g in GRAHAS}
    moon_waxing = ((planet_lons["Moon"] - sun_lon) % 360.0) < 180.0

    return ChartBundle(
        person_id=person_id, kundali=kundali, chart=chart,
        strength=strength, shadbala_ratio=shadbala_ratio,
        navamsa_sign=navamsa_sign, navamsa_lagna=nav_lagna,
        nakshatra_lord=nakshatra_lord, combust=combust,
        moon_waxing=moon_waxing, lagna_lord=SIGN_RULER[lagna_sign],
    )
