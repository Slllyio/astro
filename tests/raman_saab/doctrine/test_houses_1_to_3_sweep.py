"""Houses 1-3 strength-slot sweep (2026-10-13): what changed, and proof the rare new rules can fire.

Three engine-blind reviews read every House 1-3 lord-in-house entry against HTJAH-I. Base rates:
H1 10/12, H2 3/12, H3 7/12 correctly encoded. No entry inverted Raman's meaning; the defects
were clauses gated on something the strength branch cannot test -- an affliction, another
planet, a conjunction, a sign -- sitting in a strength slot. Every displaced clause was re-homed,
nothing deleted, and every new record is `neutral` (it refines a parent that already votes for
the placement), so the sweep moved no verdict.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_R = {r.id: r for r in ALL_RULES}
_NEW = ["H1.L.1a", "H1.L.4a", "H2.L.1a", "H2.L.2b", "H2.L.2c", "H2.L.2d", "H2.L.2e", "H2.L.2f",
        "H2.L.4a", "H2.L.6a", "H2.L.7a", "H2.L.7b", "H2.L.9a", "H2.L.10a", "H2.L.12a",
        "H3.L.3a", "H3.L.3b", "H3.L.3c", "H3.L.4a", "H3.L.4b", "H3.L.4c", "H3.L.6a", "H3.L.6b",
        "H3.L.7a", "H3.L.9a"]


def _ctx(planets: dict[str, float], asc_lon: float) -> C.EvalContext:
    return C.EvalContext(RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=asc_lon, ayanamsa="raman"))


class TestEveryRehomedClauseIsCitedAndNeutral:
    @pytest.mark.parametrize("rid", _NEW)
    def test_record_is_cited_and_casts_no_second_vote(self, rid: str) -> None:
        """Re-homed clauses display Raman's words without counting a placement twice."""
        r = _R[rid]
        assert r.source.work == "HTJAH-I" and r.source.line > 0
        assert r.polarity == "neutral", rid
        assert any((getattr(r, s) or "").strip() for s in ("general", "fortified", "afflicted"))


class TestTheDefectsAreGone:
    def test_h1_l4_no_longer_shows_the_4th_lords_reading_as_the_lagna_lords(self) -> None:
        """HTJAH-I:1026 opens "If the 4th lord is favourably disposed" -- a different planet."""
        assert _R["H1.L.4"].fortified is None
        # Live since 2026-10-13: the 4th lord's strength is in the CONDITION (IsStrong), so the
        # text is shown whenever the rule fires rather than chosen by the Lagna lord's branch.
        assert "4th lord favourably disposed" in _R["H1.L.4a"].general
        assert _R["H1.L.4a"].kind == "evaluable"

    def test_h2_l2_dropped_tara_remark_is_restored(self) -> None:
        """HTJAH-I:2335 (the 2nd lord outside the 3rd/5th/7th tara) was missing entirely."""
        assert "Janma Nakshatra" in _R["H2.L.2b"].general

    def test_h2_l2f_records_ramans_own_contradiction_instead_of_firing_it(self) -> None:
        """2506 sits under "In the second" but gates on an exchange that puts the 2nd lord in
        the 1st -- unsatisfiable with its own heading, so it is kept but never fired."""
        assert _R["H2.L.2f"].kind == "descriptive"
        assert "cannot hold together with its own heading" in _R["H2.L.2f"].general

    def test_h3_l3_identity_clauses_fire_on_the_planet_not_on_weakness(self) -> None:
        """Mars in the 3rd in Aries IS the 3rd lord in the 3rd (Aquarius rising)."""
        ctx = _ctx({"Mars": 5.0}, asc_lon=305.0)            # Aquarius asc, Mars 5 Aries
        assert C.LordIn(3, 3).evaluate(ctx) is True
        assert _R["H3.L.3a"].condition.evaluate(ctx) is True
        assert _R["H3.L.3b"].condition.evaluate(ctx) is False

    def test_dropped_words_are_restored(self) -> None:
        assert "good-natured" in _R["H2.L.3"].general
        assert "dissimulation" in _R["H2.L.6"].fortified


class TestTheStrengthGatedRulesUseRealStrength:
    """H2.L.4a/7a/9a first shipped on the conservative dignity proxy (exalted / own /
    moolatrikona), so a weak 2nd lord would never be shown a strength-gated reading. The proxy
    was replaced on 2026-10-13 by IsStrong -- Raman's binary strength, read with the facts that
    override the number (combustion, uncancelled debility)."""

    @pytest.mark.parametrize("rid", ["H2.L.4a", "H2.L.7a", "H2.L.9a"])
    def test_no_dignity_proxy_remains(self, rid: str) -> None:
        conds = _R[rid].condition.conds
        assert any(isinstance(c, C.IsStrong) for c in conds), rid
        assert not any(isinstance(c, C.LordHasDignity) for c in conds), rid

    def test_h2_l9a_fires_on_a_real_cast_chart(self) -> None:
        """No golden exercises H2.L.9a, and a synthetic chart carries no Shadbala, so the witness
        is a real cast chart: 1950-01-03 06:00 IST at Bangalore -- the 2nd lord in the 9th, the
        9th lord in the Lagna, and the 2nd lord strong."""
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.chart.model import BirthData
        ch = cast_chart(BirthData("witness", 1950, 1, 3, 6, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
        assert _R["H2.L.9a"].condition.evaluate(C.EvalContext(ch)) is True

    def test_placements_alone_never_fire_it_without_known_strength(self) -> None:
        """Scorpio rising: Jupiter (2nd lord) exalted in Cancer, the 9th; the Moon (9th lord) in
        the Lagna. Every placement holds, but a stated-position chart has no Shadbala -- and a
        missing number is never read as 'strong'."""
        ctx = _ctx({"Jupiter": 95.0, "Moon": 220.0}, asc_lon=215.0)
        assert C.LordIn(2, 9).evaluate(ctx) and C.LordIn(9, 1).evaluate(ctx)
        assert _R["H2.L.9a"].condition.evaluate(ctx) is False


