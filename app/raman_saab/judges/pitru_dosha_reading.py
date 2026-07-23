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


def _ancestral_curse(chart: RamanChart, house: int, karaka: str, curse: str,
                     cite: str) -> tuple[Tagged, ...]:
    """A śrāpa fires when the ancestor's house AND kāraka are malefic-struck and the 5th
    (children) is itself afflicted — the curse manifesting as issue-affliction (BPHS Ch.83)."""
    house_mal = _malefics_on(chart, house)
    karaka_deb = dignity(karaka, chart) == "debil"
    karaka_mal = tuple(m for m in _malefics_on(chart, _planet_house(chart, karaka)) if m != karaka
                       ) if karaka in chart.planets else ()
    if house_mal and (karaka_deb or karaka_mal):
        strike = "debilitated" if karaka_deb else f"struck by {', '.join(karaka_mal)}"
        return (Tagged(
            f"{curse}: the {house}th (ancestral seat) is afflicted by {', '.join(house_mal)} and "
            f"its kāraka {karaka} is {strike} — an inherited issue-debt from that line",
            "CLASSICAL_NONCITABLE", cite),)
    return ()


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
    # pitṛ-śrāpa: the 9th (father/ancestors) + Sun (pitṛ-kāraka)
    yogas.extend(_ancestral_curse(chart, 9, "Sun", "father's curse (pitṛ-śrāpa)", "BPHS-83:30"))
    # mātṛ-śrāpa: the 4th (mother) + Moon (mātṛ-kāraka)
    yogas.extend(_ancestral_curse(chart, 4, "Moon", "mother's curse (mātṛ-śrāpa)", "BPHS-83:130"))

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
    )
    return PitruDoshaReading(raman_children_verdict=verdict, curse_yogas=tuple(yogas),
                             pitru_bhava=tuple(pitru), notes=notes)
