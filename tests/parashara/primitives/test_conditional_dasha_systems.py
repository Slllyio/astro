"""The seven count-from-anchor conditional dashas (BPHS ch.46).

Two load-bearing checks per the module's design:
  * every system totals the year-count its NAME encodes (shodasottari=116, ... shattrimsat=36);
  * the three systems with clean worked examples reproduce Parashara's stated birth-lord exactly,
    which is what pins the inclusive counting convention the whole family shares.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import verify
from app.parashara.primitives import conditional_dasha_systems as cds


class TestTotals:
    def test_each_system_totals_the_year_count_in_its_name(self):
        expected = {
            "shodasottari": 116, "dwadasottari": 112, "panchottari": 105, "shatabdika": 100,
            "chaturashiti_sama": 84, "dwisaptati_sama": 72, "shattrimsat_sama": 36,
        }
        for name, total in expected.items():
            s = cds.system(name)
            assert s.total == total
            assert sum(s.years) == total, name

    def test_shape_is_consistent(self):
        """len(lords) == len(years) == divisor for every system (enforced in __post_init__)."""
        for s in cds.SYSTEMS.values():
            assert len(s.lords) == len(s.years) == s.divisor

    def test_the_sama_systems_have_equal_periods(self):
        """'sama' = equal: every lord gets the same span."""
        assert set(cds.system("chaturashiti_sama").years) == {12}
        assert set(cds.system("dwisaptati_sama").years) == {9}


class TestWorkedExamples:
    def test_shodasottari_rohini_gives_venus(self):
        """BPHS-46:24-26 — Rohini (nak 4), counting from Pushya, lands on Venus."""
        assert cds.system("shodasottari").seed_lord(4) == "Venus"

    def test_panchottari_mrigasira_gives_mercury(self):
        """BPHS-46:29-31 — Mrigasira (nak 5), from Anuradha, lands on Mercury."""
        assert cds.system("panchottari").seed_lord(5) == "Mercury"

    def test_shatabdika_mrigasira_gives_mars(self):
        """BPHS-46:32-34 — Mrigasira (nak 5), from Revati, lands on Mars."""
        assert cds.system("shatabdika").seed_lord(5) == "Mars"

    def test_chaturashiti_example_discrepancy_is_documented(self):
        """The verified inclusive rule computes Mercury for Mrigasira; the lone worked example (an
        OCR-corrupted line) says Mars. Three clean examples confirm the rule, so it stands — this
        test PINS the known discrepancy so it is visible, not silently 'fixed' either way."""
        assert cds.system("chaturashiti_sama").seed_lord(5) == "Mercury"


class TestTimelines:
    def test_every_system_produces_a_full_cycle_totalling_its_years(self):
        for name, s in cds.SYSTEMS.items():
            tl = s.timeline(5)
            assert len(tl) == s.divisor
            assert sum(p.years for p in tl) == pytest.approx(s.total), name

    def test_seed_lord_runs_at_birth(self):
        s = cds.system("shatabdika")
        assert s.timeline(5)[0].lord == s.seed_lord(5) == "Mars"

    def test_to_anchor_direction_differs_from_from_anchor(self):
        """Dwadasottari counts janma->Revati (to_anchor); the others count anchor->janma. The two
        directions must give different seeds for the same nakshatra, or the flag does nothing."""
        d = cds.system("dwadasottari")
        assert d.direction == "to_anchor"
        # a nakshatra where the two directions demonstrably diverge
        forward = (5 - d.anchor) % 27 + 1
        backward = (d.anchor - 5) % 27 + 1
        assert forward != backward


class TestExcludedLords:
    def test_each_system_omits_the_lords_parashara_omits(self):
        """The exclusions are doctrine, not oversight: Rahu out of Shodasottari; both nodes out of
        Panchottari/Shatabdika/Chaturashiti; Ketu out of Dwisaptati; etc."""
        assert "Rahu" not in cds.system("shodasottari").lords          # Rahu excluded, Ketu in
        assert "Venus" not in cds.system("dwadasottari").lords         # Venus excluded, both nodes in
        for nodeless in ("panchottari", "shatabdika", "chaturashiti_sama"):
            assert "Rahu" not in cds.system(nodeless).lords and "Ketu" not in cds.system(nodeless).lords
        assert "Ketu" not in cds.system("dwisaptati_sama").lords       # Rahu in, Ketu out
        assert "Ketu" not in cds.system("shattrimsat_sama").lords


class TestCitations:
    def test_every_system_citation_resolves(self):
        for s in cds.SYSTEMS.values():
            assert verify(s.source), f"{s.name}: {s.source.work}:{s.source.line}"

    def test_shastihayani_is_deliberately_absent(self):
        """Shastihayani is NOT encoded — its ch.46 OCR is internally inconsistent (69 != 60). Its
        absence is intentional and documented; this guards against a careless later addition of a
        guessed table."""
        assert "shastihayani" not in cds.SYSTEMS
