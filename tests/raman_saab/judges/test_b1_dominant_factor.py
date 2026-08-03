"""B1 dominant-factor guard — `judges/house_template` (DOCTRINE_BACKLOG B1).

HTJAH-I:3788: "Though the Karaka Mars is well disposed, the fact of the ruler of the third
becoming combust and hence powerless, renders the third house weak. This stands against his
having any brothers." Raman DENIES the matter on a powerless lord while the karaka is strong —
but clause 2 counts pillars, so lord-weak + karaka-strong + bhava-strong counts two strong and
lifts the matter to favourable, exactly inverting him.

The guard blocks that lift. It ships DISABLED: measured on the golden corpus it trades 2 exact
matches for 2 fewer real (distance>=2) errors — strict ratchet 261->259, ordinal 281->283 — so
enabling it is a human call recorded in B1, not a silent ratchet move.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges import house_template as ht


def _ledger(**kw) -> ht.FrameLedger:
    """A contradicted ledger (both polarities fired) with two strong pillars — the exact shape
    clause 2 lifts to 'favourable' unless something blocks it."""
    base = dict(
        frame="LAGNA", lord="Mercury", lord_strong=False, karaka="Mars", karaka_strong=True,
        bhava_bala=400.0, bhava_bala_strong=True, navamsa_status="neutral",
        karaka_intact=True, maraka_active=False, parivartana_resilient=False,
        lord_karaka_identical=False,
        fired_benefic=("b",), fired_malefic=("m",), fired_neutral=(), flags=(),
        lord_hard_afflicted=None)
    base.update(kw)
    return ht.FrameLedger(**base)


@pytest.fixture(autouse=True)
def _restore_flag():
    """Never leak the flag into other tests — it moves verdicts."""
    original = ht.B1_DOMINANT_FACTOR_GUARD
    yield
    ht.B1_DOMINANT_FACTOR_GUARD = original


class TestShippedState:
    def test_guard_is_on_by_default(self):
        """ENABLED 2026-08-03 on an explicit user decision. Both golden baselines were re-based
        in that same commit (strict 261->259, ordinal 281->283) — the first deliberate DOWNWARD
        strict re-base, accepted because it removes 2 favourable/afflicted inversions."""
        assert ht.B1_DOMINANT_FACTOR_GUARD is True

    def test_turning_it_off_restores_the_old_lift(self):
        """The flag is a real switch, not decoration: with it off the same ledger lifts again,
        so the A/B that justified enabling it stays reproducible."""
        ht.B1_DOMINANT_FACTOR_GUARD = False
        verdict, _shifted = ht._decide(_ledger(lord_hard_afflicted=True))
        assert verdict == "favourable"

    def test_no_house_is_exempt_by_default(self):
        """B1_GUARD_EXEMPT_HOUSES ships EMPTY. Measured 2026-08-03: exempting H12 recovers 2
        strict matches but re-escalates a real favourable<->afflicted inversion (h12_05) —
        trading back exactly what the guard was enabled to fix. Any entry here is a recorded
        human decision (DOCTRINE_BACKLOG B1), never a tuner move."""
        assert ht.B1_GUARD_EXEMPT_HOUSES == frozenset()


class TestGuardBehaviour:
    def test_hard_afflicted_lord_blocks_the_favourable_lift(self):
        """HTJAH-I:3788 — a powerless lord denies the matter even beside a strong karaka."""
        ht.B1_DOMINANT_FACTOR_GUARD = True
        verdict, _shifted = ht._decide(_ledger(lord_hard_afflicted=True))
        assert verdict == "mixed"

    def test_a_clean_lord_is_unaffected(self):
        ht.B1_DOMINANT_FACTOR_GUARD = True
        verdict, _shifted = ht._decide(_ledger(lord_hard_afflicted=False))
        assert verdict == "favourable"

    def test_track_b_none_is_not_treated_as_afflicted(self):
        """None means 'no positions to judge', not 'afflicted' — a Track-B chart must not be
        silently denied by a guard that has no evidence to act on."""
        ht.B1_DOMINANT_FACTOR_GUARD = True
        verdict, _shifted = ht._decide(_ledger(lord_hard_afflicted=None))
        assert verdict == "favourable"

    def test_the_afflicted_arm_is_untouched(self):
        """The guard only blocks a LIFT. An already-afflicted preponderance stays afflicted —
        the guard must never manufacture a verdict, only withhold an unearned one."""
        ht.B1_DOMINANT_FACTOR_GUARD = True
        v, _s = ht._decide(_ledger(lord_strong=False, karaka_strong=False,
                                   bhava_bala_strong=False, lord_hard_afflicted=True))
        assert v == "afflicted"


class TestLordHardAfflicted:
    def test_combust_lord_is_hard_afflicted(self):
        """The canonical chart's Jupiter is combust at 1.00 of the orb while its Shadbala
        (7.53) clears the 6.5 bar — the 3788 pattern, live."""
        chart = cast_chart(BirthData("c", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59),
                           ayanamsa="raman")
        assert ht._lord_hard_afflicted("Jupiter", chart) is True

    def test_an_unafflicted_lord_is_not_flagged(self):
        chart = cast_chart(BirthData("c", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59),
                           ayanamsa="raman")
        assert ht._lord_hard_afflicted("Sun", chart) is False

    def test_track_b_chart_returns_none(self):
        """No Shadbala -> no judgement, rather than a default that would deny the matter."""
        chart = RamanChart.from_stated_positions(
            {"Sun": {"lon": 10.0, "bhava": 1}, "Mercury": {"lon": 12.0, "bhava": 1}},
            asc_lon=0.0, ayanamsa="raman")
        assert ht._lord_hard_afflicted("Mercury", chart) is None
