"""Named-drekkana classification (Ayudha / Pasa / Nigala / Sarpa / Pakshi / Chatushpada) —
the death-manner drekkana apparatus of HTJAH-II's "Table of Drekkanas".

Each sign's three drekkanas (0-10, 10-20, 20-30 degrees) may carry a classical class name;
Raman reads violent/captive death manners off them ("Saturn lord of the 8th occupying Ayudha
Drekkana" -> hanging, Godse; "Ayushkaraka is also in a Nigala Drekkana" -> death in captivity,
Marie Antoinette). The table below was reconstructed cell-by-cell from the project library by
an evidence sweep (DOCTRINE_BACKLOG "WS1 pass 3", 2026-08-30) because the printed table's OCR
(HTJAH-II:3845-3871) is garbled. Sources per cell:

* [T] Raman's own Table of Drekkanas, HTJAH-II:3845-3871 — whose cells match Phaladeepika
  III.13 verbatim (phaladeepika_sastri_1950 ch.3:275-287), so PD anchors the garbled cells;
* [W] a worked-chart instance where the printed longitude derives the cell (Godse Saturn
  9deg04 Aries -> Aries-1 Ayudha, NH:14641/14735; Lincoln "2nd of Virgo" HTJAH-II:6752-6753;
  Marie Antoinette Saturn 4deg Capricorn -> Cap-1 Nigala, NH:5758/5944-5947; Tantri Moon
  Leo-3 + Saturn Gemini-2, NH:11391-11492; Savarkar Jupiter Gemini-2, NH:10453/10567;
  Chart 69's 22nd "3rd decanate of Pisces ... a Sarpa", HTJAH-II:6547);
* [C] classical corroboration (Brihat Jataka ch.27 drekkana images; Prasna Marga I:5558/6914
  + Appendix VII; Jataka Parijata II.55; Hora Ratnam ch.16).

RECORDED CONFLICTS (encoded per the resolution, never averaged):
* Scorpio-2 is PASA per the table/PD but NIGADA per Raman's own worked charts 66/67
  (HTJAH-II:6357-6358, 6416-6418) and JP II.55 -> DUAL-TAGGED {pasa, nigala}. Rule-neutral:
  every death rule Raman applies treats {Sarpa, Nigala, Pasa} as one captivity/noose triad
  (HTJAH-II:6674-6676, 6701-6705).
* Cancer's Sarpa cell: 3rd per Raman's table/PM/HR (encoded), 2nd per JP (variant recorded).
* Tantri's Ketu at Pisces 3deg43 is called "Sarpa" (NH:11492) but NO table in the library
  makes Pisces-1 Sarpa -> NOT encoded (anomalous single instance; possibly Raman's slip).
* Capricorn-1: a garbled JP line reads "Pakshi"; Raman x3 + PD + HR + BJ say fetters ->
  Nigala stands.

DELIBERATELY NOT SHIPPED: the 22nd-drekkana (rising-drekkana) lookup — Raman's own two
worked examples imply different counting conventions (HTJAH-I:10164-10166 exclusive vs
Marie Antoinette's derivation), so encoding it would guess doctrine. Planet-occupies-drekkana
needs no convention and is what the shipped rules use.

Pakshi and Chatushpada cells are retained for completeness but appear in NO death-manner
worked chart; they are SECONDARY data (several are OCR-PROBABLE) and no verdict rule may
consume them without fresh review.
"""
from __future__ import annotations

from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart

#: (sign 1..12, drekkana 1..3) -> class names. Signs: 1=Aries .. 12=Pisces.
DREKKANA_CLASSES: Final[dict[tuple[int, int], frozenset[str]]] = {
    # AYUDHA (weapon) — the fully-recovered column: [T]+PD cell-for-cell, 5 cells [W]-anchored.
    (1, 1): frozenset({"ayudha"}),      # Aries-1   [T][W Godse][C PD/BJ]
    (1, 3): frozenset({"ayudha"}),      # Aries-3   [T][C PD/BJ]
    (3, 2): frozenset({"ayudha"}),      # Gemini-2  [T][W Tantri, Savarkar][C PD/BJ]
    (3, 3): frozenset({"ayudha"}),      # Gemini-3  [T-PROBABLE][C PD/BJ]
    (5, 3): frozenset({"ayudha"}),      # Leo-3     [T][W Tantri][C PD/BJ]
    (6, 2): frozenset({"ayudha"}),      # Virgo-2   [T][W Lincoln][C PD/BJ]
    (7, 3): frozenset({"ayudha"}),      # Libra-3   [T][W Marie Antoinette][C PD/BJ]
    (9, 1): frozenset({"ayudha"}),      # Sag-1     [T][C PD/BJ][W-weak Chart 65]
    (9, 3): frozenset({"ayudha"}),      # Sag-3     [T][C PD/BJ]
    # PASA (noose) / NIGALA (fetters) — the captivity pair.
    (8, 2): frozenset({"pasa", "nigala"}),  # Scorpio-2: PASA per [T]/PD, NIGADA per Raman's
    #                                          worked charts 66/67 + JP — dual-tagged, see above.
    (10, 1): frozenset({"nigala"}),     # Cap-1     [T][W Marie Antoinette x2][C PD/HR/BJ]
    # SARPA (serpent)
    (8, 1): frozenset({"sarpa"}),       # Scorpio-1 [T-PROBABLE][C PM/JP/BJ]
    (4, 3): frozenset({"sarpa"}),       # Cancer-3  [T-PROBABLE][C PM/HR/BJ; JP variant: 2nd]
    (12, 3): frozenset({"sarpa"}),      # Pisces-3  [T-PROBABLE][W Chart 69][C PM/HR/JP/BJ]
    # PAKSHI (bird) — SECONDARY, no death-manner worked chart uses it.
    (5, 1): frozenset({"pakshi", "chatushpada"}),  # Leo-1 [T][C PM/PD/BJ]; PM App.VII dual
    (11, 1): frozenset({"pakshi"}),     # Aquarius-1 [T-PROBABLE][C PM/PD/BJ]
    (2, 3): frozenset({"pakshi"}),      # Taurus-3   [T-PROBABLE][C PD/HR]
    (7, 2): frozenset({"pakshi"}),      # Libra-2    [T][C PM/PD/BJ]
    # CHATUSHPADA (quadruped) — SECONDARY, OCR-PROBABLE throughout.
    (4, 1): frozenset({"chatushpada"}),  # Cancer-1  [T-PROBABLE][C BJ/PM]
    (1, 2): frozenset({"chatushpada"}),  # Aries-2   [T-PROBABLE][C BJ/PM]
    (2, 2): frozenset({"chatushpada"}),  # Taurus-2  [T-PROBABLE][C BJ/PM]
    (8, 3): frozenset({"chatushpada"}),  # Scorpio-3 [T-PROBABLE][C BJ/PM]
}

#: The captivity/noose triad Raman applies jointly (HTJAH-II:6674-6676: "Nigala, Sarpa or
#: Pasa ... death is brought about by suicide by hanging" / death in captivity).
CAPTIVITY_TRIAD: Final[frozenset[str]] = frozenset({"sarpa", "nigala", "pasa"})

#: Sign-midpoint sentinel: Track-B records without a printed degree materialize planets at
#: exactly 15.0 deg within the sign. A midpoint is an ABSENCE of degree knowledge, and a
#: named drekkana must never be manufactured from it (a phantom 2nd-drekkana class would
#: fire death rules on charts whose true drekkana is unknown). A genuinely printed 15d00'00"
#: is indistinguishable and forgone — recorded cost, favouring silence over invention.
_MIDPOINT_DEG: Final[float] = 15.0


def drekkana_index(lon: float) -> int:
    """1, 2 or 3 — which drekkana of its sign this longitude occupies (10-degree bands)."""
    return int((lon % 30.0) // 10.0) + 1


def planet_drekkana_classes(planet: str, chart: RamanChart) -> Optional[frozenset[str]]:
    """The named-drekkana classes `planet` occupies, or None when unknowable.

    None (not empty) when the planet is absent OR its longitude sits exactly on the sign
    midpoint — the Track-B materialization sentinel for `degree unprinted` (see
    _MIDPOINT_DEG). An empty frozenset means the degree is known and the drekkana simply
    carries no class name.
    """
    p = chart.planets.get(planet)
    if p is None:
        return None
    if (p.lon % 30.0) == _MIDPOINT_DEG:
        return None
    return DREKKANA_CLASSES.get((p.sign, drekkana_index(p.lon)), frozenset())
