"""RamanChart — the doctrine engine's chart facade.

COMPOSES the frozen run-5 ``ChartBundle`` (``app/medini/ml/raman_saab/`` is
sha-pinned; zero edits there) and adds everything the compendium DSL needs
that the bundle discards:

  * all 16 shodashavarga sign maps for every graha AND the lagna
    (chart_bundle keeps only D9 + the Vimsopaka summary),
  * khara (22nd) drekkana and the 64th-navamsa chidra point,
  * Jaimini frames: arudha lagna and karakamsa (existing core modules),
  * frame-aware house lookup — ``lagna | moon | navamsa | arudha |
    karakamsa`` — one code path for every house-valued DSL leaf,
  * both ayanamsas: ``lahiri`` (repo default) and ``raman`` via the
    per-JD ayanamsa delta (pattern replicated from run5_potency.py with
    attribution — not imported from the frozen dir).

``from_printed_positions`` mirrors ``bundle_from_positions``: golden cases
are built from B. V. Raman's own printed longitudes, so the engine is
tested in exactly the frame he reasoned in.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping

from app.core.karakamsa_arudha import arudha_lagna
from app.core.shodashavarga import compute_divisional_longitude
from app.core.varga_points import VargaPoint, khara_drekkana, navamsa_64th
from app.medini.ml.raman_saab.chart_bundle import (
    GRAHAS,
    ChartBundle,
    bundle_from_positions,
)

# The 16 shodashavarga divisors (D1 included).
SHODASHAVARGA_DIVISORS: tuple[int, ...] = (
    1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60,
)

FRAMES: tuple[str, ...] = ("lagna", "moon", "navamsa", "arudha", "karakamsa")

AYANAMSAS: tuple[str, ...] = ("lahiri", "raman")

_SEVEN: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


def ayanamsa_delta_lahiri_minus_raman(jd: float) -> float:
    """ayanamsa_lahiri(jd) − ayanamsa_raman(jd); ADD to Lahiri longitudes
    to express them in Raman's frame.

    Pattern replicated from the proven run-5 implementation
    (app/medini/ml/raman_saab/run5_potency.py::_ayanamsa_delta) — that
    directory is sha-frozen, so the ~10 lines are copied with attribution
    rather than imported.
    """
    import swisseph as swe

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    a_l = swe.get_ayanamsa_ut(jd)
    swe.set_sid_mode(swe.SIDM_RAMAN)
    a_r = swe.get_ayanamsa_ut(jd)
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # restore process default
    return a_l - a_r


def _sign_of(lon: float) -> int:
    return int(lon % 360.0 // 30) + 1


@dataclasses.dataclass(frozen=True)
class RamanChart:
    bundle: ChartBundle
    ayanamsa: str                                  # frame the longitudes are in
    varga_signs: Mapping[str, Mapping[int, int]]   # graha -> divisor -> sign 1..12
    varga_lagna: Mapping[int, int]                 # divisor -> lagna varga sign
    khara: VargaPoint                              # 22nd drekkana from lagna
    chidra: VargaPoint                             # 64th navamsa from the Moon
    arudha_lagna_sign: int
    atmakaraka: str
    karakamsa_sign: int
    # True only when planet_lons are REAL printed/ephemeris longitudes (not
    # pada-midpoint sign reconstructions). Gates the degree feature layer in
    # house_judgment so sign-reconstructed charts stay byte-identical.
    degree_resolved: bool = False

    # -- frame-aware house lookup: the one code path every house-valued
    #    DSL leaf goes through ------------------------------------------
    def house_of(self, graha: str, frame: str = "lagna") -> int:
        if frame == "lagna":
            return self.bundle.house_of(graha)
        if frame == "moon":
            return self.bundle.house_from_moon(graha)
        if frame == "navamsa":
            return self.bundle.navamsa_house(graha)
        if frame == "arudha":
            return ((self.bundle.chart.planet_signs[graha]
                     - self.arudha_lagna_sign) % 12) + 1
        if frame == "karakamsa":
            # Jaimini: counted in the navamsa, from the karakamsa sign.
            return ((self.varga_signs[graha][9] - self.karakamsa_sign) % 12) + 1
        raise ValueError(f"unknown frame {frame!r}; expected one of {FRAMES}")

    def varga_sign(self, graha: str, divisor: int) -> int:
        return self.varga_signs[graha][divisor]

    def lagna_sign(self, frame: str = "lagna") -> int:
        if frame == "lagna":
            return self.bundle.kundali.lagna_sign
        if frame == "moon":
            return self.bundle.chart.planet_signs["Moon"]
        if frame == "navamsa":
            return self.bundle.navamsa_lagna
        if frame == "arudha":
            return self.arudha_lagna_sign
        if frame == "karakamsa":
            return self.karakamsa_sign
        raise ValueError(f"unknown frame {frame!r}; expected one of {FRAMES}")


def _build(bundle: ChartBundle, ayanamsa: str, *, degree_resolved: bool = False) -> RamanChart:
    lons = bundle.chart.planet_lons
    lagna_lon = bundle.chart.asc_lon
    varga_signs = {
        g: {d: _sign_of(compute_divisional_longitude(lons[g], d))
            for d in SHODASHAVARGA_DIVISORS}
        for g in GRAHAS
    }
    varga_lagna = {d: _sign_of(compute_divisional_longitude(lagna_lon, d))
                   for d in SHODASHAVARGA_DIVISORS}
    # Atmakaraka per Raman's classical 7-karaka scheme (Studies in Jaimini
    # Astrology): highest degree-in-sign among the seven planets.
    atmakaraka = max(_SEVEN, key=lambda g: lons[g] % 30.0)
    return RamanChart(
        bundle=bundle,
        ayanamsa=ayanamsa,
        varga_signs=varga_signs,
        varga_lagna=varga_lagna,
        khara=khara_drekkana(lagna_lon),
        chidra=navamsa_64th(lons["Moon"]),
        arudha_lagna_sign=arudha_lagna(bundle.chart).arudha_sign,
        atmakaraka=atmakaraka,
        karakamsa_sign=varga_signs[atmakaraka][9],
        degree_resolved=degree_resolved,
    )


def from_positions(
    planet_lons: Mapping[str, float],
    lagna_lon: float,
    *,
    birth_jd: float,
    person_id: str = "",
    ayanamsa: str = "lahiri",
    retrograde: Mapping[str, bool] | None = None,
    degree_resolved: bool = False,
) -> RamanChart:
    """Build from sidereal longitudes already expressed in ``ayanamsa``.

    ``degree_resolved`` marks the longitudes as REAL (printed/ephemeris) rather
    than pada-midpoint sign reconstructions, enabling the degree feature layer."""
    if ayanamsa not in AYANAMSAS:
        raise ValueError(f"unknown ayanamsa {ayanamsa!r}; expected one of {AYANAMSAS}")
    bundle = bundle_from_positions(
        planet_lons, lagna_lon, birth_jd=birth_jd,
        person_id=person_id, retrograde=retrograde,
    )
    return _build(bundle, ayanamsa, degree_resolved=degree_resolved)


def from_printed_positions(
    planet_lons: Mapping[str, float],
    lagna_lon: float,
    *,
    birth_jd: float,
    person_id: str = "",
    retrograde: Mapping[str, bool] | None = None,
) -> RamanChart:
    """Golden-case constructor: Raman's PRINTED positions, his ayanamsa,
    zero ephemeris noise (mirrors bundle_from_positions semantics). These are
    real degree positions, so the degree feature layer is enabled."""
    return from_positions(
        planet_lons, lagna_lon, birth_jd=birth_jd, person_id=person_id,
        ayanamsa="raman", retrograde=retrograde, degree_resolved=True,
    )


def lahiri_to_raman(
    planet_lons: Mapping[str, float], lagna_lon: float, birth_jd: float,
) -> tuple[dict[str, float], float]:
    """Re-express Lahiri longitudes in Raman's ayanamsa frame."""
    delta = ayanamsa_delta_lahiri_minus_raman(birth_jd)
    shifted = {g: (float(v) + delta) % 360.0 for g, v in planet_lons.items()}
    return shifted, (float(lagna_lon) + delta) % 360.0
