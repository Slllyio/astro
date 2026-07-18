"""Vargavisesha (Parijatadi amsas) — GBB-3 Art.28: own-varga counts over the saptavarga.

Raman: "the greater the number of times a planet occupies its own varga the more
powerful it becomes" (GBB-3:356, Art.28 "Planets occupying more than one Own Varga"),
with his ladder of special amsas (GBB-3:383-395): twice -> Parijatamsa, thrice ->
Parvathamsa, ... twelve -> Vaiseshikamsam. Worked Example 7 (GBB-3:397-405, the
Standard Horoscope): Ravi/Kuja/Sukra each twice in own varga -> Parijatamsa; "the
other planets have only one Swavarga and consequently they have no special amsas."

NOTE (Raman wins): BPHS's Vargavisesha ladders use DIFFERENT names per varga-scheme
(Shadvarga: Kimsuka(2)..Kundala; Dasavarga: Parijata(2)..Sridhama(10); Shodasavarga:
Bhedaka..Sri Vallabha — BPHS ch.6, on disk, non-citable). This module encodes RAMAN's
single ladder from GBB-3 per the Prime Directive. The count runs over the SAPTAVARGA
(D1,D2,D3,D7,D9,D12,D30) — the same seven divisions GBB-3's own Sthana-bala uses —
so of Raman's printed 12-rung ladder only rungs 2..7 are attainable; the full ladder
is kept verbatim, not silently truncated.

KNOWN divergence (documented, mirrors tests/.../test_fixture_standard_horoscope.py):
the Standard Horoscope's Mars D30 cell is a sub-degree cusp artifact in Raman's 1918
hand tables (book: own thrimsamsa; scheme tables: Jupiter's) — the engine counts Mars
once, the book twice. Sun and Venus reproduce the book's Parijatamsa exactly.

Usage:
    from app.raman_saab.primitives.vargavisesha import vargavisesha
    for v in vargavisesha(chart):
        print(v.planet, v.own_varga_count, v.label)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.varga_lords import varga_lord_of

#: The GBB saptavarga — the seven divisions Raman's own Sthana-bala weighs (GBB-3 Art.27).
SAPTAVARGA: Final[tuple[int, ...]] = (1, 2, 3, 7, 9, 12, 30)

#: Raman's Parijatadi ladder, GBB-3:383-395 (count -> amsa name).
LADDER: Final[dict[int, str]] = {
    2: "Parijatamsa", 3: "Parvathamsa", 4: "Simhasanamsa", 5: "Swargabalamsa",
    6: "Indramsa", 7: "Rajapadmamsa", 8: "Gopuramsam", 9: "Brahpadamsam",
    10: "Vaishnavamsam", 11: "Saivamsam", 12: "Vaiseshikamsam"}

_VISIBLE: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


@dataclass(frozen=True)
class VargaVisesha:
    """One planet's own-varga standing over the saptavarga."""
    planet: str
    own_varga_count: int
    own_vargas: tuple[str, ...]          # e.g. ("D2", "D12")
    label: Optional[str]                 # LADDER[count]; None when count < 2
    source: Citation


def vargavisesha(chart: RamanChart) -> tuple[VargaVisesha, ...]:
    """Own-varga counts + Parijatadi labels for the seven visible grahas (canonical
    order). A planet 'occupies its own varga' when it is the LORD of the divisional
    sign holding its longitude (the GBB-3 Svavarga sense). Nodes are excluded — they
    own no sign."""
    out: list[VargaVisesha] = []
    for planet in _VISIBLE:
        p = chart.planets.get(planet)
        if p is None:
            continue
        own = tuple(f"D{n}" for n in SAPTAVARGA if varga_lord_of(p.lon, n) == planet)
        count = len(own)
        out.append(VargaVisesha(planet=planet, own_varga_count=count, own_vargas=own,
                                label=LADDER.get(count), source=Citation("GBB-3", 356)))
    return tuple(out)
