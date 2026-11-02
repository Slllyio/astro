"""Krishnamurti's selection of strong and fruitful significators (rulings R24-R26)."""

from __future__ import annotations

import pytest

from app.kp.chart import Birth, cast
from app.kp.citations import CITATIONS
from app.kp.judgment import timing_windows
from app.kp.selection import CITATIONS as SEL_CITES
from app.kp.selection import select, selected_windows, strong_from

BANGALORE = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)
ALIBAG = Birth(1924, 12, 23, 21, 0, tz=5.5, lat=18 + 39 / 60, lon=72 + 55 / 60)
JUDGED = Birth(2026, 11, 2, 10, 0, tz=5.5, lat=12.97, lon=77.59)
PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def _pairs(strong) -> set[tuple[str, int]]:
    return {(s.planet, s.house) for s in strong}


class TestStrongOnPrintedExamples:
    def test_reader5_occupant_stars(self) -> None:
        """KPR5 pp.208-209: Kethu (Karthik), Venus (Uthraphalguni) and Moon (Uthrashada) are in Sun's star, so
        they, not Sun as occupant, give 2nd-house results; Jupiter is among the planets 'in the constellation
        of the occupants of 2nd Bhava'; no planet is in Moon's star, so Moon is strong for the 4th."""
        star = {"Ketu": "Sun", "Venus": "Sun", "Moon": "Sun", "Sun": "Rahu", "Mercury": "Jupiter",
                "Rahu": "Jupiter", "Jupiter": "Mercury", "Saturn": "Venus", "Mars": "Venus"}
        occ = {2: ("Sun", "Rahu", "Mercury"), 4: ("Moon",)}
        strong = strong_from((2, 4), occ, {2: "Venus", 4: "Jupiter"}, star, {})
        got = _pairs(strong)
        assert {("Ketu", 2), ("Venus", 2), ("Moon", 2), ("Jupiter", 2), ("Moon", 4)} <= got
        assert ("Jupiter", 4) not in got
        sun = next(s for s in strong if (s.planet, s.house) == ("Sun", 2))
        assert sun.why.startswith("in the star of Rahu")  # Sun counts only as a dweller of Rahu's star

    def test_reader4_marriage_significators(self) -> None:
        """KPR4 p.190: Mercury lord of 2 in 2 with no planet in its star; 7 empty, lord Saturn with no planet in
        its star, Kethu represents Saturn and Rahu is in Kethu's star; Jupiter in 11 in its own star alone.
        'Hence Rahu, Kethu, Sani, Jupiter are the significators.'"""
        star = {p: "Venus" for p in PLANETS}  # any star other than the ones the text names
        star |= {"Rahu": "Ketu", "Jupiter": "Jupiter"}
        got = _pairs(strong_from((2, 7, 11), {2: ("Mercury",), 11: ("Jupiter",)},
                                 {2: "Mercury", 7: "Saturn", 11: "Venus"}, star, {"Ketu": ("Saturn",)}))
        assert got == {("Mercury", 2), ("Saturn", 7), ("Ketu", 7), ("Rahu", 7), ("Jupiter", 11)}

    def test_lord_with_star_dwellers_is_not_strong(self) -> None:
        """KPR5 p.147: an empty house goes to the planets in its lord's stars, the lord only if there are none."""
        star = {p: "Moon" for p in PLANETS} | {"Mars": "Sun", "Venus": "Sun"}
        got = _pairs(strong_from((1,), {}, {1: "Sun"}, star, {}))
        assert got == {("Mars", 1), ("Venus", 1)}


@pytest.mark.parametrize("birth", [BANGALORE, ALIBAG])
@pytest.mark.parametrize("matter", ["marriage", "children", "service", "health", "house4"])
class TestSelection:
    def test_selected_are_fruitful_significators(self, birth: Birth, matter: str) -> None:
        """Every selected planet signifies the matter and its sub-lord signifies a favourable house (R25)."""
        s = select(cast(birth), matter)
        for p in s.selected:
            assert p in s.significators and s.fruit[p].fruitful

    def test_ruling_planets_only_narrow(self, birth: Birth, matter: str) -> None:
        """With a moment of judgment, the selection is the R25 set cut down to ruling planets (R26)."""
        c = cast(birth)
        loose, tight = select(c, matter), select(c, matter, judged=JUDGED)
        assert set(tight.selected) == set(loose.selected) & set(tight.ruling)

    def test_windows_are_a_subset_of_r17(self, birth: Birth, matter: str) -> None:
        """Selected windows are R17 candidates whose three lords all survived the selection."""
        c = cast(birth)
        a, b = c.jd_ut + 20 * 365.2425, c.jd_ut + 40 * 365.2425
        base = {w.period.lords for w in timing_windows(c, matter, a, b)}
        sel = set(select(c, matter).selected)
        for w in selected_windows(c, matter, a, b):
            assert w.period.lords in base and set(w.period.lords) <= sel


def test_every_selection_citation_exists() -> None:
    """Each citation the selection names is in the verified citation table."""
    assert all(k in CITATIONS for k in SEL_CITES)


@pytest.mark.parametrize("birth", [BANGALORE, ALIBAG])
def test_flags_never_filter(birth: Birth) -> None:
    """Saturn-delay and retrograde flags describe the selected set; they never remove a planet."""
    c = cast(birth)
    for m in ("marriage", "children", "service"):
        s = select(c, m)
        assert s.delay == ("Saturn" in s.selected)
        assert set(s.retrograde) <= set(s.selected)
        for p in s.retrograde:
            assert c.planets[p].retrograde or c.planets[c.planets[p].star_lord].retrograde
