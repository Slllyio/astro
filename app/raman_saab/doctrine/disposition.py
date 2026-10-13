"""Disposition of a graha -- Raman's FORTIFIED / AFFLICTED axis, which is INFLUENCE, not strength.

Raman defines the words himself: "If the Moon is fortified, that is well aspected or conjoined"
(HTJAH-I:4283); "fortified, i.e., joined with or aspected by benefices" (HTJAH-I:2338);
"afflicted, by aspect or association, by malefic planets" (HTJAH-I:8434); a table closes on "the
benefic, malefic, or moderating nature of the lord qualified or modified otherwise by the
association or aspect of the other planets" (HTJAH-I:5173-5175). Strength is a separate axis:
"Venus is the strongest planet ... and even he is afflicted" (NH:14852-14854). Two independent
engine-blind reviews agreed on all of this (2026-10-13).

**Fortification and affliction are two flags, not one netted score.** Raman writes "fortification
as well as affliction" of one planet (NH:2843-2846), and when he calls a planet afflicted he names
the malefic contact and does not net it against good ones. This was MEASURED: a netted draft (with
dispositor, Jupiter-relief and per-Lagna-table rescues) agreed with 8 of 10 of his "fortified"
calls but only 2 of 13 "afflicted" calls on a 23-case holdout (DOCTRINE_BACKLOG "Disposition").

- AFFLICTED: joined or aspected by a natural malefic -- Sun, Mars, Saturn, Rahu, Ketu (HTJAH-I:8434;
  "considerably afflicted by his conjunction with Mars", NH:1335-1336; association with Rahu,
  NH:6262). The Lagna lord is NOT exempt here, unlike for a HOUSE (conditions.HouseAfflictedBy):
  Raman blames a malefic Lagna lord for afflicting a planet in his worked charts ("affliction of
  the 5th lord ... by Mars", Aries Lagna, HTJAH-I:5925-5937; Saturn's aspect a blemish for
  Aquarius, HTJAH-I:5641-5643) though he also writes it "does not afflict in the strict sense"
  (HTJAH-I:13193-13194). Being also a fortifier (below), it sets BOTH flags -- "mixed", never the
  opposite of either reading. Otherwise: combust anywhere inside the orb
  (HTJAH-II:4067-4076; NH:15229-15231); hemmed between malefics (HTJAH-I:6777) unless a benefic
  joins or aspects it ("Jupiter's aspect or association will however counteract", HTJAH-I:2532).
- FORTIFIED: joined or aspected by Jupiter or Venus (HTJAH-I:2338), by a functional benefic or
  yogakaraka ("Jupiter and Mars are functional benefics and their aspects fortify", HTJAH-II:1113),
  by its own dispositor ("it only strengthens", HTJAH-I:13221-13222) or by the Lagna lord
  (NH:15662-15665); exalted, own sign or moolatrikona (HTJAH-I:2339-2340); in its own nakshatra
  (HTJAH-I:13282; NH:13093).

A natural malefic that also fortifies (a functional benefic, the dispositor) sets BOTH flags:
the measure reports what Raman would point to and does not decide between them. Raman prints no
scoring rule for weighing the two ("moderately good, mixed results", HTJAH-I:5117), so a caller
should show a conditioned reading only when exactly one flag is set.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti, hemming
from app.raman_saab.primitives import nakshatra
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import functional_nature

_NODES = ("Rahu", "Ketu")
_NATURAL_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
_FIRM_BENEFICS = frozenset({"Jupiter", "Venus"})


@dataclass(frozen=True)
class Disposition:
    planet: str
    good: tuple[str, ...]
    bad: tuple[str, ...]

    @property
    def reading(self) -> str:
        """'good' | 'bad' | 'mixed' | 'none' -- only one flag set gives a clear reading."""
        if self.good and self.bad:
            return "mixed"
        return "good" if self.good else "bad" if self.bad else "none"


def _afflicts(other: str) -> bool:
    return other in _NATURAL_MALEFICS


def _fortifies(other: str, subject: str, chart: RamanChart) -> bool:
    return (other in _FIRM_BENEFICS
            or other == SIGN_LORDS[chart.planets[subject].sign]
            or other == SIGN_LORDS[chart.asc_sign]
            or (other not in _NODES
                and functional_nature(other, chart) in ("benefic", "yogakaraka")))


def disposition(planet: str, chart: RamanChart) -> Disposition | None:
    """Raman's disposition of `planet`, or None when it is absent from the chart."""
    p = chart.planets.get(planet)
    if p is None:
        return None
    good: list[str] = []
    bad: list[str] = []
    benefic_contact = False
    for other, q in chart.planets.items():
        if other == planet:
            continue
        how = ("joined by" if q.rasi_house == p.rasi_house
               else "aspected by" if drishti.aspects_planet(other, planet, chart) else None)
        if how is None:
            continue
        benefic_contact = benefic_contact or other in _FIRM_BENEFICS
        if _afflicts(other):
            bad.append(f"{how} {other}")
        if _fortifies(other, planet, chart):
            good.append(f"{how} {other}")
    if planet not in _NODES:
        d = dignity(planet, chart)
        if d in ("exalt", "own", "moolatrikona"):
            good.append(f"dignity: {d}")
        if p.nakshatra is not None and nakshatra.nakshatra_lord(p.nakshatra) == planet:
            good.append("in its own nakshatra")
        if planet != "Sun" and p.combust_fraction > 0.0:
            bad.append("combust")
    if hemming.hemmed_planet(chart, planet, "malefic") and not benefic_contact:
        bad.append("hemmed between malefics")
    return Disposition(planet, tuple(good), tuple(bad))
