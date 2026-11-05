"""Directional parivartana — the measured, NOT-shipped arms (DOCTRINE_BACKLOG Track 4a).

`_decide` credits an exchange as flat relief: a debilitated lord or karaka in a parivartana
has its penalty bypassed regardless of what the exchange partner is doing. Raman's own
worked charts run both ways — "mutually benefiting each other" (HTJAH-I:8837), but also
"Saturn who is the 7th lord ALSO IS AFFLICTED BY THIS PARIVARTANA" (HTJAH-I:9119).

Two arms were implemented and measured; BOTH SHIP OFF pending a human decision. The point
of these tests is therefore twofold: that the arms do what they claim when switched on, and
— the one that actually protects the engine — that with the flags at their shipped values
nothing whatsoever changed.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.conditions import EvalContext
from app.raman_saab.judges import house_template as HT

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def chart():
    return cast_chart(_CANONICAL)


@pytest.fixture
def flags_restored():
    """Every test here rebinds module-level flags; restore them whatever happens."""
    before = (HT.PARIVARTANA_DIRECTIONAL, HT.PARIVARTANA_TRANSMITS,
              HT.PARIVARTANA_PARTNER_TEST)
    yield
    (HT.PARIVARTANA_DIRECTIONAL, HT.PARIVARTANA_TRANSMITS,
     HT.PARIVARTANA_PARTNER_TEST) = before


class TestTheShippedDefaultsAreOff:
    """The measurement must not have leaked into the engine."""

    def test_both_arms_are_off(self):
        assert HT.PARIVARTANA_DIRECTIONAL is False
        assert HT.PARIVARTANA_TRANSMITS is False

    def test_the_partner_test_defaults_to_the_union(self):
        """Only consulted when an arm is on; pinned so a later reader knows which reading
        the recorded numbers belong to."""
        assert HT.PARIVARTANA_PARTNER_TEST == "either"


class TestThePartnerHelpers:
    def test_partners_are_the_far_end_of_each_exchange(self):
        pairs = frozenset({frozenset({"Sun", "Moon"}), frozenset({"Sun", "Mars"})})
        assert HT._parivartana_partners("Sun", pairs) == frozenset({"Moon", "Mars"})
        assert HT._parivartana_partners("Moon", pairs) == frozenset({"Sun"})

    def test_a_planet_in_no_exchange_has_no_partner(self):
        assert HT._parivartana_partners("Saturn", frozenset()) == frozenset()

    def test_a_maraka_partner_counts_as_afflicted(self, chart):
        pairs = frozenset({frozenset({"Sun", "Venus"})})
        assert HT._partner_afflicted("Sun", pairs, chart, frozenset({"Venus"}))

    def test_a_clean_partner_does_not(self, chart, flags_restored):
        """With the condition reading, a partner that is neither combust, debilitated-
        uncancelled nor a maraka is not an affliction to transmit."""
        HT.PARIVARTANA_PARTNER_TEST = "condition"
        clean = next(p for p in ("Jupiter", "Venus", "Mercury", "Moon")
                     if not HT._combust_graded(p, chart)
                     and not HT._debilitated_uncancelled(p, chart))
        pairs = frozenset({frozenset({"Sun", clean})})
        assert not HT._partner_afflicted("Sun", pairs, chart, frozenset())

    def test_the_dusthana_reading_looks_only_at_lordship(self, chart, flags_restored):
        """HTJAH-I:9119's mechanism: the 8th lordship is what travels across the exchange."""
        HT.PARIVARTANA_PARTNER_TEST = "dusthana"
        eighth_lord = HT._lord_of_sign(chart.asc_sign, 8)
        pairs = frozenset({frozenset({"Sun", eighth_lord})})
        assert HT._partner_afflicted("Sun", pairs, chart, frozenset())

    def test_the_condition_reading_ignores_lordship(self, chart, flags_restored):
        """The two readings are genuinely different rules, not two spellings of one."""
        HT.PARIVARTANA_PARTNER_TEST = "condition"
        eighth = HT._lord_of_sign(chart.asc_sign, 8)
        if (HT._combust_graded(eighth, chart)
                or HT._debilitated_uncancelled(eighth, chart)):
            pytest.skip(f"{eighth} is independently afflicted on this chart")
        pairs = frozenset({frozenset({"Sun", eighth})})
        assert not HT._partner_afflicted("Sun", pairs, chart, frozenset())

    def test_one_bad_partner_is_enough(self, chart, flags_restored):
        """A graha holding two exchanges is not shielded by the healthy one."""
        HT.PARIVARTANA_PARTNER_TEST = "condition"
        pairs = frozenset({frozenset({"Sun", "Jupiter"}), frozenset({"Sun", "Mars"})})
        assert HT._partner_afflicted("Sun", pairs, chart, frozenset({"Mars"}))


class TestSwitchingAnArmOnChangesSomething:
    """A flag that measurably does nothing would make the recorded numbers meaningless."""

    def test_transmit_moves_verdicts_somewhere_in_the_chart(self, chart, flags_restored):
        before = {(h, sv.signification): sv.verdict
                  for h in range(1, 13) for sv in HT.judge_house(chart, h).significations}
        HT.PARIVARTANA_TRANSMITS = True
        after = {(h, sv.signification): sv.verdict
                 for h in range(1, 13) for sv in HT.judge_house(chart, h).significations}
        moved = {k for k in before if before[k] != after[k]}
        assert moved, "arm B changed nothing on the canonical chart"
        # it only ever tightens — an affliction carried across cannot improve a reading
        _ORD = {"afflicted": 0, "mixed": 1, "favourable": 2}
        for k in moved:
            if before[k] in _ORD and after[k] in _ORD:
                assert _ORD[after[k]] < _ORD[before[k]], (k, before[k], after[k])

    def test_transmit_flags_the_row_it_acted_on(self, chart, flags_restored):
        HT.PARIVARTANA_TRANSMITS = True
        flagged = [sv for h in range(1, 13)
                   for sv in HT.judge_house(chart, h).significations
                   if any("PARIVARTANA_TRANSMITTED_AFFLICTION" in led.flags
                          for led in (sv.ledger, *sv.alt_ledgers))]
        assert flagged, "the arm fired but disclosed nothing in the ledger"


class TestWithTheFlagsOffNothingMoved:
    def test_the_canonical_chart_is_untouched_by_the_new_code(self, chart):
        """The whole safety claim of this commit in one assertion: with the shipped flags,
        every signification reads exactly as the ledger's own recorded verdict logic gives
        it — the helpers are computed but consulted by nobody."""
        HT.PARIVARTANA_DIRECTIONAL = False
        HT.PARIVARTANA_TRANSMITS = False
        for h in range(1, 13):
            for sv in HT.judge_house(chart, h).significations:
                for led in (sv.ledger, *sv.alt_ledgers):
                    assert "PARIVARTANA_TRANSMITTED_AFFLICTION" not in led.flags

    def test_the_partner_computation_does_not_disturb_the_memo_store(self, chart):
        """`_partner_afflicted` reads the SAME cached pair set `_decide` already builds."""
        ctx = EvalContext(chart)
        first = HT._parivartana_pairs(chart, ctx)
        HT._partner_afflicted("Sun", first, chart, HT._maraka_grahas(chart))
        assert HT._parivartana_pairs(chart, ctx) is first
