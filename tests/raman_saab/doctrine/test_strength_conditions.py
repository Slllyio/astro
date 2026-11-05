"""IsStrong / IsWeak: Raman's binary strength, read with the facts that override the number.

Built on `effective_strength` (B1), not raw `is_powerful`. Across the golden charts the raw
number calls a planet strong 198 times where Raman would call it powerless -- combust
(HTJAH-I:3788, "the ruler of the third becoming combust and hence powerless") or debilitated
without cancellation. Gating on the raw number was tried before and over-fired badly.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.primitives.effective_strength import effective_strength
from app.raman_saab.primitives.shadbala.total import is_powerful
from tools.raman_saab import doctrine_snapshot as ds


@pytest.fixture(scope="module")
def charts():
    out = []
    for rec in ds._h.load_goldens():
        try:
            out.append((ds._h._id(rec), ds._h.build_chart(rec)))
        except Exception:
            continue
    return out


class TestAgainstTheGoldens:
    def test_never_both_strong_and_weak(self, charts) -> None:
        """The two readings are exclusive; 'marginal' and unknown fall between them."""
        for cid, ch in charts:
            ctx = C.EvalContext(ch)
            for name in ch.planets:
                assert not (C.IsStrong(name).evaluate(ctx) and C.IsWeak(name).evaluate(ctx)), (cid, name)

    def test_they_are_exactly_the_effective_strength_reading(self, charts) -> None:
        """One measure, reused -- no second definition of 'strong' to drift."""
        for cid, ch in charts[:60]:
            ctx = C.EvalContext(ch)
            for name in ch.planets:
                es = effective_strength(name, ch)
                assert C.IsStrong(name).evaluate(ctx) == (es.band == "strong" and not es.decisively_weak)
                assert C.IsWeak(name).evaluate(ctx) == es.decisively_weak

    def test_a_combust_or_debilitated_planet_is_not_strong_whatever_its_number(self, charts) -> None:
        """HTJAH-I:3788: a combust ruler is 'powerless' even when otherwise well disposed. The
        raw bar alone would call these strong."""
        overridden = []
        for cid, ch in charts:
            ctx = C.EvalContext(ch)
            for name, p in ch.planets.items():
                if (p.shadbala_rupas is not None
                        and is_powerful(name, p.shadbala_rupas.total / 60.0)
                        and not C.IsStrong(name).evaluate(ctx)):
                    assert C.IsWeak(name).evaluate(ctx), (cid, name)
                    overridden.append((cid, name))
        assert len(overridden) >= 100, len(overridden)


class TestUnknownStrengthIsNotGuessed:
    @staticmethod
    def _ctx(planets: dict[str, float]) -> C.EvalContext:
        return C.EvalContext(RamanChart.from_stated_positions(
            {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
            asc_lon=5.0, ayanamsa="raman"))

    def test_no_shadbala_means_never_strong(self) -> None:
        """A Track-B chart carries no Shadbala; a missing number is not a high one."""
        ctx = self._ctx({"Mars": 10.0})                  # Mars in its own Aries
        assert C.IsStrong("Mars").evaluate(ctx) is False
        assert C.IsWeak("Mars").evaluate(ctx) is False

    def test_hard_facts_still_make_a_planet_weak_without_shadbala(self) -> None:
        """The Sun at 10 deg Libra is debilitated; nothing here cancels it."""
        ctx = self._ctx({"Sun": 190.0})
        assert C.IsWeak("Sun").evaluate(ctx) is True
        assert C.IsStrong("Sun").evaluate(ctx) is False

    def test_the_nodes_are_never_strong(self) -> None:
        """Rahu and Ketu carry no Shadbala (GBB-3, seven grahas)."""
        ctx = self._ctx({"Rahu": 100.0})
        assert C.IsStrong("Rahu").evaluate(ctx) is False


class TestHouseLordReferences:
    def test_lord_of_resolves_to_the_same_answer_as_the_named_planet(self, charts) -> None:
        """'LORD_OF:n' must read the actual lord, not silently return False."""
        from app.raman_saab.chart.constants import SIGN_LORDS
        for cid, ch in charts[:40]:
            ctx = C.EvalContext(ch)
            lord1 = SIGN_LORDS[ch.asc_sign]
            assert C.IsStrong("LORD_OF:1").evaluate(ctx) == C.IsStrong(lord1).evaluate(ctx), cid
            assert C.IsWeak("LORD_OF:1").evaluate(ctx) == C.IsWeak(lord1).evaluate(ctx), cid


class TestPromotedClauses:
    """The clauses parked on 'needs a strength predicate' are live, with strength in the
    condition and the text in `general` -- never chosen by `_branch`, which tests the rule's
    HOUSE lord with the raw number."""

    PROMOTED = ["H1.L.4a", "H3.L.4a", "H3.L.4b", "H3.L.4c", "H6.L.2b", "H6.L.6a", "H7.L.6c",
                "H7.L.7a", "H7.L.12c", "H8.L.6b", "H8.L.9d", "H10.L.10a", "H10.L.10b", "H12.L.4a"]

    @pytest.mark.parametrize("rid", PROMOTED)
    def test_is_live_neutral_and_text_in_general(self, rid: str) -> None:
        from app.raman_saab.doctrine.rule_sets import ALL_RULES
        r = next(x for x in ALL_RULES if x.id == rid)
        assert r.kind == "evaluable" and r.polarity == "neutral", rid
        assert r.general and not r.fortified and not r.afflicted, rid
        assert "TODO(" not in r.general, rid

    def test_weak_and_afflicted_needs_both_halves(self) -> None:
        """H7.L.7a: the case the slot machinery could never express."""
        from app.raman_saab.doctrine.rule_sets import ALL_RULES
        r = next(x for x in ALL_RULES if x.id == "H7.L.7a")
        kinds = {type(c).__name__ for c in r.condition.conds}
        assert {"IsWeak", "AfflictedBy"} <= kinds

    def test_h7_l6c_witness_debility_alone_makes_venus_weak(self) -> None:
        """Aries rising: Venus is the 7th lord; in Virgo (the 6th) she is debilitated, which
        makes her weak even with no Shadbala on the chart, and nothing afflicts her."""
        from app.raman_saab.doctrine.rule_sets import ALL_RULES
        r = next(x for x in ALL_RULES if x.id == "H7.L.6c")
        ctx = C.EvalContext(RamanChart.from_stated_positions(
            {"Venus": {"lon": 160.0, "bhava": 6}}, asc_lon=5.0, ayanamsa="raman"))
        assert r.condition.evaluate(ctx) is True
