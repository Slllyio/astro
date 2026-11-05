"""Scan-the-day — the clean spans are nothing but runs of the SAME single-moment judgment.

Every test here is ephemeris-free: `scan_day` takes a caller-supplied sampler, so the
doctrine under test is the iteration (equivalence with `evaluate_moment`, blocked windows
excluded, contiguity/ordering), never the ephemeris.
"""
from __future__ import annotations

import pytest

from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.electional.day_scanner import (
    DEFAULT_SAMPLE_MINUTES,
    MomentInputs,
    jd_to_local_iso,
    rank_spans,
    scan_day,
)
from app.raman_saab.electional.negative_windows import Window
from app.raman_saab.electional.window_scorer import evaluate_moment

_DAY_START = 2460000.0          # arbitrary JD; the scanner is pure arithmetic over it
_DAY_END = _DAY_START + 1.0
_STEP = DEFAULT_SAMPLE_MINUTES / 1440.0

#: A moment that passes every essential: five suitable limbs, Kshema tarabala (janma star 1 ->
#: day star 4), Moon in the janma rasi itself (Chandrabala), panchaka 1+1+4+8 = 14 -> 5 (good).
_CLEAN = MomentInputs(tithi_in_paksha=1, weekday=0, day_nakshatra=4, yoga=2, karana=1,
                      election_moon_rasi=1, lagna_sign=8)
#: Same moment with the Moon 6th from the janma rasi — a Chandrabala HARD failure that owes
#: nothing to any negative window (MUHURTHA-3:66-71).
_MOON_FAILS = MomentInputs(**{**_CLEAN.__dict__, "election_moon_rasi": 6})

_NATIVE = dict(janma_nakshatra=1, janma_rasi=1)

#: A long blocked window (like Rahu Kalam) that swallows several samples, and a SHORT one that
#: fits entirely between two consecutive samples — the case a naive "join adjacent clean
#: samples" would pave straight over.
_LONG_WINDOW = Window(_DAY_START + 0.25, _DAY_START + 0.3125, "Rahu Kalam",
                      Citation("MUHURTHA-18", 767))
_GAP_WINDOW = Window(_DAY_START + 0.505, _DAY_START + 0.510, "Durmuhurtha (diurnal 10)",
                     Citation("MUHURTHA-4", 290))
_WINDOWS = (_LONG_WINDOW, _GAP_WINDOW)


def _sampler(jd: float) -> MomentInputs:
    """Clean all day except a stretch where the Moon moves 6th from the janma rasi."""
    return _MOON_FAILS if _DAY_START + 0.60 <= jd < _DAY_START + 0.70 else _CLEAN


def _scan(**kw):
    return scan_day(day_start_jd=_DAY_START, day_end_jd=_DAY_END, sampler=_sampler,
                    negative_windows=_WINDOWS, **{**_NATIVE, **kw})


class TestScanDayEquivalence:
    def test_every_sample_in_a_span_passes_the_same_scorer_directly(self):
        """A span claims nothing the single-moment judgment does not: re-judging each of its
        sample points with `evaluate_moment` reproduces ok=True and the identical score."""
        scan = _scan()
        by_jd = {s.jd: s for s in scan.samples}
        for span in scan.clean_spans:
            inside = [s for s in scan.samples if span.start_jd <= s.jd < span.end_jd]
            assert inside, "a span must own the samples that produced it"
            for s in inside:
                direct = evaluate_moment(jd=s.jd, **_NATIVE, **_sampler(s.jd).__dict__,
                                         negative_windows=_WINDOWS)
                assert direct.ok, s.local_iso
                assert direct.score == s.score == by_jd[s.jd].evaluation.score
            assert span.score == min(s.score for s in inside)
            assert span.score_max == max(s.score for s in inside)
            assert span.samples == len(inside)

    def test_span_factors_are_the_scorers_own_favourable_essentials(self):
        """`passing` = favourable at EVERY sample, `failing` = unfavourable at some sample;
        together they are exactly the eight essentials, and `score` is the passing count."""
        scan = _scan()
        for span in scan.clean_spans:
            assert not set(span.passing) & set(span.failing)
            assert len(span.passing) + len(span.failing) == 8
            # a sample scores its OWN favourable factors, which always include the span-wide
            # intersection — so the guaranteed score can never fall below the passing count.
            assert span.score >= len(span.passing)

    def test_a_failing_sample_never_lands_inside_a_span(self):
        for scan in (_scan(),):
            for s in scan.samples:
                if s.ok:
                    continue
                assert not any(sp.start_jd <= s.jd < sp.end_jd for sp in scan.clean_spans)


class TestScanDayWindows:
    def test_a_hard_blocked_window_never_overlaps_a_clean_span(self):
        """Rahu Kalam / Durmuhurtha are hard failures (MUHURTHA-10:226-228 ordering), so a
        span may not merely avoid their sample points — it may not touch them at all."""
        scan = _scan()
        assert scan.clean_spans
        for span in scan.clean_spans:
            for w in _WINDOWS:
                assert not (w.start_jd < span.end_jd and w.end_jd > span.start_jd), (
                    f"{w.label} overlaps {span.start_local}..{span.end_local}")

    def test_a_window_hiding_between_two_samples_splits_the_span(self):
        """The 7.2-minute `_GAP_WINDOW` touches no sample, yet the run it sits in must break
        there rather than be paved over — and the earlier piece must stop at its start."""
        scan = _scan()
        ends_before = [sp for sp in scan.clean_spans if sp.end_jd <= _GAP_WINDOW.start_jd + 1e-9]
        assert any(abs(sp.end_jd - _GAP_WINDOW.start_jd) < 1e-9 for sp in ends_before)
        assert any(abs(sp.start_jd - (_DAY_START + 0.5 + _STEP)) < 1e-9
                   for sp in scan.clean_spans)

    def test_the_scan_reports_the_windows_it_was_given(self):
        assert _scan().blocked_windows == _WINDOWS


class TestScanDayShape:
    def test_spans_are_contiguous_non_overlapping_and_chronological(self):
        scan = _scan()
        assert len(scan.clean_spans) > 1
        last_end = None
        for span in scan.clean_spans:
            assert span.end_jd > span.start_jd
            assert span.duration_minutes > 0
            if last_end is not None:
                assert span.start_jd >= last_end          # no overlap, forward order
            last_end = span.end_jd
            # contiguous: the span's own samples run consecutively at the sample interval
            inside = sorted(s.jd for s in scan.samples
                            if span.start_jd <= s.jd < span.end_jd)
            for a, b in zip(inside, inside[1:]):
                assert abs((b - a) - _STEP) < 1e-9
            assert abs(inside[0] - span.start_jd) < 1e-9

    def test_samples_cover_the_day_at_the_requested_interval(self):
        scan = _scan(sample_minutes=15)
        assert scan.sample_minutes == 15
        assert len(scan.samples) == 96
        assert all(s.local_iso.endswith("+00:00") for s in scan.samples)
        for a, b in zip(scan.samples, scan.samples[1:]):
            assert abs((b.jd - a.jd) - 15 / 1440.0) < 1e-9
        assert scan.samples[-1].jd < _DAY_END

    def test_default_interval_is_half_an_hour(self):
        scan = _scan()
        assert scan.sample_minutes == DEFAULT_SAMPLE_MINUTES == 30
        assert len(scan.samples) == 48
        assert scan.clean_sample_count == sum(1 for s in scan.samples if s.evaluation.ok)

    def test_a_day_with_no_clean_moment_yields_no_spans(self):
        scan = scan_day(day_start_jd=_DAY_START, day_end_jd=_DAY_END,
                        sampler=lambda jd: _MOON_FAILS, negative_windows=_WINDOWS, **_NATIVE)
        assert scan.clean_spans == ()
        assert scan.clean_sample_count == 0

    def test_act_is_passed_through_to_the_scorer(self):
        """MUHURTHA-3:157-168 — naming the act can only relax a panchaka verdict, so the act
        argument must reach `evaluate_moment` (panchaka 1+1+4+1 = 7 ... lagna 2 -> 8 = roga)."""
        roga = MomentInputs(**{**_CLEAN.__dict__, "lagna_sign": 2})
        blocked = scan_day(day_start_jd=_DAY_START, day_end_jd=_DAY_START + 0.2,
                           sampler=lambda jd: roga, **_NATIVE)
        relaxed = scan_day(day_start_jd=_DAY_START, day_end_jd=_DAY_START + 0.2,
                           sampler=lambda jd: roga, act="travel", **_NATIVE)
        assert blocked.clean_spans == ()
        assert relaxed.clean_spans and relaxed.clean_sample_count == len(relaxed.samples)

    @pytest.mark.parametrize("kw", [{"sample_minutes": 0}, {"sample_minutes": -30}])
    def test_a_non_positive_interval_is_rejected(self, kw):
        with pytest.raises(ValueError):
            _scan(**kw)

    def test_an_empty_or_reversed_day_is_rejected(self):
        with pytest.raises(ValueError):
            scan_day(day_start_jd=_DAY_END, day_end_jd=_DAY_START,
                     sampler=_sampler, **_NATIVE)


class TestRankingAndFormatting:
    def test_rank_spans_orders_by_score_then_length_then_time(self):
        ranked = rank_spans(_scan().clean_spans)
        keys = [(-s.score, -s.duration_minutes, s.start_jd) for s in ranked]
        assert keys == sorted(keys)
        assert sorted(ranked, key=lambda s: s.start_jd) == sorted(
            _scan().clean_spans, key=lambda s: s.start_jd)

    def test_local_iso_renders_at_the_callers_offset(self):
        """JD 2460000.5 is 2023-02-25 00:00 UT; at +05:30 that is 05:30 the same morning."""
        assert jd_to_local_iso(2460000.5, 0.0) == "2023-02-25T00:00:00+00:00"
        assert jd_to_local_iso(2460000.5, 5.5) == "2023-02-25T05:30:00+05:30"
