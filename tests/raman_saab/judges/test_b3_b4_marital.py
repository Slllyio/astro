"""B3 + B4-arm-2 — the two never-shipped Phase-2 marriage items (DOCTRINE_BACKLOG).

B3 (HTJAH-II:2579): Kuja-dosha / maraka pressure concerns the DEATH of the spouse
("the death of the husband/wife will occur"), NOT marital happiness. The 7th being
a maraka house lands Venus-the-karaka in the maraka set and clause-6/clause-3
over-afflict the happiness sub-matter on maraka pressure alone. The guard
suppresses maraka's VERDICT-DRIVING effect for ``marital_happiness`` only —
mirroring LONGEVITY_GUARD's shape; the ledger still records ``maraka_active``
honestly and death/longevity matters are untouched.

B4 arm 2 (HTJAH-II:1474): a Yogakaraka Venus in a FIXED sign gives "fixity of
affections" — a benefic marital testimony that answers the dual-sign multiplicity
stigma. Encoded as rule H7.C.87 (arm 1, the blemishless-Venus floor, shipped
2026-06-15 as a gate).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges import house_template as ht


def _ledger(**kw) -> ht.FrameLedger:
    """Track-B shape (no Shadbala): clause 3 decides on polarity/maraka alone —
    the exact arm B3 must change for marital happiness."""
    base = dict(
        frame="LAGNA", lord="Venus", lord_strong=None, karaka="Venus", karaka_strong=None,
        bhava_bala=None, bhava_bala_strong=None, navamsa_status="neutral",
        karaka_intact=True, maraka_active=True, parivartana_resilient=False,
        lord_karaka_identical=True,
        fired_benefic=(), fired_malefic=(), fired_neutral=(), flags=(),
        lord_hard_afflicted=None)
    base.update(kw)
    return ht.FrameLedger(**base)


class TestB3MarakaNonDeathGuard:
    def test_unguarded_maraka_still_afflicts(self):
        """Baseline unchanged: with no guard flag, lone maraka pressure afflicts (clause 3)."""
        v, _ = ht._decide(_ledger())
        assert v == "afflicted"

    def test_guarded_marital_matter_is_not_driven_by_maraka_alone(self):
        """With MARAKA_NON_DEATH_GUARD, maraka pressure alone no longer produces
        'afflicted' — the matter reads insufficient-evidence on empty evidence
        (HTJAH-II:2579: maraka concerns the spouse's death, not the happiness)."""
        v, _ = ht._decide(_ledger(flags=("MARAKA_NON_DEATH_GUARD",)))
        assert v == "insufficient-evidence"

    def test_guard_does_not_suppress_fired_malefics(self):
        """The guard is maraka-scoped only: a genuinely fired malefic rule still afflicts."""
        v, _ = ht._decide(_ledger(flags=("MARAKA_NON_DEATH_GUARD",), fired_malefic=("m",)))
        assert v == "afflicted"

    def test_longevity_guard_semantics_unchanged(self):
        """LONGEVITY_GUARD still clamps to insufficient-evidence exactly as before."""
        v, _ = ht._decide(_ledger(flags=("LONGEVITY_GUARD",)))
        assert v == "insufficient-evidence"

    def test_ledger_build_flags_marital_happiness_only(self):
        """_build_frame_ledger stamps the guard on marital_happiness and NOT on death:
        the death MANNER matter keeps its maraka sensitivity (HTJAH-II combos #1-2)."""
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.chart.model import BirthData
        from app.raman_saab.doctrine.significations import SIGNIFICATIONS
        chart = cast_chart(BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59),
                           ayanamsa="raman")
        mh = next(s for s in SIGNIFICATIONS[7] if s.key == "marital_happiness")
        death = next(s for s in SIGNIFICATIONS[8] if s.key == "death")
        led_mh = ht._build_frame_ledger(chart, mh, "lagna")
        led_death = ht._build_frame_ledger(chart, death, "lagna")
        assert "MARAKA_NON_DEATH_GUARD" in led_mh.flags
        assert "MARAKA_NON_DEATH_GUARD" not in led_death.flags


class TestB4YogakarakaVenusFixity:
    """H7.C.87 — Yogakaraka Venus in a fixed sign → fixity of affections (HTJAH-II:1474)."""

    def _chart(self, asc_lon: float, venus_lon: float) -> RamanChart:
        return RamanChart.from_stated_positions(
            {"Venus": {"lon": venus_lon, "bhava": 1}}, asc_lon=asc_lon, ayanamsa="raman")

    def _rule(self):
        from app.raman_saab.doctrine.rule_sets import house_07_kalatra
        return next(r for r in house_07_kalatra.RULES if r.id == "H7.C.87")

    def test_fires_for_yogakaraka_venus_in_fixed_sign(self):
        """Capricorn lagna (Venus lords the 5th and 10th — Yogakaraka, HTJAH-I:606),
        Venus in Taurus (a fixed sign) → the rule fires."""
        rule = self._rule()
        chart = self._chart(asc_lon=272.0, venus_lon=41.0)   # asc Capricorn, Venus Taurus
        assert rule.fires(chart) is True

    def test_does_not_fire_in_dual_sign(self):
        """Same lagna, Venus in Gemini (a dual sign) → no fixity testimony."""
        rule = self._rule()
        chart = self._chart(asc_lon=272.0, venus_lon=72.0)   # Venus Gemini
        assert rule.fires(chart) is False

    def test_does_not_fire_when_venus_not_yogakaraka(self):
        """Aries lagna: Venus lords 2 and 7 — no kendra+trikona pair, not Yogakaraka."""
        rule = self._rule()
        chart = self._chart(asc_lon=5.0, venus_lon=41.0)     # asc Aries, Venus Taurus
        assert rule.fires(chart) is False

    def test_polarity_and_signification(self):
        """The record is a benefic marital-happiness testimony citing HTJAH-II:1474."""
        rule = self._rule()
        assert rule.polarity == "benefic"
        assert rule.signification == "marital_happiness"
        assert (rule.source.work, rule.source.line) == ("HTJAH-II", 1474)


class TestMarginalGateAntiDoubleMove:
    """Doctrine-review HIGH (2026-08-17): the widened marginal-karaka gate must never
    re-lift a 'mixed' produced by the _marital_bond_gate demote (>=2 cruel malefics
    8th-from-Moon, HTJAH-II:2664/2877 — Raman's own troubled-marriage reading)."""

    class _FakeBala:
        def __init__(self, total_shashtiamsas: float): self.total = total_shashtiamsas

    class _FakePlanet:
        def __init__(self, rupas: float):
            self.shadbala_rupas = TestMarginalGateAntiDoubleMove._FakeBala(rupas * 60.0)

    class _FakeChart:
        def __init__(self, planets): self.planets = planets

    def _fixture(self):
        from app.raman_saab.doctrine.significations import SIGNIFICATIONS
        mh = next(s for s in SIGNIFICATIONS[7] if s.key == "marital_happiness")
        # marginal Venus: 5.37 rupas against the canonical 5.5 bar (inside the 0.2 band);
        # strong lord, no fired malefic, D9 neutral, benefic evidence -> re-decide lifts.
        led = ht.FrameLedger(
            frame="LAGNA", lord="Sun", lord_strong=True, karaka="Venus", karaka_strong=False,
            bhava_bala=400.0, bhava_bala_strong=True, navamsa_status="neutral",
            karaka_intact=True, maraka_active=True, parivartana_resilient=False,
            lord_karaka_identical=False,
            fired_benefic=("b",), fired_malefic=(), fired_neutral=(),
            flags=("MARAKA_NON_DEATH_GUARD",), lord_hard_afflicted=False)
        chart = self._FakeChart({"Venus": self._FakePlanet(5.37)})
        return chart, mh, led

    def test_mixed_from_marginal_cliff_is_lifted(self):
        """Without a bond demote, the widened trigger lifts the marginal-cliff 'mixed'."""
        chart, mh, led = self._fixture()
        v, md = ht._marginal_karaka_gate(chart, mh, "mixed", led, bond_demoted=False)
        assert v == "favourable" and md

    def test_bond_demoted_mixed_is_never_relifted(self):
        """With bond_demoted=True the SAME configuration stays 'mixed' — the demote is
        doctrine, not the cliff artefact."""
        chart, mh, led = self._fixture()
        v, md = ht._marginal_karaka_gate(chart, mh, "mixed", led, bond_demoted=True)
        assert v == "mixed" and md == ()

    def test_afflicted_trigger_unaffected_by_bond_flag(self):
        """The original afflicted arm ignores bond_demoted (the bond gate never emits
        afflicted, so there is no interaction to guard)."""
        chart, mh, led = self._fixture()
        v, _ = ht._marginal_karaka_gate(chart, mh, "afflicted", led, bond_demoted=True)
        assert v == "favourable"
