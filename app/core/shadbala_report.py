"""Per-chart Shadbala report — Phase 4 bridge layer.

The existing ``app/core/shadbala.py`` already implements all six Bala
components per-planet. This module bridges it to the framework's
``Chart`` contract: feed in a Chart, get back a ``ShadbalaReport``
with virupa scores and strong/weak labels for every visible planet.

## What "strong enough" means

BPHS Ch.27 fixes the *Pinda-bala* minimum thresholds in **rupas**
(1 rupa = 60 virupas). A planet whose total Shadbala exceeds its rupa
threshold is "sufficient" — Phase 6's three-pillar bhava judge treats
sufficient planets as load-bearing for their bhava significations,
insufficient ones as informational only.

| Planet  | Required (rupas) | (virupas) |
|---------|------------------|-----------|
| Sun     | 6.5              | 390       |
| Moon    | 6.0              | 360       |
| Mars    | 5.0              | 300       |
| Mercury | 7.0              | 420       |
| Jupiter | 6.5              | 390       |
| Venus   | 5.5              | 330       |
| Saturn  | 5.0              | 300       |

Rahu/Ketu have no Shadbala (they don't rule signs); they're excluded.

## Caveats

* The chart-level call assumes the input Chart carries D1 longitudes;
  D9 (Navamsha) sign is re-derived here via the locked Shodashavarga
  formula. If the dossier ever loses Navamsha alignment, this module
  is where the drift will surface.
* Kala-bala in the underlying engine currently includes only the
  Paksha sub-component; the other 7 (Nathonatha, Tribhaga, Hora, Dina,
  Masa, Varsha, Ayana) need birth-time + ephemeris derivations the
  framework doesn't yet pipe through. We surface this in the report.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart
from app.core.shadbala import shadbala_total
from app.core.shodashavarga import compute_divisional_longitude

# BPHS Ch.27 minimum-Shadbala threshold in virupas (rupas × 60).
_THRESHOLD_VIRUPA: Final[Mapping[str, float]] = {
    "Sun":     390.0,
    "Moon":    360.0,
    "Mars":    300.0,
    "Mercury": 420.0,
    "Jupiter": 390.0,
    "Venus":   330.0,
    "Saturn":  300.0,
}

_VISIBLE: Final[tuple[str, ...]] = tuple(_THRESHOLD_VIRUPA.keys())


@dataclass(frozen=True)
class PlanetShadbala:
    """Per-planet Shadbala result."""
    planet: str
    total_virupa: float
    sthana: float
    dig: float
    kala: float
    cheshta: float
    naisargika: float
    drik: float
    threshold_virupa: float
    is_sufficient: bool
    pinda_rupa: float


@dataclass(frozen=True)
class ShadbalaReport:
    """Whole-chart Shadbala — one PlanetShadbala per visible planet.

    Strongest planet by Pinda-bala is highlighted; Phase 6 treats it
    as the chart's primary actor for default predictions.
    """
    per_planet: Mapping[str, PlanetShadbala]
    strongest: str
    weakest: str
    notes: tuple[str, ...] = ()


def _navamsha_sign(longitude: float) -> int:
    """D9 sign from sidereal longitude using the locked Shodashavarga rule."""
    d9_lon = compute_divisional_longitude(longitude, 9) % 360.0
    return int(d9_lon // 30) + 1


def _build_legacy_chart_dict(chart: Chart) -> dict:
    """Convert Chart to the dict-shape the legacy shadbala_total expects."""
    return {
        p: {
            "longitude": chart.planet_lons.get(p, 0.0),
            "is_retrograde": chart.planet_retrograde.get(p, False),
            "sign": chart.planet_signs.get(p),
            "house": chart.planet_houses.get(p),
        }
        for p in chart.planet_signs
    }


def compute_planet_shadbala(planet: str, chart: Chart) -> PlanetShadbala:
    """Compute one planet's full Shadbala against the given chart."""
    if planet not in _THRESHOLD_VIRUPA:
        raise ValueError(f"planet must be visible (Sun..Saturn), got {planet}")
    lon = chart.planet_lons.get(planet)
    sign = chart.planet_signs.get(planet)
    house = chart.planet_houses.get(planet)
    if lon is None or sign is None or house is None:
        raise ValueError(
            f"chart missing planet={planet} position data — "
            f"lon={lon}, sign={sign}, house={house}"
        )
    d9_sign = _navamsha_sign(lon)
    legacy_chart = _build_legacy_chart_dict(chart)
    parts = shadbala_total(
        planet,
        longitude=lon,
        d1_sign=sign,
        d9_sign=d9_sign,
        house=house,
        chart=legacy_chart,
    )
    total = parts["total"]
    threshold = _THRESHOLD_VIRUPA[planet]
    return PlanetShadbala(
        planet=planet,
        total_virupa=total,
        sthana=parts["sthana"],
        dig=parts["dig"],
        kala=parts["kala"],
        cheshta=parts["cheshta"],
        naisargika=parts["naisargika"],
        drik=parts["drik"],
        threshold_virupa=threshold,
        is_sufficient=total >= threshold,
        pinda_rupa=total / 60.0,
    )


def compute_shadbala(chart: Chart) -> ShadbalaReport:
    """Full Shadbala report for one chart — all 7 visible planets."""
    per_planet = {p: compute_planet_shadbala(p, chart) for p in _VISIBLE}
    by_total = sorted(per_planet.values(), key=lambda x: x.total_virupa)
    return ShadbalaReport(
        per_planet=per_planet,
        strongest=by_total[-1].planet,
        weakest=by_total[0].planet,
        notes=(
            "Kala-bala includes Paksha only; 7 other sub-components "
            "(Nathonatha, Tribhaga, Hora, Dina, Masa, Varsha, Ayana) "
            "require birth-time + Sun declination not currently piped "
            "through the framework.",
        ),
    )


def is_sufficiently_strong(planet: str, chart: Chart) -> bool:
    """Convenience boolean — does this planet exceed its rupa threshold?"""
    return compute_planet_shadbala(planet, chart).is_sufficient
