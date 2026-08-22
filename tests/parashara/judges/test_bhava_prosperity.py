"""The bhava-prosperity verdict layer (BPHS ch.11 sl.14-16) and its chart adapter.

The doctrine tests exercise Parashara's own conditions and antidote clauses directly on
`BhavaFactors`; the chart tests confirm the factors are computed and every house judged. Assertions
target invariants Parashara's scheme guarantees, not hand-computed labels for a specific chart.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.bhava_chart import bhava_factors, judge_all_bhavas, judge_bhava
from app.parashara.judges.bhava_prosperity import BhavaFactors, judge_prosperity
from app.parashara.doctrine.sources import verify


def _neutral(**over) -> BhavaFactors:
    """A bhava with nothing firing — the baseline to toggle single conditions against."""
    base = dict(
        house=1, benefic_occupant=False, benefic_aspect=False, lord_avastha="bala",
        lord_own_or_exalt=False, lord_in_tenth=False, lord_aspects_bhava=False,
        lord_conjunct_malefic=False, lord_malefic_conjunction_mitigated=False,
        lord_conjunct_dusthana_lord=False, lord_is_itself_dusthana_lord=False,
        lord_defeated_in_war=False,
    )
    base.update(over)
    return BhavaFactors(**base)


class TestProsperityConditions:
    def test_each_prosperity_condition_alone_makes_it_flourish(self):
        """Any one of the five prosperity conditions, with no annihilation, tips to flourishing."""
        for over in (
            {"benefic_occupant": True},
            {"benefic_aspect": True},
            {"lord_avastha": "yuva"},
            {"lord_own_or_exalt": True},
            {"lord_in_tenth": True},
        ):
            v = judge_prosperity(_neutral(**over))
            assert v.verdict == "flourishing", over
            assert v.net_prosperity == 1 and v.net_annihilation == 0

    def test_kumara_and_yuva_flourish_but_bala_does_not(self):
        assert judge_prosperity(_neutral(lord_avastha="kumara")).net_prosperity == 1
        assert judge_prosperity(_neutral(lord_avastha="yuva")).net_prosperity == 1
        assert judge_prosperity(_neutral(lord_avastha="bala")).net_prosperity == 0


class TestAnnihilationConditions:
    def test_dusthana_lord_conjunction_annihilates(self):
        v = judge_prosperity(_neutral(lord_conjunct_dusthana_lord=True))
        assert v.verdict == "annihilated" and v.net_annihilation == 1

    def test_defeat_in_war_annihilates(self):
        assert judge_prosperity(_neutral(lord_defeated_in_war=True)).verdict == "annihilated"

    def test_vriddha_and_mrita_annihilate(self):
        assert judge_prosperity(_neutral(lord_avastha="vriddha")).verdict == "annihilated"
        assert judge_prosperity(_neutral(lord_avastha="mrita")).verdict == "annihilated"

    def test_unaspected_by_lord_alone_is_not_annihilation(self):
        """BPHS-11:16a — 'this does not mean the bhava suffers annihilation'. With the lord not
        aspecting and nothing else, it stays ordinary, not annihilated."""
        v = judge_prosperity(_neutral(lord_aspects_bhava=False))
        assert v.verdict == "ordinary" and v.net_annihilation == 0


class TestAntidotes:
    def test_lords_aspect_antidotes_the_malefic_conjunction(self):
        """BPHS-11:16a — the lord's aspect on its bhava is the antidote to a malefic relation.
        Malefic conjunction fires, but the lord aspecting the bhava neutralises it."""
        without = judge_prosperity(_neutral(lord_conjunct_malefic=True, lord_aspects_bhava=False))
        withasp = judge_prosperity(_neutral(lord_conjunct_malefic=True, lord_aspects_bhava=True))
        assert without.verdict == "annihilated"
        assert withasp.net_annihilation == 0        # antidoted away

    def test_mitigation_flag_antidotes_the_malefic_conjunction(self):
        """'If the malefic is friendly ... or exalted ... the evil is minimized.'"""
        v = judge_prosperity(_neutral(lord_conjunct_malefic=True,
                                      lord_malefic_conjunction_mitigated=True))
        assert v.net_annihilation == 0

    def test_evil_lord_gets_relief_from_dusthana_conjunction(self):
        """'if he himself is an evil lord, then some relief can be expected.'"""
        plain = judge_prosperity(_neutral(lord_conjunct_dusthana_lord=True))
        relief = judge_prosperity(_neutral(lord_conjunct_dusthana_lord=True,
                                           lord_is_itself_dusthana_lord=True))
        assert plain.net_annihilation == 1
        assert relief.net_annihilation == 0


class TestNetVerdict:
    def test_equal_sides_are_ordinary(self):
        """One clean prosperity + one un-antidoted annihilation = a tie = ordinary."""
        v = judge_prosperity(_neutral(benefic_occupant=True, lord_defeated_in_war=True))
        assert v.net_prosperity == 1 and v.net_annihilation == 1
        assert v.verdict == "ordinary"

    def test_nothing_firing_is_ordinary(self):
        assert judge_prosperity(_neutral()).verdict == "ordinary"

    def test_reasons_are_readable_and_signed(self):
        v = judge_prosperity(_neutral(benefic_occupant=True, lord_defeated_in_war=True))
        assert any(r.startswith("+") for r in v.reasons)
        assert any(r.startswith("-") for r in v.reasons)

    def test_citations_resolve(self):
        v = judge_prosperity(_neutral(benefic_occupant=True))
        for c in v.prosperity + v.annihilation:
            assert verify(c.source), f"{c.key}: {c.source.work}:{c.source.line}"


class TestChartAdapter:
    #: Canonical baseline chart (CLAUDE.md), sidereal longitudes; Virgo lagna (sign 6).
    _CHART = {
        "Sun": 89.1, "Moon": 355.3, "Mars": 21.7, "Mercury": 111.4,
        "Jupiter": 96.8, "Venus": 62.5, "Saturn": 262.9, "Rahu": 300.0, "Ketu": 120.0,
    }
    _ASC = 6

    def test_all_twelve_houses_judged(self):
        got = judge_all_bhavas(self._CHART, asc_sign=self._ASC, moon_waxing=True)
        assert set(got) == set(range(1, 13))
        for h, v in got.items():
            assert v.house == h
            assert v.verdict in ("flourishing", "ordinary", "annihilated")

    def test_factors_are_populated(self):
        f = bhava_factors(1, self._CHART, asc_sign=self._ASC, moon_waxing=True)
        assert f.lord_avastha in ("bala", "kumara", "yuva", "vriddha", "mrita")
        assert isinstance(f.benefic_occupant, bool)

    def test_deterministic(self):
        a = judge_bhava(7, self._CHART, asc_sign=self._ASC, moon_waxing=True)
        b = judge_bhava(7, self._CHART, asc_sign=self._ASC, moon_waxing=True)
        assert a == b

    def test_paksha_can_change_a_verdict_somewhere(self):
        """The Moon's benefic nature depends on paksha, so at least one house's benefic-occupant/
        aspect factor — and possibly its verdict — should differ between waxing and waning."""
        wax = judge_all_bhavas(self._CHART, asc_sign=self._ASC, moon_waxing=True)
        wan = judge_all_bhavas(self._CHART, asc_sign=self._ASC, moon_waxing=False)
        assert any(wax[h].verdict != wan[h].verdict or
                   wax[h].net_prosperity != wan[h].net_prosperity for h in range(1, 13))
