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
