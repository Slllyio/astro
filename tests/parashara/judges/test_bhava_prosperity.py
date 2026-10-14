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

    def test_citations_point_at_doctrine_not_frontmatter(self):
        """Regression guard for the 2026-08-22 audit defect: the sources cited sloka NUMBERS (14/16)
        as line numbers, which landed in the YAML frontmatter. `verify()` passed but `passage()`
        returned 'topics:' / 'classical_refs:'. Assert the cited lines are REAL doctrine text."""
        from app.parashara.doctrine.sources import passage
        v = judge_prosperity(_neutral(benefic_occupant=True))
        for c in v.prosperity + v.annihilation:
            text = passage(f"{c.source.work}:{c.source.line}")["text"].lower()
            assert "topics:" not in text and "classical_refs:" not in text, \
                f"{c.key} cites frontmatter: {text[:40]!r}"
            assert len(text.strip()) > 10, f"{c.key} cites an empty/near-empty line"


class TestSuptavastha:
    """The third killing avastha (BPHS-11:158), added after the audit found it missing."""

    def test_supta_alone_annihilates(self):
        v = judge_prosperity(_neutral(lord_in_supta=True))
        assert v.verdict == "annihilated" and v.net_annihilation == 1

    def test_supta_is_independent_of_the_baladi_avasthas(self):
        """Supta (debil/enemy-sign, Jagradadi) is distinct from Vriddha/Mrita (Baladi by degree);
        a lord can be spent by degree AND sleeping by dignity — two separate afflictions."""
        both = judge_prosperity(_neutral(lord_avastha="mrita", lord_in_supta=True))
        assert both.net_annihilation == 2

    def test_supta_condition_cites_its_sloka(self):
        from app.parashara.doctrine.sources import passage
        v = judge_prosperity(_neutral(lord_in_supta=True))
        supta = next(c for c in v.annihilation if c.key == "lord_in_supta")
        assert "avasthas" in passage(f"{supta.source.work}:{supta.source.line}")["text"].lower()


class TestCh34Redemption:
    """ch.11's evil-companion clause counts only FUNCTIONALLY evil dusthana lords (BPHS ch.34)."""

    def test_trine_co_lords_are_redeemed(self):
        """Aries lagna: Mars (8th + lagna) and Jupiter (12th + 9th) own trines, so only Mercury
        (6th + 3rd) stays evil (BPHS-34:61, :115)."""
        from app.parashara.chart.bhava_chart import _evil_dusthana_lords
        assert _evil_dusthana_lords(1) == frozenset({"Mercury"})

    def test_moon_as_eighth_lord_is_not_evil(self):
        """Sagittarius lagna: the Moon owns the 8th — 'not evil' (BPHS-34:64); Mars (12th + 5th) is
        trine-redeemed; Venus (6th + 11th) stays evil."""
        from app.parashara.chart.bhava_chart import _evil_dusthana_lords
        assert _evil_dusthana_lords(9) == frozenset({"Venus"})

    def test_per_ascendant_key_overrides_redemption(self):
        """Taurus lagna: Venus owns the 1st AND the 6th, yet Parashara's own key names him a malefic
        (BPHS-34:386) — he stays evil; Jupiter (8th+11th) and Mars (12th+7th) are plainly evil."""
        from app.parashara.chart.bhava_chart import _evil_dusthana_lords
        assert _evil_dusthana_lords(2) == frozenset({"Venus", "Jupiter", "Mars"})

    def test_redeemed_companion_does_not_fire_the_clause(self):
        """Aries lagna, 10th lord Saturn with Jupiter (12th+9th lord): no evil association; with
        Mercury (6th+3rd lord): the clause fires."""
        lons_jup = {"Saturn": 245.0, "Jupiter": 250.0, "Mars": 10.0, "Sun": 40.0,
                    "Moon": 70.0, "Mercury": 100.0, "Venus": 130.0}
        lons_mer = {**lons_jup, "Mercury": 250.0, "Jupiter": 100.0}
        assert not bhava_factors(10, lons_jup, asc_sign=1, moon_waxing=True).lord_conjunct_dusthana_lord
        assert bhava_factors(10, lons_mer, asc_sign=1, moon_waxing=True).lord_conjunct_dusthana_lord


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
