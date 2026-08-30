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

THE 22ND-DREKKANA COUNTING CONVENTION — RESOLVED 2026-08-30 by derivation, not assumption:
INCLUSIVE (+21 steps from the rising drekkana; equivalently, the SAME drekkana index in the
8th sign from the lagna-drekkana's sign). Three worked derivations agree:
  * Lincoln (HTJAH-II Chart 73): cast lagna Aquarius 17.4deg -> Aqu-2; +21 -> Virgo-2 —
    exactly "the 2nd of Virgo" (HTJAH-II:6752-6753); exclusive gives Virgo-3.
  * HTJAH-II Chart 69: fresh-cast from its printed birth data (10-11-1897 1:15am LMT,
    45N 93W) -> Leo 22.7deg -> Leo-3; +21 -> Pisces-3 — exactly "the 3rd decanate of
    Pisces" (HTJAH-II:6547); exclusive gives Aries-1.
  * Marie Antoinette is ANOMALOUS, not a third fit (reviewer recomputation, 2026-08-30):
    her hand-recast lagna is consistent with the PRINTED 74deg01 (Gemini 14 -> Gem-2), from
    which inclusive gives Cap-2 and exclusive Cap-3 — Raman's printed "first of Capricorn"
    (NH:5758/5945) matches NEITHER; he may have used the JP translator's first-of-8th-house
    shortcut there. Recorded as indeterminate; the derivation does not lean on her.
Jataka Parijata's gloss (jataka_parijata ch045:453-457) corroborates the 8TH-HOUSE PLACEMENT
of the 22nd only — its literal "FIRST drekkana in the 8th house" wording is refuted for the
index by Lincoln's Virgo-2 and Chart 69's Pisces-3. Raman's own in-passage identity is the
structural anchor: "drekkana rises in the 8th Bhava, i.e., the 22nd drekkana"
(HTJAH-II:3687), which only inclusive counting preserves for every lagna index. The ONE
contrary datum — the abstract Aquarius-27deg textbook example (HTJAH-I:10164-10166, "the
22nd from this is the 1st drekkana of Libra", +22) — contradicts Raman's own gloss two
sentences earlier by landing in the NINTH sign, is exactly one cell past the inclusive
Virgo-3, and is recorded as the classic off-by-one printing slip.

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


#: The four classes of the suicide/violent-end dictum (HTJAH-II:3684-3687: "a Sarpa
#: (serpent), Nigada (fetters), Pasa (noose) or Ayudha (weapon), drekkana rises in the
#: 8th Bhava, i.e., the 22nd drekkana").
VIOLENT_22ND_CLASSES: Final[frozenset[str]] = frozenset({"sarpa", "nigala", "pasa", "ayudha"})

#: Track-B lagna materialization sentinel: records carrying only `lagna_sign` build the
#: ascendant at exactly 5.0 deg into the sign (test_goldens.build_chart). Like the planet
#: midpoint, it is an absence of degree knowledge; a genuine 5d00'00" lagna is forgone.
_ASC_SENTINEL_DEG: Final[float] = 5.0


def drekkana_22nd(chart: RamanChart) -> Optional[tuple[int, int]]:
    """The (sign, index) cell of the 22nd drekkana, or None when the lagna degree is unknown.

    INCLUSIVE counting (see the module docstring's derivation): 21 drekkanas past the rising
    drekkana — equivalently the same drekkana index in the 8th sign from the lagna. None when
    the ascendant longitude sits on the sign-only materialization sentinel (5.0 deg)."""
    if (chart.asc_lon % 30.0) == _ASC_SENTINEL_DEG:
        return None
    k = drekkana_index(chart.asc_lon)
    n = (chart.asc_sign - 1) * 3 + k + 21          # inclusive: rising drekkana is the 1st
    n = ((n - 1) % 36) + 1
    return (n - 1) // 3 + 1, (n - 1) % 3 + 1


def drekkana_22nd_classes(chart: RamanChart) -> Optional[frozenset[str]]:
    """Named classes of the 22nd drekkana; None when unknowable, empty when unnamed."""
    cell = drekkana_22nd(chart)
    if cell is None:
        return None
    return DREKKANA_CLASSES.get(cell, frozenset())


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
