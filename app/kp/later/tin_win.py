"""Tin Win's KP House Grouping tables (KNR printed pp.70-91), the encodable rows (rulings LR8-LR10).

A later author's tables, not Krishnamurti's. The method is the author's own, from the page after
the tables (KNR scan 172): "if the cuspal sub lord of the house (mentioned in Column 1) is the
significator (by occupation or ownership at the planet, star and sub levels) of the house or
houses (mentioned in Column 4), then the event (shown in Column 3) is promised."

* LR8 (levels). "Planet, star and sub levels" = the houses the cusp sub-lord (CSL) itself
  occupies or owns (ladder levels B, D), those its star lord occupies or owns (A, C), and those
  its own sub-lord occupies or owns.
* LR9 (groups). A comma list needs ANY one house, as his worked example reads "2,7,11" ("signifies
  the required marriage houses 2 or 7 or 11"); "&" joins groups that must ALL be met; a remark that
  the houses "should operate jointly, not separately" needs two or more of them; a remark "not
  connected to ..." means none of those houses. Bracketed houses are not required: he never says
  what the brackets mean, and treating them as optional only drops a condition, never invents one.
* LR10 (left out). Rows that read the Lagna lord rather than a CSL, rows with alternatives ("or"),
  rows naming a planet, sign, Badhaka or Maraka, starred planet/sign conditions, death and danger to
  life (LR3), and moral character or punishment (LR7). Every row and its status is listed in
  ``docs/kp/KP_TIN_WIN_ROWS_2026-11-02.md``.

Column 5 (the houses whose joint period times the event) is listed there but not used.

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.later.tin_win import tin_win_indications
    for f in tin_win_indications(cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))):
        print(f.page, f.cusp, f.event, f.csl)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.chart import KPChart
from app.kp.later.citations import LATER_CITATIONS
from app.kp.later.tin_win_rows import ROWS
from app.kp.significators import Signification, planet_significations

CITATION: Final[str] = "KNR-tin_win_method"
FRAMING: Final[str] = ("Tin Win's House Grouping table (a later author, not Krishnamurti): what the "
                       "table says the configuration promises, not a validated prediction.")


@dataclass(frozen=True, slots=True)
class TinWinRow:
    row: int
    page: int
    cusp: int
    event: str
    groups: tuple[tuple[int, ...], ...]
    at_least_two: bool
    not_houses: tuple[int, ...]
    context: str


TIN_WIN_ROWS: Final[tuple[TinWinRow, ...]] = tuple(TinWinRow(*r) for r in ROWS)


@dataclass(frozen=True, slots=True)
class TinWinFired:
    row: int
    page: int
    cusp: int
    event: str
    csl: str
    houses: tuple[int, ...]
    context: str

    def to_dict(self) -> dict:
        return {"row": self.row, "page": self.page, "cusp": self.cusp, "event": self.event,
                "csl": self.csl, "houses": list(self.houses), "context": self.context,
                "author": "Tin Win", "citation": LATER_CITATIONS[CITATION].ref(), "framing": FRAMING}


def pss_houses(chart: KPChart, sigs: dict[str, tuple[Signification, ...]], csl: str) -> frozenset[int]:
    """Houses the CSL signifies at the planet, star and sub levels (ruling LR8)."""
    own = {s.house for s in sigs[csl] if s.level in "ABCD"}
    sub = chart.planets[csl].sub_lord
    return frozenset(own | {s.house for s in sigs[sub] if s.level in "BD"})


def row_holds(row: TinWinRow, houses: frozenset[int]) -> bool:
    """Ruling LR9: any house per group, all groups; two or more when 'jointly'; none of ``not``."""
    if houses & frozenset(row.not_houses):
        return False
    if row.at_least_two:
        return len(houses & frozenset(row.groups[0])) >= 2
    return all(houses & frozenset(g) for g in row.groups)


def tin_win_indications(chart: KPChart, *, context: str | None = None) -> tuple[TinWinFired, ...]:
    sigs = planet_significations(chart)
    out = []
    for r in TIN_WIN_ROWS:
        if context and r.context != context:
            continue
        csl = chart.cusp(r.cusp).sub_lord
        h = pss_houses(chart, sigs, csl)
        if row_holds(r, h):
            out.append(TinWinFired(r.row, r.page, r.cusp, r.event, csl, tuple(sorted(h)), r.context))
    return tuple(out)


__all__ = ["CITATION", "FRAMING", "TIN_WIN_ROWS", "TinWinFired", "TinWinRow", "pss_houses",
           "row_holds", "tin_win_indications"]
