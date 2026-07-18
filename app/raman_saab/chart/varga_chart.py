"""Full divisional-chart casting — the varga lagna and planets-in-houses for any of the
16 Shodasavarga divisions.

Doctrine: HPA ch.11 ("The Shadvargas") defines the divisions Raman teaches, and names
Parashara's sixteen-fold scheme (HPA-11:195-201). All per-longitude sign math delegates to
``chart/varga.py`` (pinned by tests/raman_saab/test_varga_divisions.py); the varga LAGNA is
the varga sign of the ascendant degree — the same construction the engine already uses for
the D9 lagna (``primitives/special_points.navamsa_lagna``), generalized to every division.
Houses are whole-sign counted from the varga lagna, mirroring the D1 ``rasi_house``
construction (``chart/model.py``).

D2 (Hora) is a TWO-sign division (every longitude maps to Cancer or Leo only,
HPA-11 hora definition): it carries no 12-house frame, so every ``VargaPos.house`` is None
there and judges must treat the hora as sign-placement only.

Usage:
    from app.raman_saab.chart.varga_chart import cast_varga_chart, cast_all_vargas
    d10 = cast_varga_chart(chart, 10)          # the Dasamsa chart
    all16 = cast_all_vargas(chart)             # {n: VargaChart} over SUPPORTED_VARGAS
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart

#: Divisions with no 12-house frame (sign-placement only).
_NO_HOUSE_FRAME: frozenset[int] = frozenset({2})


@dataclass(frozen=True)
class VargaPos:
    """One graha's place in a divisional chart."""
    name: str
    sign: int                      # 1..12 — varga_sign(planet.lon, n)
    house: Optional[int]           # 1..12 from the varga lagna; None when the division
                                   # has no house frame (D2 hora)
    vargottama: bool               # the planet's D1==D9 flag (PlanetPos.vargottama) —
                                   # surfaced on every varga row because a vargottama graha
                                   # is strong wherever it testifies (NOT a per-varga
                                   # same-sign claim)


@dataclass(frozen=True)
class VargaChart:
    """A cast divisional chart: its lagna and every available graha placed."""
    n: int                         # 1,2,3,4,7,9,10,12,16,20,24,27,30,40,45,60
    lagna_sign: int                # varga_sign(chart.asc_lon, n)
    lagna_lord: str                # SIGN_LORDS[lagna_sign]
    lagna_vargottama: bool         # lagna_sign == the D1 ascendant sign (meaningful for D9:
                                   # a vargottama lagna; True elsewhere only by coincidence)
    positions: Mapping[str, VargaPos]


def cast_varga_chart(chart: RamanChart, n: int) -> VargaChart:
    """Cast the D-``n`` chart for ``chart``. Works on Track-B sparse charts (needs only
    ``asc_lon`` + per-planet ``lon``); grahas absent from ``chart.planets`` are simply
    absent from ``positions``. Raises ValueError for an unsupported ``n`` (delegated to
    ``varga.varga_sign``)."""
    lagna_sign = varga.varga_sign(chart.asc_lon, n)
    house_frame = n not in _NO_HOUSE_FRAME
    positions: dict[str, VargaPos] = {}
    for name, p in chart.planets.items():
        sign = varga.varga_sign(p.lon, n)
        house = ((sign - lagna_sign) % 12) + 1 if house_frame else None
        positions[name] = VargaPos(name=name, sign=sign, house=house,
                                   vargottama=p.vargottama)
    return VargaChart(n=n, lagna_sign=lagna_sign, lagna_lord=SIGN_LORDS[lagna_sign],
                      lagna_vargottama=(lagna_sign == chart.asc_sign),
                      positions=positions)


def cast_all_vargas(chart: RamanChart) -> dict[int, VargaChart]:
    """All 16 Shodasavarga charts, keyed by division number, ascending."""
    return {n: cast_varga_chart(chart, n) for n in sorted(varga.SUPPORTED_VARGAS)}
