"""KP event timing registry (ruling R19)."""

from __future__ import annotations

from app.kp.chart import Birth, cast
from app.kp.citations import CITATIONS
from app.kp.events import EVENTS, coverage, event_windows
from app.kp.significators import houses_signified, planet_significations

BLR = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)


class TestEventRegistry:
    def test_every_event_is_cited(self) -> None:
        """Each event names at least one citation that exists."""
        for e in EVENTS.values():
            assert e.citations and all(c in CITATIONS for c in e.citations), e.key

    def test_house_groups_are_krishnamurtis(self) -> None:
        """Spot-check the printed groups: business 2,7,10; building 4,11,12; transfer 3,9,12; childbirth 2,5,11."""
        assert EVENTS["business"].houses == {2, 7, 10}
        assert EVENTS["building"].houses == {4, 11, 12}
        assert EVENTS["transfer"].houses == {3, 9, 12} and EVENTS["transfer"].confirm == {6, 10}
        assert EVENTS["childbirth"].houses == {2, 5, 11}

    def test_no_longevity_event(self) -> None:
        """Ruling R20: longevity and maraka timing are not encoded."""
        assert not any(k in EVENTS for k in ("death", "longevity", "maraka"))


class TestEventWindows:
    def test_all_three_lords_signify(self) -> None:
        """Every window's dasa, bhukti and antara lords signify one of the event houses."""
        c = cast(BLR)
        sigs = planet_significations(c)
        for w in event_windows(c, "building", from_age=20, to_age=30):
            assert all(houses_signified(c, l, sigs) & EVENTS["building"].houses for l in w.period.lords)

    def test_coverage_is_a_share(self) -> None:
        """Coverage (the chance rate of a hit) lies in [0, 1]."""
        c = cast(BLR)
        j0, j1 = c.jd_ut + 20 * 365.2425, c.jd_ut + 40 * 365.2425
        cov = coverage(event_windows(c, "marriage", from_age=20, to_age=40), j0, j1)
        assert 0.0 <= cov <= 1.0
