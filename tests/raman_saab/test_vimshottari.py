"""Vimshottari Dasha timeline — validated against the canonical pin + Raman's dated deaths.

The Mahadasha running at the death date reproduces Raman's stated period for every dated
death golden; the canonical chart's birth Mahadasha is Mercury (CLAUDE.md test pin).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vd

_GOLDENS = Path(__file__).resolve().parents[1] / "fixtures" / "raman_goldens.jsonl"

# Raman's stated death Mahadasha/Bhukti for the dated death goldens (from the verdict prose).
_STATED_DEATH_DASHA = {
    "HTJAH-II.chart_35": ("Rahu", "Sun"),
    "HTJAH-II.chart_73": ("Saturn", "Mercury"),   # Lincoln
    "HTJAH-II.chart_74": ("Jupiter", "Sun"),       # Gandhi
    "HTJAH-II.chart_78": ("Rahu", "Moon"),         # Hitler
}


def _canonical_chart():
    return cast_chart(BirthData(name="c", year=1990, month=7, day=15, hour=12, minute=0,
                                tz_offset=5.5, latitude=12.97, longitude=77.59), ayanamsa="raman")


def _golden_chart(cid: str):
    for ln in _GOLDENS.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        r = json.loads(s)
        if r["id"] != cid:
            continue
        b = r["birth"]
        dp, _, tp = str(b["dt"]).partition("T")
        y, mo, d = (int(x) for x in dp.split("-"))
        hh, mm = int(tp.split(":")[0]), int(tp.split(":")[1])
        chart = cast_chart(BirthData(name="g", year=y, month=mo, day=d, hour=hh, minute=mm,
                                     tz_offset=float(b["tz"]), latitude=float(b["lat"]),
                                     longitude=float(b["lon"])), ayanamsa="raman")
        el = r.get("expected_longevity") or {}
        return chart, el.get("death_date")
    raise KeyError(cid)


def test_canonical_birth_mahadasha_is_mercury():
    """CLAUDE.md pin: Bangalore 1990-07-15 -> Mercury Mahadasha at birth."""
    ch = _canonical_chart()
    period = vd.dasha_on(ch, ch.jd_ut)
    assert period is not None and period.maha == "Mercury"


def test_timeline_is_contiguous_and_covers_a_full_cycle():
    """The Mahadasha periods are contiguous (no gaps/overlaps) and one cycle sums to 120y."""
    ch = _canonical_chart()
    tl = vd.mahadasha_timeline(ch)
    for a, b in zip(tl, tl[1:]):
        assert a.end_jd == pytest.approx(b.start_jd)            # contiguous
    nine = tl[:9]
    span_years = (nine[-1].end_jd - nine[0].start_jd) / 365.2425
    assert span_years == pytest.approx(120.0, abs=0.01)         # a full cycle


@pytest.mark.parametrize("cid", list(_STATED_DEATH_DASHA))
def test_death_mahadasha_matches_raman(cid: str):
    """The Mahadasha running at the death date reproduces Raman's stated MD for every
    dated death golden (the core timing validation)."""
    chart, death_date = _golden_chart(cid)
    dy, dmo, dd = (int(x) for x in death_date.split("-"))
    period = vd.dasha_on(chart, vd.date_to_jd(dy, dmo, dd))
    assert period is not None
    assert period.maha == _STATED_DEATH_DASHA[cid][0], \
        f"{cid}: engine MD {period.maha!r} != Raman {_STATED_DEATH_DASHA[cid][0]!r}"


def test_death_bhukti_matches_raman_for_clean_births():
    """For the two precisely-timed births, the Bhukti also matches exactly (Lincoln
    Saturn/Mercury, Hitler Rahu/Moon)."""
    for cid in ("HTJAH-II.chart_73", "HTJAH-II.chart_78"):
        chart, death_date = _golden_chart(cid)
        dy, dmo, dd = (int(x) for x in death_date.split("-"))
        period = vd.dasha_on(chart, vd.date_to_jd(dy, dmo, dd))
        assert (period.maha, period.antar) == _STATED_DEATH_DASHA[cid]


@pytest.mark.parametrize("cid", list(_STATED_DEATH_DASHA))
def test_death_falls_in_a_maraka_period(cid: str):
    """The strong, robust death-timing claim: the death's Mahadasha lord is a maraka, and the
    death falls in a maraka period, for every dated death golden (the engine recognises the
    death period as death-dealing — incl. the functional Rahu/Jupiter marakas)."""
    chart, death_date = _golden_chart(cid)
    dy, dmo, dd = (int(x) for x in death_date.split("-"))
    jd = vd.date_to_jd(dy, dmo, dd)
    ms = vd.maraka_set(chart)
    assert vd.dasha_on(chart, jd).maha in ms.all()        # death-MD lord is a maraka
    assert vd.is_maraka_period(chart, jd)                 # death falls in a maraka period


def test_death_window_returns_maraka_periods_near_span():
    """death_window yields maraka periods in the alloted-span region; for a near-span death
    (Gandhi, died ~78 ≈ ayurdaya span) the death falls inside one. (Premature/violent deaths
    strike a strong EARLIER maraka the engine does not isolate — a documented limit.)"""
    chart, death_date = _golden_chart("HTJAH-II.chart_74")
    dy, dmo, dd = (int(x) for x in death_date.split("-"))
    jd = vd.date_to_jd(dy, dmo, dd)
    windows = vd.death_window(chart)
    assert windows and all(w.score > 0 for w in windows)
    assert any(w.start_jd <= jd < w.end_jd for w in windows)


def test_significator_windows_catch_relative_death_mds():
    """General event-timing soft claim (death-class): the stated relative-death Mahadasha lord
    is among the matter's significators (here the maraka set), so it appears as an active window.
    Validated for the relative-death goldens; gains/career events that fall in a yoga-specific
    Dasha are a documented partial (see DOCTRINE_BACKLOG)."""
    for cid, sig_key, event_md in (("HTJAH-I.h4_01", "mother", "Mars"),
                                   ("HTJAH-II.h7_13", "coverture", "Mars"),
                                   ("HTJAH-II.h7_12", "coverture", "Saturn")):
        chart, _ = _golden_chart(cid)
        grahas = {"maraka": vd.maraka_set(chart).all()}
        windows = vd.significator_dasha_windows(chart, grahas)
        assert event_md in {w.graha for w in windows}, f"{cid}: {event_md} not an active window"


def test_timing_primitives_noop_on_track_b():
    """Track-B (stated-position) charts have no birth_jd -> timing primitives degrade cleanly."""
    from app.raman_saab.chart.model import RamanChart
    tb = RamanChart.from_stated_positions(
        {"Sun": {"lon": 10.0, "bhava": 1}, "Moon": {"lon": 40.0, "bhava": 2}},
        asc_lon=5.0, ayanamsa="raman")
    assert vd.death_window(tb) == ()
    assert vd.significator_dasha_windows(tb, {"maraka": frozenset({"Saturn"})}) == ()


def test_date_to_jd_and_dasha_on_outside_timeline():
    ch = _canonical_chart()
    assert vd.date_to_jd(2000, 1, 1) > vd.date_to_jd(1990, 1, 1)
    assert vd.dasha_on(ch, ch.jd_ut - 100 * 365.2425) is None   # before the timeline start
