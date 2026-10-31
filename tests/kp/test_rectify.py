"""Tests for app.kp.rectify: scoring rules, resolution honesty, the event split and the reuse guard."""

from __future__ import annotations

import pytest

from app.kp.chart import Birth, cast
from app.kp.dasa import periods_on
from app.kp.rectify import (
    EventLedger, KPEvent, KP_EVENT_TYPES, ReuseError, rectify, score_event, split_events,
)
from app.kp.significators import houses_signified

BANGALORE = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)


class TestEventTypes:
    def test_every_type_cites_reader3_period_rule(self) -> None:
        """Each event type times by KPR3-PERIODS (period lords signifying the houses)."""
        assert all("KPR3-PERIODS" in t.citations for t in KP_EVENT_TYPES.values())

    def test_unknown_type_is_refused(self) -> None:
        """Free-text event types are a hard error, not guessed."""
        with pytest.raises(ValueError):
            KPEvent("promotion", 2010, 1, 1)


class TestResolutionHonesty:
    def test_year_event_cannot_claim_antara(self) -> None:
        """A year-dated event scores at most the levels one period covers for the whole year (RR3)."""
        chart = cast(BANGALORE)
        es = score_event(chart, KPEvent("marriage", 2016))
        assert len(es.lords) <= 2

    def test_day_event_scores_three_levels(self) -> None:
        """A day-dated event gets dasa, bhukti and antara lords."""
        chart = cast(BANGALORE)
        es = score_event(chart, KPEvent("marriage", 2016, 2, 14))
        assert len(es.lords) == 3


class TestPlantedEvent:
    def test_event_planted_in_matching_antara_is_a_timing_match(self) -> None:
        """An event dated inside an antara whose lords all signify 2/7/11 scores a timing match."""
        chart = cast(BANGALORE)
        from app.kp.dasa import periods_between
        from app.kp.significators import planet_significations
        sigs = planet_significations(chart)
        sp = KP_EVENT_TYPES["marriage"]
        win = next(w for w in periods_between(chart, chart.jd_ut + 20 * 365.2425, chart.jd_ut + 50 * 365.2425)
                   if all(houses_signified(chart, l, sigs) & sp.houses for l in w.lords)
                   and w.end_jd - w.start_jd > 4)
        import swisseph as swe
        y, m, d, _ = swe.revjul(win.start_jd + 2)
        es = score_event(chart, KPEvent("marriage", y, m, d))
        assert es.timing and es.lords == win.lords
        assert periods_on(chart, win.start_jd + 2, depth=3)[-1].lords == win.lords


class TestRectify:
    def test_window_has_every_minute_and_handoff_covers_top_set(self) -> None:
        """±10 gives 21 minutes; the KP hand-off window covers every top-scoring minute."""
        evs = [KPEvent("marriage", 2016, 2, 14), KPEvent("service_start", 2012, 7, 1),
               KPEvent("childbirth", 2018, 5, 3)]
        r = rectify(BANGALORE, evs, window_minutes=10)
        assert len(r.minutes) == 21
        kb = r.kp_birth()
        lo, hi = min(r.top_offsets), max(r.top_offsets)
        assert kb.uncertainty_minutes >= (hi - lo) / 2
        assert 0 < r.top_share <= 1

    def test_percentile_rank_is_half_when_all_tie(self) -> None:
        """If every minute ties, any minute ranks at chance (0.5)."""
        r = rectify(BANGALORE, [KPEvent("gain", 1700)], window_minutes=2)
        if len({m.total for m in r.minutes}) == 1:
            assert r.percentile_rank(0) == 0.5


class TestSplitAndLedger:
    EVS = [KPEvent("marriage", 2016, 2, 14), KPEvent("service_start", 2012, 7, 1),
           KPEvent("childbirth", 2018, 5, 3), KPEvent("illness", 2020, 4, 1)]

    def test_split_is_deterministic_and_order_free(self) -> None:
        """The same person and events split the same way whatever their order."""
        a = split_events("p1", self.EVS)
        b = split_events("p1", list(reversed(self.EVS)))
        assert {e.key for e in a[0]} == {e.key for e in b[0]}
        assert len(a[0]) == 2 and len(a[1]) == 2

    def test_split_always_seals_one_event(self) -> None:
        """With two or more events at least one is sealed."""
        rect, sealed = split_events("p2", self.EVS[:2], rect_fraction=1.0)
        assert len(sealed) == 1

    def test_ledger_refuses_reuse(self) -> None:
        """An event that rectified a person cannot then test KP on that person."""
        rect, sealed = split_events("p1", self.EVS)
        led = EventLedger()
        rectify(BANGALORE, list(rect), window_minutes=1, ledger=led, person="p1")
        led.check_test("p1", sealed)
        with pytest.raises(ReuseError):
            led.check_test("p1", rect[:1])
        assert EventLedger.from_dict(led.to_dict()).used == led.used


class TestStabilityBand:
    def test_band_covers_every_minute_for_every_cusp(self) -> None:
        """Each cusp's runs tile the window with no gap or overlap."""
        from app.kp.rectify import stability_band
        b = stability_band(BANGALORE, 10)
        for c in range(1, 13):
            rs = b.cusp_runs(c)
            assert rs[0].start == -10 and rs[-1].end == 10
            assert all(x.end + 1 == y.start for x, y in zip(rs, rs[1:]))

    def test_zero_window_is_all_stable_and_matches_cast(self) -> None:
        """With no uncertainty every cusp is stable at the cast's own sub-lord."""
        from app.kp.rectify import stability_band
        b = stability_band(BANGALORE, 0)
        chart = cast(BANGALORE)
        assert all(b.stable(c) == chart.cusp(c).sub_lord for c in range(1, 13))
