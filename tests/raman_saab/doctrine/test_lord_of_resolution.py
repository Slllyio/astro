"""Every Condition must understand "the lord of house N", or fail loudly — never silently.

Rules refer to planets two ways: by name ("Mars") and by role ("LORD_OF:5", the lord of the
5th, which is a different planet in every chart). `_resolve_planet` turns the second into the
first. A Condition that skips it and reads `chart.planets` directly looks up the literal string
"LORD_OF:5", finds nothing, and returns **False for every chart ever cast** — no error, no
warning, no failing test. A rule built on it is dead on arrival and looks alive.

This was found TWICE in two days, both times only because a new rule happened to need it:

* `InHouseClass` — would have made H8.L.12b (HTJAH-II:3061) a dead rule;
* `Aspects`      — would have made H5.L.10a (HTJAH-I:5162) a dead rule.

A bug you can only discover by stepping on it needs a guard, not a fix. The sweep that followed
found eight more Conditions with the same shape and closed them; **zero shipped rules were
affected, because none had tried to use them yet** — which is exactly the point. This test fails
if a new Condition reintroduces the shape.
"""
from __future__ import annotations

import inspect
import re

import pytest

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C

#: A Condition taking one of these constructor args names a SUBJECT planet, so it must accept
#: a "LORD_OF:n" reference for it.
_SUBJECT_ARGS = ("planet", "a", "b", "afflicter", "target")


def _condition_classes():
    for name, obj in vars(C).items():
        if (inspect.isclass(obj) and issubclass(obj, C.Condition)
                and obj is not C.Condition and obj.__module__ == C.__name__):
            yield name, obj


class TestNoConditionSilentlyRejectsAHouseLord:
    def test_every_subject_taking_condition_routes_through_resolve_planet(self) -> None:
        offenders = []
        for name, cls in _condition_classes():
            try:
                init = inspect.getsource(cls.__init__)
                body = inspect.getsource(cls.evaluate)
            except (OSError, TypeError, AttributeError):
                continue
            takes_subject = re.search(
                r"def __init__\(self,\s*(%s)\b" % "|".join(_SUBJECT_ARGS), init)
            # WIDENED 2026-10-13: the first version required a direct `chart.planets` read, and
            # so missed six Conditions that hand the raw name to a helper instead (HasDignity,
            # IsYogaKaraka, MutualAspect, Exchange, HemmedBy, FunctionalNature). How the chart is
            # read does not matter; an unresolved "LORD_OF:n" is wrong either way.
            if takes_subject and "_resolve_planet" not in body:
                offenders.append(name)
        assert not offenders, (
            "these Conditions take a subject planet but read chart.planets directly, so a "
            "'LORD_OF:n' subject resolves to None and they return False for EVERY chart "
            "without raising: " + ", ".join(offenders) +
            ". Route the lookup through _resolve_planet — static names pass through unchanged.")


class TestTheResolutionActuallyWorks:
    """The scan above is structural. These check the behaviour it is standing in for."""

    @staticmethod
    def _chart():
        # Taurus ascendant (asc_sign 2). The 5th house is Virgo, so the 5th lord is Mercury.
        return RamanChart.from_stated_positions(
            {"Mercury": {"lon": 130.0, "bhava": 4},      # Leo -> 4th from Taurus
             "Sun": {"lon": 10.0, "bhava": 12}},         # Aries -> 12th from Taurus
            asc_lon=35.0, ayanamsa="raman")

    def test_the_fixture_is_what_the_assertions_assume(self) -> None:
        assert SIGN_LORDS[6] == "Mercury", "the 5th from Taurus is Virgo"
        ch = self._chart()
        assert ch.asc_sign == 2 and ch.planets["Mercury"].rasi_house == 4

    @pytest.mark.parametrize("cond,expected", [
        (C.InRashiHouse("LORD_OF:5", 4), True),
        (C.InRashiHouse("LORD_OF:5", 7), False),
        (C.InSign("LORD_OF:5", 5), True),
        (C.InHouseClass("LORD_OF:5", "kendra"), True),
        (C.InHouseClass("LORD_OF:5", "trikona"), False),
    ])
    def test_a_lord_of_subject_is_evaluated_against_the_right_planet(self, cond, expected):
        assert cond.evaluate(C.EvalContext(self._chart())) is expected

    def test_a_static_name_behaves_exactly_as_before(self) -> None:
        """The fix must be a strict generalisation — no shipped rule may change behaviour.
        The corpus-wide proof is the doctrine snapshot, which stayed IDENTICAL across all 346
        goldens; this is the unit-level statement of the same claim."""
        ctx = C.EvalContext(self._chart())
        assert C.InRashiHouse("Mercury", 4).evaluate(ctx) is True
        assert C.InRashiHouse("Mercury", 5).evaluate(ctx) is False
        assert C.InSign("Sun", 1).evaluate(ctx) is True

    def test_an_absent_lord_is_false_not_an_error(self) -> None:
        """Sparse Track-B charts carry only some planets; a missing lord must not raise."""
        sparse = RamanChart.from_stated_positions(
            {"Sun": {"lon": 10.0, "bhava": 1}}, asc_lon=35.0, ayanamsa="raman")
        assert C.InRashiHouse("LORD_OF:5", 4).evaluate(C.EvalContext(sparse)) is False

    def test_a_malformed_reference_raises_rather_than_reading_false(self) -> None:
        """An encoding typo must be loud. This is the whole distinction the file is about:
        wrong input raises, absent data returns False."""
        with pytest.raises(ValueError, match="malformed LORD_OF"):
            C.InRashiHouse("LORD_OF:x", 4).evaluate(C.EvalContext(self._chart()))
