"""BPHS fidelity ledger — the parashara engine scored against Parashara's OWN worked results.

The Raman engine's headline (259/293 exact) is VERDICT accuracy against Raman's published chart-
verdict gallery: he printed hundreds of nativities with his judgment of each, and the engine is
scored against those judgments. BPHS gives no such gallery — it is a systematic treatise, not a book
of worked verdicts. So the faithful analog here is different IN KIND, and honestly so: it scores the
engine's reproduction of the concrete worked RESULTS Parashara (and the allied lineage) actually
printed — the Ahargana lords he computes, the ashtakavarga totals and trine reduction he tabulates,
the Vimshottari seed he specifies, the Uchcha value he works, the argala of his hypothetical chart.

Each ledger row is a number or lookup Parashara stated; the engine either reproduces it or it does
not. This is TEXTBOOK FIDELITY to Parashara's own arithmetic — the same category of claim as the
Raman ratchet's fidelity axis, and it carries the same caveat: it measures faithfulness to the text,
NOT validated prediction of real lives.

Usage:
    py -3.12 -m tools.parashara.fidelity_ledger        # prints the ledger + the headline figure
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import swisseph as swe

from app.parashara.chart.cast import cast
from app.parashara.chart.ephemeris import _WEEKDAY_LORD, _ahargana
from app.parashara.doctrine import argala, bhava_lord_effects
from app.parashara.doctrine.arudha import EXCEPTION_SOURCE, RULE_SOURCE, arudha_pada
from app.parashara.doctrine.functional_by_lagna import YOGAKARAKA_SOURCE, yogakaraka
from app.parashara.doctrine.sources import Citation, verify
from app.parashara.primitives import ashtakavarga as av
from app.parashara.primitives.longevity import (
    ASCENDANT_SOURCE,
    NISARGAYU_YEARS,
    YEARS_SOURCE,
    _ascendant_years_navamsa,
    _ascendant_years_rasi,
)
from app.parashara.primitives.shadbala.sthana import uchcha_bala
from app.parashara.primitives.upagrahas import SOURCE as UPAGRAHA_SOURCE, upagrahas
from app.parashara.primitives.vimshottari_dasha import seed as vim_seed


@dataclass(frozen=True)
class WorkedExample:
    name: str
    citation: Citation
    expected: Any
    compute: Callable[[], Any]

    def run(self) -> tuple[bool, Any]:
        got = self.compute()
        return got == self.expected, got


def _ahargana_lord(y: int, m: int, d: int, div: int, mult: int) -> str:
    a = _ahargana(int(swe.julday(y, m, d, 12.0, swe.GREG_CAL)) + 0.5)
    return _WEEKDAY_LORD[((a // div) * mult + 1) % 7 - 1]


def _canonical_signs() -> tuple[dict[str, int], int]:
    ch = cast(year=1990, month=7, day=15, hour=12, minute=0,
              tz_offset=5.5, latitude=12.97, longitude=77.59)
    return {g: int(ch.longitudes[g] % 360.0 // 30) + 1 for g in av.PLANETS}, ch.asc_sign


def _sun_bav_reduced() -> dict[int, int]:
    sun = {1: 4, 2: 3, 3: 4, 4: 6, 5: 5, 6: 2, 7: 3, 8: 6, 9: 5, 10: 5, 11: 3, 12: 2}
    return av.trikona_shodhana(sun)


def _argala_houses() -> set[int]:
    # BPHS-31's hypothetical Aries chart: Mars 4th, Sun+Mercury 2nd, Jupiter 11th give argala.
    ps = {"Mars": 4, "Sun": 2, "Mercury": 2, "Jupiter": 11}
    return {a.argala_house for a in argala.argala_for(1, ps)}


def ledger() -> list[WorkedExample]:
    """Every worked result Parashara (or the cited allied text) states that the engine reproduces."""
    signs, asc = _canonical_signs()
    rows: list[WorkedExample] = [
        WorkedExample("Ahargana Varsha lord (1 Jun 1984 -> Jupiter/Thu)",
                      Citation("BPHS-46", 128), "Jupiter",
                      lambda: _ahargana_lord(1984, 6, 1, 360, 3)),
        WorkedExample("Ahargana Masa lord (1 Jun 1984 -> Venus/Fri)",
                      Citation("BPHS-46", 128), "Venus",
                      lambda: _ahargana_lord(1984, 6, 1, 30, 2)),
        WorkedExample("Vimshottari seed (Revati/27 -> Mercury MD)",
                      Citation("BPHS-46", 128), "Mercury", lambda: vim_seed(27).lord),
        WorkedExample("Uchcha bala (152 deg 15' from debilitation -> 50.75)",
                      Citation("BPHS-27", 97), 50.75,
                      lambda: round(uchcha_bala("Sun", 37.75), 2)),
        WorkedExample("Trikona shodhana of the Sun's BAV (BPHS-67 worked table)",
                      Citation("BPHS-67", 530),
                      {1: 0, 2: 1, 3: 1, 4: 4, 5: 1, 6: 0, 7: 0, 8: 4, 9: 1, 10: 3, 11: 0, 12: 0},
                      _sun_bav_reduced),
        WorkedExample("Sarvashtakavarga total = 337",
                      Citation("BPHS-66", 199), 337,
                      lambda: sum(av.sarvashtakavarga(signs, asc_sign=asc).values())),
        WorkedExample("Bhava-lord effects fully catalogued (144/144)",
                      Citation("BPHS-24", 25), 144, lambda: len(bhava_lord_effects.all_effects())),
        WorkedExample("Argala on the ascendant (BPHS-31 hypothetical chart)",
                      Citation("BPHS-31", 62), {2, 4, 11}, _argala_houses),
        # Arudha padas — Parashara's four worked examples (ch.29).
        WorkedExample("Arudha base (Scorpio asc, Mars in Cancer -> Pisces)",
                      RULE_SOURCE, 12, lambda: arudha_pada(8, 4)),
        WorkedExample("Arudha exception, lord in 1st (Jupiter in Sagittarius -> Virgo)",
                      EXCEPTION_SOURCE, 6, lambda: arudha_pada(9, 9)),
        WorkedExample("Arudha exception, lord in 7th (Saturn in Leo, Aquarius asc -> Taurus)",
                      EXCEPTION_SOURCE, 2, lambda: arudha_pada(11, 5)),
        WorkedExample("Arudha exception, lord in 4th (Sun in Scorpio, Leo asc -> the 4th)",
                      EXCEPTION_SOURCE, 8, lambda: arudha_pada(5, 8)),
        # Nisargayu — the ascendant contribution's two cases (ch.43).
        WorkedExample("Nisargayu ascendant, navamsa case (Cancer navamsa, asc 0-48-34 -> 3.2428)",
                      ASCENDANT_SOURCE, 3.2428,
                      lambda: round(_ascendant_years_navamsa(4, 0 + 48 / 60 + 34 / 3600), 4)),
        WorkedExample("Nisargayu ascendant, rasi case (Sagittarius asc -> 8 years)",
                      ASCENDANT_SOURCE, 8.0, lambda: _ascendant_years_rasi(9, 0.0)),
        WorkedExample("Nisargayu allotment sums to the 120-year lifespan",
                      YEARS_SOURCE, 120, lambda: int(sum(NISARGAYU_YEARS.values()))),
        # Upagrahas — Parashara's closing identity (ch.3): Upaketu + 1 sign == the Sun.
        WorkedExample("Upagraha chain closes (Upaketu + 1 sign == Sun, at Sun 132 deg)",
                      UPAGRAHA_SOURCE, 132.0,
                      lambda: round((upagrahas(132.0)["Upaketu"] + 30.0) % 360.0, 4)),
        # Functional nature — the 12-lagna yogakaraka key (ch.34): Mars for Cancer lagna.
        WorkedExample("Yogakaraka for Cancer lagna -> Mars",
                      YOGAKARAKA_SOURCE, ("Mars",), lambda: yogakaraka(4)),
    ]
    # Each planet's canonical Bhinnashtakavarga total (Sun 48 ... Saturn 39).
    for planet, total in av.BAV_TOTALS.items():
        rows.append(WorkedExample(
            f"Bhinnashtakavarga total: {planet} = {total}", Citation("BPHS-66", 199), total,
            lambda p=planet: sum(av.bhinnashtakavarga(p, signs, asc_sign=asc).values())))
    return rows


def summary() -> tuple[int, int, list[tuple[str, bool, Any, Any]]]:
    """(reproduced, total, [(name, ok, expected, got)])."""
    detail: list[tuple[str, bool, Any, Any]] = []
    reproduced = 0
    for ex in ledger():
        ok, got = ex.run()
        reproduced += int(ok)
        detail.append((ex.name, ok, ex.expected, got))
    return reproduced, len(detail), detail


def main() -> None:
    reproduced, total, detail = summary()
    for name, ok, expected, got in detail:
        mark = "OK " if ok else "XX "
        extra = "" if ok else f"   expected={expected!r} got={got!r}"
        print(f"  {mark}{name}{extra}")
    cites_ok = all(verify(ex.citation) for ex in ledger())
    print(f"\n[bphs-fidelity] reproduced={reproduced}/{total} of Parashara's own worked results; "
          f"citations_resolve={cites_ok}")
    print("(textbook fidelity to Parashara's stated arithmetic — NOT validated prediction of lives)")


if __name__ == "__main__":
    main()
