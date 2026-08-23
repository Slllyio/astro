"""Richer bhava verdict — ch.11 extended with strength (Vimsopaka/SAV/dignity) + yoga.

Pins the structure (all 12 houses, ch.11 base carried, verdict rule = net votes) and that the added
factors actually bear on the verdict, each citing a source. Not tuned to any target — a structural /
doctrinal test only.
"""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.judges.richer_bhava import richer_all_bhavas


def _canonical():
    return cast(year=1990, month=7, day=15, hour=12, minute=0,
                tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestStructure:
    def test_all_twelve_houses(self):
        ch = _canonical()
        r = richer_all_bhavas(ch.longitudes, asc_sign=ch.asc_sign, moon_waxing=ch.moon_waxing)
        assert set(r) == set(range(1, 13))
        for v in r.values():
            assert v.verdict in ("flourishing", "ordinary", "annihilated")
            assert v.base is not None                       # the ch.11 verdict is carried
            assert v.prosperity_votes >= 0 and v.annihilation_votes >= 0

    def test_verdict_follows_the_net_vote_rule(self):
        ch = _canonical()
        for v in richer_all_bhavas(ch.longitudes, asc_sign=ch.asc_sign,
                                   moon_waxing=ch.moon_waxing).values():
            p, a = v.prosperity_votes, v.annihilation_votes
            expect = "flourishing" if p > a else "annihilated" if a > p else "ordinary"
            assert v.verdict == expect

    def test_richer_votes_extend_the_ch11_base(self):
        """The richer votes are >= the ch.11 base counts (they only ADD BPHS-cited votes)."""
        ch = _canonical()
        for v in richer_all_bhavas(ch.longitudes, asc_sign=ch.asc_sign,
                                   moon_waxing=ch.moon_waxing).values():
            assert v.prosperity_votes >= v.base.net_prosperity
            assert v.annihilation_votes >= v.base.net_annihilation


class TestFactorsCited:
    def test_added_factors_carry_a_citation_tag(self):
        ch = _canonical()
        added_tags = ("BPHS-7", "BPHS-32", "BPHS-66", "SARAVALI-37")
        seen = False
        for v in richer_all_bhavas(ch.longitudes, asc_sign=ch.asc_sign,
                                   moon_waxing=ch.moon_waxing).values():
            for f in v.factors:
                if any(t in f for t in added_tags):
                    seen = True
        assert seen, "no strength/yoga factor fired on the canonical chart — expected at least one"
