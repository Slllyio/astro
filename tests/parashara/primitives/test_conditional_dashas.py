"""Conditional dashas (BPHS ch.46) — the flagship BPHS capability the Raman engine lacks.

Load-bearing checks: each system totals its defining constant (108 Ashtottari, 36 Yogini), and the
seed reproduces Parashara's OWN worked example where he gives one (Yogini: Mrigasira -> Sankata).
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import passage, verify
from app.parashara.primitives import ashtottari_dasha as ash
from app.parashara.primitives import yogini_dasha as yog
from app.parashara.primitives.nakshatra_dasha import dasha_timeline, total_years


class TestFramework:
    def test_first_period_is_the_seed_and_partially_elapsed(self):
        cycle = (("A", 10.0), ("B", 20.0), ("C", 30.0))
        tl = dasha_timeline(cycle, start_index=1, elapsed_fraction=0.5)
        assert tl[0].lord == "B"
        # half of B's 20 remains at birth
        assert tl[0].end_year == pytest.approx(10.0)
        assert tl[1].lord == "C" and tl[1].start_year == pytest.approx(10.0)
        assert tl[-1].lord == "A"

    def test_wraps_once_through_the_whole_cycle(self):
        cycle = (("A", 10.0), ("B", 20.0), ("C", 30.0))
        tl = dasha_timeline(cycle, start_index=2)
        assert [p.lord for p in tl] == ["C", "A", "B"]

    def test_rejects_bad_inputs(self):
        cycle = (("A", 10.0),)
        with pytest.raises(ValueError):
            dasha_timeline(cycle, start_index=3)
        with pytest.raises(ValueError):
            dasha_timeline(cycle, start_index=0, elapsed_fraction=1.0)


class TestYogini:
    def test_totals_thirty_six_years(self):
        assert total_years(yog.CYCLE) == 36 == yog.TOTAL_YEARS

    def test_the_eight_yoginis_and_their_lords(self):
        """BPHS-46:199 — Mangala/Moon, Pingala/Sun, Dhanya/Jupiter, Bhramari/Mars, Bhadrika/Mercury,
        Ulka/Saturn, Siddha/Venus, Sankata/Rahu; years 1..8."""
        assert [y[0] for y in yog.YOGINIS] == [
            "Mangala", "Pingala", "Dhanya", "Bhramari", "Bhadrika", "Ulka", "Siddha", "Sankata"]
        assert [y[1] for y in yog.YOGINIS] == [
            "Moon", "Sun", "Jupiter", "Mars", "Mercury", "Saturn", "Venus", "Rahu"]
        assert [y[2] for y in yog.YOGINIS] == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_parasharas_own_worked_example(self):
        """BPHS-46:199 — 'The Janma Nakshatra is Mrigasira. Its number is 5. Adding 3 we get 8.
        Dividing 8 by 8 we get zero remainder ... the 8th Yogini, namely Sankata.'"""
        s = yog.seed(5)   # Mrigasira
        assert s.yogini == "Sankata" and s.lord == "Rahu"

    def test_seed_remainder_mapping(self):
        assert yog.seed(1).yogini == "Bhramari"    # (1+3)%8 = 4 -> Bhramari
        assert yog.seed(4).yogini == "Siddha"      # (4+3)%8 = 7 -> Siddha
        assert yog.seed(5).yogini == "Sankata"     # (5+3)%8 = 0 -> 8th

    def test_timeline_covers_all_eight_and_totals_36(self):
        tl = yog.timeline(5)
        assert len(tl) == 8
        assert tl[0].lord == "Rahu"                # Sankata's lord runs at birth
        assert sum(p.years for p in tl) == 36

    def test_source_resolves(self):
        assert verify(yog.SOURCE)
        assert "Yogini" in passage("BPHS-46:5789")["text"]


class TestAshtottari:
    def test_totals_one_hundred_eight_years(self):
        assert total_years(ash.CYCLE) == 108 == ash.TOTAL_YEARS

    def test_lord_years_are_the_sloka_verbatim(self):
        """BPHS-46:1627 — Sun 6, Moon 15, Mars 8, Mercury 17, Saturn 10, Jupiter 19, Rahu 12,
        Venus 21; Ketu excluded."""
        assert dict(ash.CYCLE) == {
            "Sun": 6, "Moon": 15, "Mars": 8, "Mercury": 17,
            "Saturn": 10, "Jupiter": 19, "Rahu": 12, "Venus": 21}
        assert "Ketu" not in dict(ash.CYCLE)

    def test_seed_starts_the_sun_at_ardra(self):
        """sl.17-20 — 'From 4 nakshatras from Ardra commences the Dasa of the Sun.' Ardra is the
        6th nakshatra, and the first four (Ardra..Pushya) are the Sun's."""
        for nak in (6, 7, 8, 9):        # Ardra, Punarvasu, Pushya, Ashlesha
            assert ash.seed(nak).lord == "Sun", nak
        assert ash.seed(10).lord == "Moon"   # the next 3 begin the Moon

    def test_seed_group_sizes_follow_4_3_4_3(self):
        """The lords cycle through the nakshatras in groups of 4,3,4,3,4,3,4,3 = 28."""
        counts = {}
        for nak in range(1, 28):        # 27 real nakshatras
            counts[ash.seed(nak).lord] = counts.get(ash.seed(nak).lord, 0) + 1
        counts[ash.seed(1, is_abhijit=True).lord] = counts.get(
            ash.seed(1, is_abhijit=True).lord, 0) + 1
        # 28 nakshatra-slots distributed as the group sizes
        assert sorted(counts.values()) == [3, 3, 3, 3, 4, 4, 4, 4]

    def test_timeline_covers_eight_lords_and_totals_108(self):
        tl = ash.timeline(6)            # Ardra -> Sun at birth
        assert len(tl) == 8
        assert tl[0].lord == "Sun"
        assert sum(p.years for p in tl) == 108

    def test_applicability_rule(self):
        """Adopt when Rahu is NOT in Lagna/Kendra and NOT in a trikona from the lagna lord."""
        assert ash.is_applicable(rahu_house_from_lagna=3, rahu_house_from_lagna_lord=6) is True
        assert ash.is_applicable(rahu_house_from_lagna=1, rahu_house_from_lagna_lord=6) is False  # lagna
        assert ash.is_applicable(rahu_house_from_lagna=7, rahu_house_from_lagna_lord=6) is False  # kendra
        assert ash.is_applicable(rahu_house_from_lagna=3, rahu_house_from_lagna_lord=5) is False  # trikona/lord

    def test_sources_resolve(self):
        assert verify(ash.SOURCE) and verify(ash.APPLICABILITY_SOURCE)
        assert "Astottari" in passage("BPHS-46:1627")["text"] or \
               "108" in passage("BPHS-46:1627")["text"]
