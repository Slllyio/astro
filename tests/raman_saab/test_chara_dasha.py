"""Jaimini Chara Dasha (KN Rao convention) — structural invariants."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import chara_dasha as cd

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def _ch():
    return cast_chart(_MAINPURI, ayanamsa="lahiri")


def test_twelve_periods_cover_every_sign_once():
    seq = cd.chara_dasha(_ch())
    assert len(seq) == 12
    assert sorted(s for s, _ in seq) == list(range(1, 13))


def test_durations_in_1_to_12():
    for _, yrs in cd.chara_dasha(_ch()):
        assert 1 <= yrs <= 12


def test_even_lagna_runs_reverse():
    # Mainpuri Lagna = Scorpio (8, even) -> reverse: starts Scorpio(8), then Libra(7).
    seq = cd.chara_dasha(_ch())
    assert seq[0][0] == 8 and seq[1][0] == 7


def test_chara_dasha_on_returns_a_running_period():
    ch = _ch()
    cur = cd.chara_dasha_on(ch, 5.0)
    assert cur is not None and 1 <= cur[0] <= 12
    # age 0 is the first period
    assert cd.chara_dasha_on(ch, 0.0) == cd.chara_dasha(ch)[0]


def test_chara_dasha_dated_spans_are_contiguous_jd_arithmetic():
    """The dated accessor mirrors the undated sequence exactly, spans contiguous from the
    birth JD with span length == years * 365.2425 (JD arithmetic, never timedelta)."""
    ch = _ch()
    spans = cd.chara_dasha_dated(ch)
    assert [(s, y) for s, y, _lo, _hi in spans[:12]] == cd.chara_dasha(ch)
    assert abs(spans[0][2] - ch.jd_ut) < 1e-9
    for (_s1, y1, lo1, hi1), (_s2, _y2, lo2, _hi2) in zip(spans, spans[1:]):
        assert abs(hi1 - lo2) < 1e-9
        assert abs((hi1 - lo1) - y1 * 365.2425) < 1e-6


def test_chara_dasha_dated_repeats_the_cycle_through_jd():
    """One cycle by default; a through_jd past the first cycle appends the repeat (KN Rao),
    in the same sign order."""
    ch = _ch()
    one = cd.chara_dasha_dated(ch)
    assert len(one) == 12
    two = cd.chara_dasha_dated(ch, through_jd=one[-1][3] + 10.0)
    assert len(two) == 24
    assert [s for s, _y, _lo, _hi in two[12:]] == [s for s, _y, _lo, _hi in two[:12]]
