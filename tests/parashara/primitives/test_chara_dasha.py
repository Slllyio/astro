"""Chara dasha (BPHS-46 sl.155-167): pada, sequence, years, dual lords, repetition.

Pinned against BPHS's printed results (via the fidelity ledger) and, as corroboration, against every
worked figure in Raman's *Studies in Jaimini* art.79 plus his full Example 20 table.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.doctrine.sources import verify
from app.parashara.primitives import chara_dasha as cd

_REST = {"Sun": 1, "Moon": 1, "Mars": 1, "Mercury": 1, "Jupiter": 1, "Venus": 1, "Saturn": 1,
         "Rahu": 1, "Ketu": 7}


def _signs(**kw: int) -> dict[str, int]:
    return {**_REST, **kw}


class TestPadaAndSequence:
    def test_odd_padas_are_aries_to_gemini_and_libra_to_sagittarius(self):
        """BPHS-46:4660 -- 'every three signs from Aries etc. have four padas'; odd padas count onwards."""
        assert [s for s in range(1, 13) if cd.is_savya(s)] == [1, 2, 3, 7, 8, 9]

    def test_sequence_direction_follows_the_ninth_signs_pada(self):
        """BPHS-46:4733 -- Aries lagna (9th Sagittarius, odd) runs onwards; Cancer lagna (9th Pisces) in reverse."""
        assert [s for s, _ in cd.sequence(1, _REST)][:3] == [1, 2, 3]
        assert [s for s, _ in cd.sequence(4, _REST)][:3] == [4, 3, 2]

    def test_taurus_lagna_runs_in_reverse_though_taurus_is_odd_pada(self):
        """The direction is the 9th's pada (Capricorn, even), not the lagna's own parity."""
        assert [s for s, _ in cd.sequence(2, _REST)][:3] == [2, 1, 12]


class TestYears:
    @pytest.mark.parametrize("sign,lord_at,expected", [
        (1, {"Mars": 5}, 4),        # Mesha, Kuja in Simha -> n=5 -> 4   (SJ art.79)
        (2, {"Venus": 8}, 6),       # Vrishabha, Sukra in Vrischika -> 6
        (4, {"Moon": 5}, 11),       # Kataka (even pada), Moon in Simha counted back -> n=12 -> 11
        (10, {"Saturn": 5}, 5),     # Makara (even), Sani in Simha back -> n=6 -> 5
        (9, {"Jupiter": 1}, 4),     # Dhanus, Guru in Mesha -> n=5 -> 4
    ])
    def test_raman_article_79_worked_figures(self, sign, lord_at, expected):
        """Years = n - 1 in the sign's pada direction (Raman SJ art.79, corroborating BPHS-46:4789/5037)."""
        assert cd.years(sign, _signs(**lord_at)) == expected

    def test_lord_in_own_sign_gives_twelve(self):
        """Convention (Jaimini ch.9:752, Raman art.80): lord in its own sign -> 12 years."""
        assert cd.years(5, _signs(Sun=5)) == 12

    def test_exalted_lord_adds_and_debilitated_lord_removes_a_year(self):
        """Convention (Jaimini ch.9:756, Raman art.80): Moon exalted in Taurus from Cancer -> 2+1."""
        assert cd.years(4, _signs(Moon=2)) == 3
        assert cd.years(1, _signs(Mars=4)) == 2          # Mars debilitated in Cancer: 3 - 1

    def test_debilitated_lord_in_the_second_gives_zero_and_is_skipped(self):
        """n = 2 minus 1 for debilitation = 0: a period of no length, absent from the timeline."""
        s = _signs(Jupiter=10)                             # Sagittarius' lord debilitated in Capricorn, its 2nd onwards
        assert cd.years(9, s) == 0
        assert 9 not in {p.sign for p in cd.timeline(1, s, horizon=200)}


class TestDualLords:
    def test_both_lords_in_aquarius_gives_twelve(self):
        """BPHS-46:4703 -- both lords in their own rasi -> 12 years."""
        assert cd.years(11, _signs(Saturn=11, Rahu=11)) == 12

    def test_one_lord_in_own_sign_counts_to_the_other(self):
        """BPHS-46:4707 -- one in his own sign, the other elsewhere: count to the other (root over the commentary)."""
        s = _signs(Mars=8, Ketu=12)
        assert cd.dasa_lord(8, s) == "Ketu"
        assert cd.years(8, s) == 4                          # Scorpio (odd pada) onwards to Pisces: n=5

    def test_associated_lord_beats_a_lone_lord(self):
        """BPHS-46:4783 -- 'Rahu is associated with a planet. Therefore, Rahu is more powerful than Saturn.'"""
        s = {"Saturn": 8, "Rahu": 3, "Moon": 3, "Ketu": 9, "Sun": 6, "Mars": 2, "Mercury": 11,
             "Jupiter": 11, "Venus": 11}
        assert cd.dasa_lord(11, s) == "Rahu"
        assert cd.years(11, s) == 8

    def test_sign_nature_breaks_an_association_tie(self):
        """BPHS-46:4721 -- dual > fixed > movable when both lords are equally associated."""
        s = {"Mars": 3, "Ketu": 1, "Sun": 3, "Moon": 1, "Mercury": 5, "Jupiter": 5, "Venus": 5,
             "Saturn": 5, "Rahu": 7}
        assert cd.dasa_lord(8, s) == "Mars"                  # Gemini (dual) over Aries (movable)

    def test_exaltation_does_not_override_association(self):
        """All three sources put exaltation LAST (BPHS 46:4725, Jaimini ch.9:800, Raman art.86)."""
        s = _signs(Saturn=7, Rahu=3, Moon=3)                 # Saturn exalted in Libra, Rahu associated
        assert cd.dasa_lord(11, s) == "Rahu"

    def test_lone_exalted_lord_breaks_a_full_tie_before_years(self):
        """Convention (Jaimini ch.9:800): equal on association and sign nature -> the exalted lord."""
        s = {"Saturn": 7, "Rahu": 1, "Sun": 12, "Moon": 4, "Mars": 6, "Mercury": 6, "Jupiter": 6,
             "Venus": 6, "Ketu": 10}                         # both unassociated, both in movable signs
        assert cd.dasa_lord(11, s) == "Saturn"

    def test_rahu_exalted_in_taurus_adds_a_year(self):
        """BPHS-47:280 -- 'The sign of exaltation of Rahu is Taurus' (the engine table omits nodes)."""
        s = _signs(Saturn=11, Rahu=2)                        # Saturn in Aquarius -> count to Rahu
        assert cd.years(11, s) == 10                         # Aquarius (even) back to Taurus: n=10 -> 9, +1


class TestTimeline:
    def test_repeats_and_is_contiguous_to_horizon(self):
        """BPHS-46:4837 -- after one round the first sign starts again, with the same years."""
        s = _signs(Mars=5, Venus=8)
        tl = cd.timeline(1, s, horizon=100)
        assert tl[-1].end_year >= 100
        assert all(a.end_year == b.start_year for a, b in zip(tl, tl[1:]))
        live = [p for p in tl if p.years > 0]
        k = len([y for _, y in cd.sequence(1, s) if y > 0])
        assert [p.sign for p in live[k:2 * k]] == [p.sign for p in live[:k]]


class TestRamanExample20:
    def test_full_table_reproduced(self):
        """SJ Example 20 (8 Aug 1912, 19:35 IST, Bangalore): all twelve printed years, both dual lords and
        the exalted-Moon +1 for Cancer, are reproduced exactly (corroboration, not authority)."""
        ch = cast(year=1912, month=8, day=8, hour=19, minute=35, tz_offset=5.5, latitude=12.97, longitude=77.59)
        printed = {11: 9, 12: 4, 1: 4, 2: 3, 3: 2, 4: 3, 5: 1, 6: 1, 7: 10, 8: 9, 9: 11, 10: 8}
        seq = cd.sequence(ch.asc_sign, cd.chart_signs(ch))
        assert [s for s, _ in seq][:3] == [11, 12, 1]
        assert dict(seq) == printed


def test_every_citation_resolves():
    """Each rule constant points at a real corpus line."""
    cites = [v for v in vars(cd).values() if type(v).__name__ == "Citation"]
    assert len(cites) >= 13 and all(verify(c) for c in cites)


class TestAntardashas:
    def test_fixed_runs_every_sixth_backwards_when_even(self):
        """BPHS-51:581 -- fixed: 'every sixth rasi'; Taurus (even) counts it in reverse."""
        assert cd.antardasha_signs(2)[:3] == (2, 9, 4)

    def test_dual_odd_takes_kendras_onwards(self):
        """BPHS-51:582-585 -- Gemini (odd, dual): itself, its kendras, then those of its 5th and 9th."""
        assert cd.antardasha_signs(3) == (3, 6, 9, 12, 7, 10, 1, 4, 11, 2, 5, 8)

    def test_every_order_is_a_permutation_of_the_twelve(self):
        """Each dasa yields each of the twelve signs once."""
        assert all(sorted(cd.antardasha_signs(s)) == list(range(1, 13)) for s in range(1, 13))

    def test_twelve_equal_parts_tile_the_dasa(self):
        """BPHS-51:529 -- each antardasha is 1/12 of the dasa years."""
        p = cd.CharaPeriod(sign=11, years=8, start_year=3.0, end_year=11.0)
        ads = cd.antardashas(p)
        assert len(ads) == 12 and ads[0].start_year == 3.0 and abs(ads[-1].end_year - 11.0) < 1e-9
        assert all(abs(a.years - 8 / 12) < 1e-12 for a in ads)
