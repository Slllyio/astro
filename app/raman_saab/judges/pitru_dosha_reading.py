"""Pitṛ-doṣa / ancestral-karma reading — a REPORT-ONLY, CLASSICAL surface.

The classical thesis (BPHS Ch. 82-83; Praśna Mārga Ch. 18) reads **absence or loss of issue as an
inherited karmic debt** — the curse of the father (pitṛ-śrāpa), the mother (mātṛ-śrāpa), or the
serpents (sarpa-śrāpa) from a past birth, remedied by ancestral rites (śrāddha) that "prolong the
family lineage" (BPHS 83:107-121). This surface reads the RASI-computable curse-yogas that bear on
progeny + lineage.

PROVENANCE (honest, no unlock): every curse-yoga here is **CLASSICAL_NONCITABLE** — it lives in
BPHS / Praśna Mārga, NOT in Raman's live corpus (the firewall stays intact; this is tagged exactly
like the KP/Rath successive-child scheme in ``saptamsa_reading.py``). The one AUTHORITATIVE line is
Raman's OWN children verdict (``judge_house(chart, 5)``), which DECIDES; the ancestral-curse yogas
are a *corroborating lens*, never the verdict. The lineage vargas (D-40 mother-line, D-45
father-line, D-60 past-births; Rath/BPHS) are noted but beyond the engine's 16-varga range.

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path — the golden ratchet is
untouched by construction.

NOT FATALISM. An ancestral-karma reading is a contemplative lens with a classical remedy (śrāddha),
never a decree; and never medical advice.

Usage:
    from app.raman_saab.judges.pitru_dosha_reading import build_pitru_dosha_reading
    r = build_pitru_dosha_reading(chart)
    r.raman_children_verdict   # Raman's authoritative progeny read
    r.curse_yogas              # the classical ancestral-curse indications that fire
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.judges.house_template import judge_house
from app.raman_saab.judges.saptamsa_reading import Tagged
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS, NATURAL_MALEFICS

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@dataclass(frozen=True)
class PitruDoshaReading:
    """The ancestral-karma lens on progeny + lineage — Raman decides, the classical curses corroborate."""
    raman_children_verdict: str          # RAMAN_EXPLICIT — the authoritative progeny read
    curse_yogas: tuple[Tagged, ...]       # the classical curse-yogas that FIRE (CLASSICAL_NONCITABLE)
    pitru_bhava: tuple[Tagged, ...]       # the 9th (pitṛ-sthāna) + Sun (pitṛ-kāraka) picture
    notes: tuple[Tagged, ...]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _house_of_sign(from_sign: int, offset: int) -> int:
    return ((from_sign - 1) + (offset - 1)) % 12 + 1


def _occupants(chart: RamanChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in chart.planets and chart.planets[n].rasi_house == house)


def _malefics_on(chart: RamanChart, house: int) -> tuple[str, ...]:
    occ = _occupants(chart, house)
    asp = tuple(drishti.aspecting_house(house, chart))
    return tuple(n for n in _PLANET_ORDER
                if n in NATURAL_MALEFICS and (n in occ or n in asp))


def _benefic_aspect_on(chart: RamanChart, house: int) -> bool:
    return any(n in NATURAL_BENEFICS for n in drishti.aspecting_house(house, chart))


def _planet_house(chart: RamanChart, planet: str) -> int:
    p = chart.planets.get(planet)
    return p.rasi_house if p is not None else 0


def _serpent_curse(chart: RamanChart, fifth: int, fifth_lord: str) -> tuple[Tagged, ...]:
    """Sarpa-śrāpa (Praśna Mārga): Rahu in the 5th, or Rahu with the 5th lord, without a benefic
    aspect on the 5th → loss of issue by the serpent-curse."""
    rahu_h = _planet_house(chart, "Rahu")
    lord_h = _planet_house(chart, fifth_lord)
    with_lord = rahu_h != 0 and rahu_h == lord_h
    in_fifth = rahu_h == fifth
    if (in_fifth or with_lord) and not _benefic_aspect_on(chart, fifth):
        where = "in the 5th" if in_fifth else f"with the 5th lord ({fifth_lord})"
        return (Tagged(
            f"serpent-curse (sarpa-śrāpa): Rahu {where}, with no benefic aspect on the 5th — "
            "loss of issue by the serpents' curse of a past birth", "CLASSICAL_NONCITABLE",
            "PrasnaMarga-18:682"),)
    return ()


# ---------------------------------------------------------------------------
# BPHS Ch.83 curse-yogas — FAITHFUL per-verse encodings (replacing the earlier
# editorial proxy, which tested the 9th+Sun / 4th+Moon — a region BPHS-83's own
# verses never use; the father's curse is keyed to the 5th/Ascendant/Sun-as-5th-
# lord chains and the mother's to the 4th/5th/Moon chains).
#
# Sources: father's curse = vol2_chapter_083_i.md (verses 20.30, eleven numbered
# combinations, L33-93); mother's curse = vol2_chapter_083_ii.md (verses 34-50,
# thirteen numbered combinations, L114-166 — RECOVERED 2026-07-26 from the same
# archive.org scan the library's scrape drew from; the original scrape cut off at
# this section's heading). CLASSICAL_NONCITABLE throughout (BPHS is outside the
# live registry — the divergence firewall).
#
# ON RECORD, NOT ENCODED (each needs a primitive the engine lacks, or clean text):
#   father #1 (BPHS-83:33) and #2 (BPHS-83:36) — papakartari (hemmed between
#     malefics); the SYN_N6 precedent: recorded pending a hemming primitive.
#   mother #1's hemming DISJUNCT (BPHS-83-ii:114) — same; its debilitation
#     disjunct IS encoded below.
#   mother #9 (BPHS-83-ii:144) — hemming again.
#   mother #10 (BPHS-83-ii:148) — the OCR garbles the clause ("...and the lord of
#     the 4th and the Moon or in the 6th...") beyond honest reconstruction.
#   Praśna Mārga's own father's-curse variant (PrasnaMarga-18:695-696) — needs
#     Gulika, which this engine does not compute.
#
# INTERPRETATION CONVENTIONS (source-verified line by line, disclosed):
#   "associated with" a planet = co-occupancy of the same rasi house (the
#     conservative conjunction reading; the verses' association is samyoga, not
#     the wider conjunction-or-mutual-aspect sense `lords_associated` uses).
#   father #3's "the lord of the 5th is with the Sun" reads DEGENERATE-TRUE when
#     the 5th lord IS the Sun (Leo 5th, Aries ascendant) — the clause cannot
#     fail of itself there; firing then rests on the verse's other clauses.
#   mother #5's "associated with Saturn, Rahu and Mars; are in the 5th or the
#     9th" is encoded as all five bodies (5th lord, Moon, Saturn, Rahu, Mars)
#     within houses {5, 9} — marginally looser than requiring each malefic to
#     share the exact house of the 5th lord or Moon; the strict same-house
#     reading is a subset of what fires.
# ---------------------------------------------------------------------------

def _lord_of(chart: RamanChart, house: int) -> str:
    return SIGN_LORDS[_house_of_sign(chart.asc_sign, house)]


def _in_h(chart: RamanChart, planet: str, *houses: int) -> bool:
    return _planet_house(chart, planet) in houses


def _malefic_occupies(chart: RamanChart, house: int) -> bool:
    """"Occupied by malefics" — occupancy ONLY (the verses say occupied, not aspected)."""
    return any(n in NATURAL_MALEFICS for n in _occupants(chart, house))


def _assoc(chart: RamanChart, a: str, b: str) -> bool:
    ha, hb = _planet_house(chart, a), _planet_house(chart, b)
    return ha != 0 and ha == hb


def _with_malefics(chart: RamanChart, planet: str) -> bool:
    h = _planet_house(chart, planet)
    return h != 0 and any(n in NATURAL_MALEFICS and n != planet for n in _occupants(chart, h))


def _debil(chart: RamanChart, planet: str) -> bool:
    return planet in chart.planets and dignity(planet, chart) == "debil"


def _combust(chart: RamanChart, planet: str) -> bool:
    p = chart.planets.get(planet)
    return p is not None and p.combust_fraction >= 0.5   # lord_quality's own threshold


def _devoid_of_strength(chart: RamanChart, planet: str) -> bool:
    """"Devoid of strength" via Shadbala is_powerful — False (not fired) when Shadbala is
    unavailable (Track-B), never guessed."""
    from app.raman_saab.primitives.shadbala.total import is_powerful
    p = chart.planets.get(planet)
    if p is None or p.shadbala_rupas is None:
        return False
    return not is_powerful(planet, p.shadbala_rupas.total / 60.0)


def _malefic_navamsa(chart: RamanChart, planet: str) -> bool:
    """The planet's navamsa sign is ruled by a natural malefic ("in a malefic Navamsa")."""
    p = chart.planets.get(planet)
    return p is not None and SIGN_LORDS[p.navamsa_sign] in NATURAL_MALEFICS


def _malefic_sign(chart: RamanChart, planet: str) -> bool:
    """The planet's rasi sign is ruled by a natural malefic ("in a malefic sign")."""
    p = chart.planets.get(planet)
    return p is not None and SIGN_LORDS[p.sign] in NATURAL_MALEFICS


def _exchange(chart: RamanChart, h1: int, h2: int) -> bool:
    return (_in_h(chart, _lord_of(chart, h1), h2)
            and _in_h(chart, _lord_of(chart, h2), h1))


#: (verse-number-in-list, cite, source-faithful condition text, checker)
_FATHER_CURSE_YOGAS: Final[tuple[tuple[int, str, str], ...]] = (
    (3, "BPHS-83:41", "Jupiter in the Sun's sign, the 5th lord with the Sun, and the "
                      "Ascendant and the 5th occupied by malefics"),
    (4, "BPHS-83:47", "the Ascendant lord devoid of strength in the 5th, the 5th lord "
                      "combust, and the Ascendant and the 5th occupied by malefics"),
    (5, "BPHS-83:53", "exchange of houses between the 5th and 10th lords, and the Ascendant "
                      "and the 5th occupied by malefics"),
    (6, "BPHS-83:58", "Mars as 10th lord associated with the 5th lord, and the Ascendant, "
                      "the 5th and the 10th occupied by malefics"),
    (7, "BPHS-83:63", "the 10th lord in the 6th/8th/12th, Jupiter in a malefic sign, and the "
                      "Ascendant lord and the 5th lord associated with malefics"),
    (8, "BPHS-83:68", "the Sun in the Ascendant, Mars and Saturn in the 5th, Rahu in the 8th "
                      "and Jupiter in the 12th (the translator's stated reading of the verse)"),
    (9, "BPHS-83:85", "the Sun in the 8th, Saturn in the 5th, the 5th lord with Rahu, and a "
                      "malefic in the Ascendant"),
    (10, "BPHS-83:89", "the 12th lord in the Ascendant, the 8th lord in the 5th, and the "
                       "10th lord in the 8th"),
    (11, "BPHS-83:92", "the 6th lord in the 5th, the 10th lord in the 6th, and Jupiter "
                       "associated with Rahu"),
)


def _father_curse_fires(chart: RamanChart, num: int) -> bool:
    l5, l10 = _lord_of(chart, 5), _lord_of(chart, 10)
    if num == 3:
        jp = chart.planets.get("Jupiter")
        return (jp is not None and jp.sign == 5                      # Leo, the Sun's sign
                and _assoc(chart, l5, "Sun")
                and _malefic_occupies(chart, 1) and _malefic_occupies(chart, 5))
    if num == 4:
        l1 = _lord_of(chart, 1)
        return (_devoid_of_strength(chart, l1) and _in_h(chart, l1, 5)
                and _combust(chart, l5)
                and _malefic_occupies(chart, 1) and _malefic_occupies(chart, 5))
    if num == 5:
        return (_exchange(chart, 5, 10)
                and _malefic_occupies(chart, 1) and _malefic_occupies(chart, 5))
    if num == 6:
        return (l10 == "Mars" and _assoc(chart, "Mars", l5)
                and _malefic_occupies(chart, 1) and _malefic_occupies(chart, 5)
                and _malefic_occupies(chart, 10))
    if num == 7:
        return (_in_h(chart, l10, 6, 8, 12) and _malefic_sign(chart, "Jupiter")
                and _with_malefics(chart, _lord_of(chart, 1))
                and _with_malefics(chart, l5))
    if num == 8:
        return (_in_h(chart, "Sun", 1) and _in_h(chart, "Mars", 5)
                and _in_h(chart, "Saturn", 5) and _in_h(chart, "Rahu", 8)
                and _in_h(chart, "Jupiter", 12))
    if num == 9:
        return (_in_h(chart, "Sun", 8) and _in_h(chart, "Saturn", 5)
                and _assoc(chart, l5, "Rahu") and _malefic_occupies(chart, 1))
    if num == 10:
        return (_in_h(chart, _lord_of(chart, 12), 1)
                and _in_h(chart, _lord_of(chart, 8), 5) and _in_h(chart, l10, 8))
    if num == 11:
        return (_in_h(chart, _lord_of(chart, 6), 5) and _in_h(chart, l10, 6)
                and _assoc(chart, "Jupiter", "Rahu"))
    return False


_MOTHER_CURSE_YOGAS: Final[tuple[tuple[int, str, str], ...]] = (
    (1, "BPHS-83-ii:114", "the Moon as 5th lord in her sign of debilitation, and the 4th and "
                          "the 5th occupied by malefics (the verse's hemming disjunct is on "
                          "record, unencoded)"),
    (2, "BPHS-83-ii:118", "Saturn in the 11th, malefics in the 4th, and the Moon in the 5th "
                          "in her sign of debilitation"),
    (3, "BPHS-83-ii:121", "the 5th lord in the 6th/8th/12th, the Ascendant lord debilitated, "
                          "and the Moon associated with malefics"),
    (4, "BPHS-83-ii:125", "the 5th lord in the 8th/6th/12th, the Moon in a malefic Navamsa, "
                          "and malefics in the Ascendant and the 5th"),
    (5, "BPHS-83-ii:129", "the 5th lord and the Moon, with Saturn, Rahu and Mars, in the 5th "
                          "or the 9th"),
    (6, "BPHS-83-ii:132", "Mars as 4th lord associated with Saturn and Rahu, the Sun in the "
                          "5th and the Moon in the Ascendant"),
    (7, "BPHS-83-ii:136", "the Ascendant lord and the 5th lord in the 6th, the 4th lord in "
                          "the 8th, and the Ascendant occupied by the 8th and 10th lords"),
    (8, "BPHS-83-ii:140", "the Ascendant occupied by the 6th and 8th lords, the 4th lord in "
                          "the 12th, and the Moon and Jupiter, with malefics, in the 5th"),
    (11, "BPHS-83-ii:152", "the Cancer Ascendant occupied by Mars and Rahu, and the Moon and "
                           "Saturn in the 5th"),
    (12, "BPHS-83-ii:161", "Mars, Rahu, the Sun and Saturn in the Ascendant, 5th, 8th and "
                           "12th respectively, and the Ascendant and 4th lords in the "
                           "6th/8th/12th"),
    (13, "BPHS-83-ii:165", "Mars, Rahu and Jupiter in the 8th, and Saturn and the Moon in "
                           "the 5th"),
)


def _mother_curse_fires(chart: RamanChart, num: int) -> bool:
    l5, l4, l1 = _lord_of(chart, 5), _lord_of(chart, 4), _lord_of(chart, 1)
    if num == 1:
        return (l5 == "Moon" and _debil(chart, "Moon")
                and _malefic_occupies(chart, 4) and _malefic_occupies(chart, 5))
    if num == 2:
        return (_in_h(chart, "Saturn", 11) and _malefic_occupies(chart, 4)
                and _in_h(chart, "Moon", 5) and _debil(chart, "Moon"))
    if num == 3:
        return (_in_h(chart, l5, 6, 8, 12) and _debil(chart, l1)
                and _with_malefics(chart, "Moon"))
    if num == 4:
        return (_in_h(chart, l5, 6, 8, 12) and _malefic_navamsa(chart, "Moon")
                and _malefic_occupies(chart, 1) and _malefic_occupies(chart, 5))
    if num == 5:
        return (_in_h(chart, l5, 5, 9) and _in_h(chart, "Moon", 5, 9)
                and all(_in_h(chart, m, 5, 9) for m in ("Saturn", "Rahu", "Mars")))
    if num == 6:
        return (l4 == "Mars" and _assoc(chart, "Mars", "Saturn")
                and _assoc(chart, "Mars", "Rahu")
                and _in_h(chart, "Sun", 5) and _in_h(chart, "Moon", 1))
    if num == 7:
        return (_in_h(chart, l1, 6) and _in_h(chart, l5, 6) and _in_h(chart, l4, 8)
                and _in_h(chart, _lord_of(chart, 8), 1)
                and _in_h(chart, _lord_of(chart, 10), 1))
    if num == 8:
        return (_in_h(chart, _lord_of(chart, 6), 1) and _in_h(chart, _lord_of(chart, 8), 1)
                and _in_h(chart, l4, 12)
                and _in_h(chart, "Moon", 5) and _in_h(chart, "Jupiter", 5)
                and _malefic_occupies(chart, 5))
    if num == 11:
        return (chart.asc_sign == 4                                   # Cancer Ascendant
                and _in_h(chart, "Mars", 1) and _in_h(chart, "Rahu", 1)
                and _in_h(chart, "Moon", 5) and _in_h(chart, "Saturn", 5))
    if num == 12:
        return (_in_h(chart, "Mars", 1) and _in_h(chart, "Rahu", 5)
                and _in_h(chart, "Sun", 8) and _in_h(chart, "Saturn", 12)
                and _in_h(chart, l1, 6, 8, 12) and _in_h(chart, l4, 6, 8, 12))
    if num == 13:
        return (_in_h(chart, "Mars", 8) and _in_h(chart, "Rahu", 8)
                and _in_h(chart, "Jupiter", 8)
                and _in_h(chart, "Saturn", 5) and _in_h(chart, "Moon", 5))
    return False


def _bphs_curse_yogas(chart: RamanChart) -> tuple[Tagged, ...]:
    """Fire the encoded BPHS Ch.83 curse-yogas — one Tagged per fired verse, each naming its
    number and quoting its own condition, with a per-verse cite."""
    out: list[Tagged] = []
    for num, cite, text in _FATHER_CURSE_YOGAS:
        if _father_curse_fires(chart, num):
            out.append(Tagged(f"father's curse (pitṛ-śrāpa), BPHS verse-combination #{num}: "
                              f"{text} — want of male issue from the father's curse of a "
                              f"previous birth", "CLASSICAL_NONCITABLE", cite))
    for num, cite, text in _MOTHER_CURSE_YOGAS:
        if _mother_curse_fires(chart, num):
            out.append(Tagged(f"mother's curse (mātṛ-śrāpa), BPHS verse-combination #{num}: "
                              f"{text} — want of male issue from the mother's curse of a "
                              f"previous birth", "CLASSICAL_NONCITABLE", cite))
    return tuple(out)


def build_pitru_dosha_reading(chart: RamanChart) -> PitruDoshaReading:
    """Read the classical ancestral-curse yogas bearing on progeny/lineage, alongside Raman's own
    (authoritative) children verdict."""
    # kāraka-houses are counted as HOUSE NUMBERS (the occupancy/aspect helpers key on rasi_house,
    # where house 1 = the lagna). Signs are used only to name a house's lord.
    fifth_lord = SIGN_LORDS[_house_of_sign(chart.asc_sign, 5)]
    pf = judge_house(chart, 5)
    child_sv = next((s for s in pf.significations if s.signification == "children"), None)
    verdict = child_sv.verdict if child_sv else "insufficient-evidence"

    yogas: list[Tagged] = []
    yogas.extend(_serpent_curse(chart, 5, fifth_lord))
    # BPHS Ch.83's own numbered verse-combinations, encoded per verse (9 father + 11 mother;
    # the rest are on record — see the block comment above _FATHER_CURSE_YOGAS).
    yogas.extend(_bphs_curse_yogas(chart))

    pitru: list[Tagged] = [Tagged(
        f"pitṛ-sthāna (the 9th, {SIGN_LORDS[_house_of_sign(chart.asc_sign, 9)]}-ruled) — the "
        f"ancestral / past-life seat; kāraka Sun (pitṛ-kāraka)", "CLASSICAL_NONCITABLE", "BPHS-23:63")]
    nmal = _malefics_on(chart, 9)
    if nmal:
        pitru.append(Tagged(f"the 9th is afflicted by {', '.join(nmal)} — strain in the ancestral "
                            "line", "CLASSICAL_NONCITABLE", "BPHS-23:63"))

    notes = (
        Tagged(f"Raman's OWN method decides the children matter (5th + Beeja/Kṣetra + Navāṁśa); "
               f"his verdict here is {verdict.upper()}. The ancestral-curse yogas below are a "
               "classical CORROBORATING lens, never the verdict.", "RAMAN_EXPLICIT", "HTJAH-I:5018"),
        Tagged("Every curse-yoga here is CLASSICAL (BPHS / Praśna Mārga) — NOT Raman's live corpus; "
               "the firewall is intact, these are flagged classical, not live citations.",
               "CLASSICAL_NONCITABLE"),
        Tagged("The lineage vargas (D-45 father-line, D-40 mother-line, D-60 past-births; Rath/BPHS) "
               "deepen this thesis but lie beyond the engine's 16-varga range — noted, not computed.",
               "CLASSICAL_NONCITABLE"),
        Tagged("Classical remedy: śrāddha (ancestral rites), which the texts say 'prolongs the "
               "family lineage' (BPHS-83:107). An ancestral-karma reading is a contemplative lens "
               "with a remedy — never a decree, never medical advice.", "CLASSICAL_NONCITABLE",
               "BPHS-83:107"),
        Tagged("The curse-yogas above are BPHS Ch.83's OWN numbered verse-combinations, encoded "
               "per verse (father: 9 of 11 from BPHS-83:33-93; mother: 11 of 13 from the "
               "recovered BPHS-83-ii:114-166 block). ON RECORD, unencoded: father #1-2 and "
               "mother #9 (each needs a papakartari/hemming primitive the engine lacks — the "
               "SYN_N6 precedent), mother #1's hemming disjunct, mother #10 (OCR-garbled beyond "
               "honest reconstruction), and Praśna Mārga's father's-curse variant "
               "(PrasnaMarga-18:695-696 — needs Gulika, not computed). An earlier editorial "
               "proxy (9th+Sun / 4th+Moon malefic-touch) was RETIRED by this encoding: BPHS's "
               "own verses never use that region.", "CLASSICAL_NONCITABLE"),
        Tagged("A DIFFERENT LAYER, not a contradiction: these curse-yogas are narrow technical "
               "gates about PROGENY/lineage continuation, keyed by BPHS's own verses to the "
               "5th house/Ascendant chains (father) and the 4th/5th/Moon chains (mother) — "
               "they are not a judgment on your actual rapport with a living parent. The "
               "native's OWN standing with father and fortune (House 9) and mother and home "
               "(House 4) is judged separately in House-by-house reading and Your Reading, "
               "from those houses' own lord/karaka/aspects with many more factors weighed — "
               "so a favourable House 9 or 4 there can coexist with a curse-yoga firing here "
               "without contradiction.", "CLASSICAL_NONCITABLE"),
    )
    return PitruDoshaReading(raman_children_verdict=verdict, curse_yogas=tuple(yogas),
                             pitru_bhava=tuple(pitru), notes=notes)
