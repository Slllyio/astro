"""Swavarga attainment — Raman's amsa-title ladder, with its counting basis MEASURED.

Raman's own table (GBB-3, the Sthana Bala chapter): a planet occupying its own varga N times
earns a title —

    2  Parijatamsa       3  Parvathamsa       4  Simhasanamsa
    5  Swargabalamsa     6  Indramsa          7  Rajapadmamsa
    8  Gopuramsam        9  Brahmapadamsam    10 Vaishnavamsam
    11 Saivamsam         12 Vaiseshikamsam                     (GBB-3:371-395)

His own definition of Swavarga: "If a planet, in any of the vargas occupies its own varga
(division) it is said to be in Swavarga" (GBB-3:320-322) — OWN sign, in that varga. His worked
example (Example 6-7, GBB-3:331-405) demonstrates the count over the SAPTAVARGA
(Rasi/Hora/Drekkana/Saptamsa/Navamsa/Dwadasamsa/Trimsamsa: Ravi two Swavargas → Parijatamsa).

**The ladder's upper rungs cannot ride the saptavarga** (seven vargas cannot yield twelve), so
Raman's table implies a wider set for them. The candidates were MEASURED (2026-08-09, 0.05°
longitude scan, every planet) over the shodasavarga the engine computes:

    own-sign counting:            Gopuramsa (8) reachable for ALL seven planets
                                  (max: Sun 11, Moon 8, Mars 14, Mercury 10, Jupiter 9,
                                  Venus 10, Saturn 8); Vaiseshikamsa (12) reachable ONLY
                                  for Mars.
    own+exalted+moolatrikona:     Vaiseshikamsa still unreachable for Moon, Mercury,
                                  Jupiter, Venus (max 10) — only Sun/Mars clear 12.

So this module exposes exactly what the measurements support:

* `swavarga_count(chart, planet)` over the shodasavarga, own-sign per Raman's definition;
* `amsa_title(count)` — the verbatim ladder;
* `attains_gopuramsa(chart, planet)` — rung 8, reachable for every planet under the one
  reading that can host the ladder's upper rungs. Named interpretive choice: the counting
  set is the shodasavarga (his example demonstrates the method on the saptavarga, where
  rung 8 is impossible; the wider set is the only coherent host).

**Vaiseshikamsa is deliberately NOT exposed.** Under every counting basis measured, rung 12 is
unreachable for most planets — any predicate would be either dead code or a silent
redefinition of Raman's count. The two 3HC yogas that need it (Bhojana Soukhya 170, Annadana
171) stay deferred with this measurement as the reason. BPHS's alternative ladders (dasavarga:
2 Parijata … 4 Gopura … 10 Sridhama/Vaiseshikamsa per Sarvartha Chintamani; BPHS
vol1_chapter_006:75-95) are recorded here as the classical variants — where they and Raman's
table disagree, Raman's stands, per the project rule.

Usage:
    from app.raman_saab.primitives.varga_attainment import attains_gopuramsa
"""
from __future__ import annotations

from typing import Final, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.varga import SUPPORTED_VARGAS, varga_sign

#: Raman's ladder, verbatim (GBB-3:371-395). Keys are Swavarga counts.
RAMAN_AMSA_TITLES: Final[dict[int, str]] = {
    2: "Parijatamsa", 3: "Parvathamsa", 4: "Simhasanamsa", 5: "Swargabalamsa",
    6: "Indramsa", 7: "Rajapadmamsa", 8: "Gopuramsam", 9: "Brahmapadamsam",
    10: "Vaishnavamsam", 11: "Saivamsam", 12: "Vaiseshikamsam",
}

#: The seven vargas of Raman's worked example (GBB-3:331-345).
SAPTAVARGA: Final[tuple[int, ...]] = (1, 2, 3, 7, 9, 12, 30)

#: The full shodasavarga the engine computes — the one set whose arithmetic can host the
#: ladder's upper rungs (measured; module docstring).
SHODASAVARGA: Final[tuple[int, ...]] = tuple(sorted(SUPPORTED_VARGAS))


def swavarga_count(chart: RamanChart, planet: str,
                   vargas: tuple[int, ...] = SHODASAVARGA) -> int:
    """How many of `vargas` place `planet` in its OWN sign — Raman's Swavarga definition
    (GBB-3:320-322), nothing wider. Nodes own no sign and always count zero."""
    p = chart.planets.get(planet)
    if p is None:
        return 0
    return sum(1 for n in vargas if SIGN_LORDS.get(varga_sign(p.lon, n)) == planet)


def amsa_title(count: int) -> Optional[str]:
    """The title a Swavarga count earns on Raman's ladder, or None below Parijatamsa."""
    return RAMAN_AMSA_TITLES.get(min(count, 12) if count >= 2 else 0)


def attains_gopuramsa(chart: RamanChart, planet: str) -> bool:
    """Rung 8 of Raman's ladder over the shodasavarga — reachable for every planet under
    own-sign counting (measured maxima 8-14), which is what makes this predicate honest
    where a Vaiseshikamsa predicate would not be."""
    return swavarga_count(chart, planet) >= 8
