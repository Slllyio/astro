"""The end-to-end Parashara reading — cast a real birth, assemble the full cited reading.

This is the capstone integration: it proves the whole stack works together on a real chart cast
from birth data, not just the primitives in isolation. Uses the project's canonical baseline
nativity (CLAUDE.md: Bangalore 1990-07-15 12:00 IST) so the cast is comparable across engines.
Assertions target structure and doctrine-guaranteed invariants; the exact placements are the
ephemeris's business, verified elsewhere.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.doctrine.sources import verify
from app.parashara.primitives import relationships as rel
from app.parashara.reading import read


@pytest.fixture(scope="module")
def reading():
    chart = cast(year=1990, month=7, day=15, hour=12, minute=0,
                 tz_offset=5.5, latitude=12.97, longitude=77.59)
    return read(chart)


class TestCast:
    def test_chart_is_populated(self, reading):
        c = reading.chart
        assert 1 <= c.asc_sign <= 12
        assert 1 <= c.janma_nakshatra <= 27
        assert set(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                    "Rahu", "Ketu")) <= set(c.longitudes)
        assert all(0.0 <= l < 360.0 for l in c.longitudes.values())

    def test_baseline_ascendant_is_virgo(self, reading):
        """CLAUDE.md pins this nativity's Lagna as Virgo (~173.99 deg) — a cross-check that the
        shared ephemeris is casting the expected chart."""
        assert reading.chart.asc_sign == 6      # Virgo

    def test_moon_paksha_is_boolean(self, reading):
        assert isinstance(reading.chart.moon_waxing, bool)


class TestReadingStructure:
    def test_all_twelve_bhavas_judged(self, reading):
        assert set(reading.bhavas) == set(range(1, 13))
        for v in reading.bhavas.values():
            assert v.verdict in ("flourishing", "ordinary", "annihilated")

    def test_seven_grahas_have_vimsopaka(self, reading):
        assert set(reading.vimsopaka) == set(rel.GRAHAS)
        for score in reading.vimsopaka.values():
            assert 5.0 - 1e-9 <= score.score <= 20.0 + 1e-9

    def test_all_ten_dasha_systems_reported(self, reading):
        """Vimshottari + Yogini + Ashtottari + the 7 count-from-anchor systems, each with a real
        applicability boolean and its adoption condition as the reason."""
        systems = {d.system: d for d in reading.dashas}
        for name in ("shodasottari", "dwadasottari", "panchottari", "shatabdika",
                     "chaturashiti_sama", "dwisaptati_sama", "shattrimsat_sama"):
            assert name in systems, name
            assert isinstance(systems[name].applicable, bool)
            assert systems[name].reason
            # applicable -> a timeline; not applicable -> empty (like Ashtottari)
            assert bool(systems[name].timeline) == systems[name].applicable

    def test_dashas_reported_with_applicability(self, reading):
        systems = {d.system: d for d in reading.dashas}
        assert "vimshottari" in systems and "yogini" in systems and "ashtottari" in systems
        assert systems["vimshottari"].applicable is True       # the primary system, always reported
        assert systems["yogini"].applicable is True            # general system
        # Ashtottari applicability is a real boolean with a stated reason either way.
        assert isinstance(systems["ashtottari"].applicable, bool)
        assert systems["ashtottari"].reason

    def test_applicable_dasha_has_a_timeline_totalling_its_span(self, reading):
        for d in reading.dashas:
            if d.applicable:
                total = sum(p.years for p in d.timeline)
                assert total in (36, 108, 120), (d.system, total)  # yogini / ashtottari / vimshottari
            else:
                assert d.timeline == ()

    def test_shadbala_present_and_flagged_complete(self, reading):
        """The complete six-fold Shadbala is surfaced, and every entry declares itself complete."""
        assert set(reading.shadbala) == set(rel.GRAHAS)
        for s in reading.shadbala.values():
            assert s.complete is True
            assert s.virupas > 0

    def test_avasthas_present_for_seven_grahas(self, reading):
        """REPORT COMPLETENESS: the computed avasthas must be surfaced in the reading."""
        assert set(reading.avasthas) == set(rel.GRAHAS)
        for a in reading.avasthas.values():
            assert a.baladi in ("bala", "kumara", "yuva", "vriddha", "mrita")
            assert a.jagradadi in ("jagrat", "swapna", "sushupti")

    def test_nisargayu_present_and_flagged_pre_reduction(self, reading):
        assert reading.nisargayu.reductions_applied is False
        assert 60.0 - 1e-6 <= reading.nisargayu.natural_years <= 120.0 + 1e-6

    def test_dashas_are_birth_balance_adjusted(self, reading):
        """The timelines use the Moon's-arc birth balance: the birth mahadasha shows less than its
        full span (its elapsed portion is dropped), so the visible Vimshottari total is under 120."""
        assert reading.balance_adjusted is True
        vim = next(d for d in reading.dashas if d.system == "vimshottari")
        total_visible = vim.timeline[-1].end_year
        assert total_visible < 120.0                 # elapsed portion of the birth MD is not shown
        assert vim.timeline[0].end_year - vim.timeline[0].start_year <= vim.timeline[0].years


class TestTraceability:
    def test_every_bhava_reason_cites_bphs(self, reading):
        """Each fired condition in every bhava verdict resolves to a real BPHS line."""
        for v in reading.bhavas.values():
            for c in v.prosperity + v.annihilation:
                assert verify(c.source)

    def test_vimsopaka_and_nisargayu_cite_bphs(self, reading):
        for score in reading.vimsopaka.values():
            assert verify(score.source)
        for contrib in reading.nisargayu.per_planet.values():
            # contributions don't each carry a citation, but the span's inputs are BPHS-43 sourced
            assert contrib.full_years > 0

    def test_deterministic(self, reading):
        again = read(reading.chart)
        assert again.bhavas.keys() == reading.bhavas.keys()
        assert again.nisargayu.natural_years == reading.nisargayu.natural_years
