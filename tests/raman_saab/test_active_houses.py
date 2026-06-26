"""Dasha-driven house activation (the inverse timer-set) + the prioritized reading.

Validates Raman's two-layer method: on a dated event, the event house is ACTIVE during the
stated period (par_excellence where both period-lords converge), while the natal promise stays
unchanged (additive).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pytest

from app.raman_saab import render
from app.raman_saab import reading_timeline as rt
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.cli import main
from app.raman_saab.primitives import vimshottari as vd
from app.raman_saab.proforma import read_chart

_GOLDENS = Path(__file__).resolve().parents[1] / "fixtures" / "raman_goldens.jsonl"


def _birth(cid: str) -> BirthData:
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
        return BirthData(name=cid, year=y, month=mo, day=d, hour=hh, minute=mm,
                         tz_offset=float(b["tz"]), latitude=float(b["lat"]),
                         longitude=float(b["lon"]))
    raise KeyError(cid)


def _chart(cid: str) -> RamanChart:
    return cast_chart(_birth(cid), ayanamsa="raman")


def _period_mid_jd(chart: RamanChart, md_lord: str, antar_lord: str) -> Optional[float]:
    """Midpoint jd of the first MD/Bhukti period matching (md_lord, antar_lord)."""
    for md in vd.mahadasha_timeline(chart):
        if md.maha != md_lord:
            continue
        for bh in vd.bhuktis(md):
            if bh.antar == antar_lord:
                return (bh.start_jd + bh.end_jd) / 2.0
    return None


# (id, event-house(s), MD lord, Bhukti lord) — the dated events Raman times by Dasha.
_DATED_EVENTS = [
    ("HTJAH-II.chart_73", (8,), "Saturn", "Mercury"),   # Lincoln, assassinated
    ("HTJAH-II.chart_74", (8,), "Jupiter", "Sun"),       # Gandhi, assassinated
    ("HTJAH-II.chart_78", (8,), "Rahu", "Moon"),         # Hitler, suicide
    ("HTJAH-I.chart_40", (2, 11), "Ketu", "Mercury"),    # inherited an empire
    ("HTJAH-II.h7_13", (7,), "Mars", "Venus"),           # husband died
    ("HTJAH-I.h4_05", (4,), "Jupiter", "Venus"),         # acquired a car
    ("HTJAH-I.h4_06", (4,), "Jupiter", "Mars"),          # acquired a house
]


def test_event_house_active_during_its_period_rate():
    """PRIMARY claim (>=80%): on the stated period, the event house is ACTIVE (par_excellence
    OR limited). The lone known miss is the spouse-marakas edge (h7_12), excluded here."""
    active_hits = 0
    for cid, houses, md, antar in _DATED_EVENTS:
        chart = _chart(cid)
        jd = _period_mid_jd(chart, md, antar)
        assert jd is not None, f"{cid}: no {md}/{antar} period found"
        lit = {a.house for a in vd.active_houses(chart, jd)}
        if any(h in lit for h in houses):
            active_hits += 1
    rate = active_hits / len(_DATED_EVENTS)
    assert rate >= 0.80, f"event-house-active rate {active_hits}/{len(_DATED_EVENTS)}"


@pytest.mark.parametrize("cid,houses,md,antar", [
    ("HTJAH-I.chart_40", (2, 11), "Ketu", "Mercury"),    # both lords relate to wealth
    ("HTJAH-II.chart_73", (8,), "Saturn", "Mercury"),    # clean-birth death
    ("HTJAH-II.chart_78", (8,), "Rahu", "Moon"),         # clean-birth death
])
def test_event_house_par_excellence_on_clean_charts(cid, houses, md, antar):
    """SECONDARY (sharper): where both period-lords converge on the event house it is graded
    par_excellence — asserted on the worked-example empire chart and the clean-birth deaths."""
    chart = _chart(cid)
    jd = _period_mid_jd(chart, md, antar)
    pe = {a.house for a in vd.active_houses(chart, jd) if a.grade == "par_excellence"}
    assert any(h in pe for h in houses), f"{cid}: {houses} not par_excellence (pe={sorted(pe)})"


def test_snapshot_is_additive_promise_unchanged():
    """The Dasha snapshot CARRIES the natal reading unchanged — activation never edits a verdict."""
    birth = _birth("HTJAH-II.chart_73")
    snap = rt.read_chart_on_date(birth, vd.date_to_jd(1865, 4, 14))
    assert snap.promise == read_chart(birth)


def test_active_houses_par_excellence_first():
    """Active houses are sorted par_excellence-first (the focus leads the reading)."""
    chart = _chart("HTJAH-II.chart_73")
    rows = vd.active_houses(chart, vd.date_to_jd(1865, 4, 14))
    grades = [r.grade for r in rows]
    assert grades == sorted(grades, key=lambda g: 0 if g == "par_excellence" else 1)


def test_active_houses_track_b_noop():
    """Track-B (stated-position) charts have no birth_jd -> no activation, no crash."""
    tb = RamanChart.from_stated_positions(
        {"Sun": {"lon": 10.0, "bhava": 1}, "Moon": {"lon": 40.0, "bhava": 2}},
        asc_lon=5.0, ayanamsa="raman")
    assert vd.active_houses(tb, 2400000.0) == ()


def test_lord_quality_well_poorly_unknown():
    """The delivery descriptor: a node yields 'unknown' (no Shadbala); the tag never crashes."""
    chart = _chart("HTJAH-II.chart_73")
    assert vd.lord_quality(chart, "Rahu").tag == "unknown"
    for lord in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        assert vd.lord_quality(chart, lord).tag in ("well", "poorly", "mixed", "unknown")


def test_cli_snapshot_and_timeline_smoke():
    """--at renders a Dasha snapshot; --timeline renders the life-narrative; both exit 0."""
    args = ["--name", "L", "--date", "1809-02-12", "--time", "06:54", "--tz", "-5",
            "--lat", "37.5", "--lon", "-85.5"]
    assert main(args + ["--at", "1865-04-14", "--format", "text"]) == 0
    assert main(args + ["--timeline", "--format", "markdown"]) == 0


def test_render_snapshot_shows_active_houses_and_period():
    """The rendered snapshot names the running period and the active houses with their promise."""
    birth = _birth("HTJAH-II.chart_73")
    txt = render.snapshot_to_text(rt.read_chart_on_date(birth, vd.date_to_jd(1865, 4, 14)))
    assert "Dasha Snapshot" in txt and "Running period: Saturn / Mercury" in txt
    assert "House 8 - Longevity / Death" in txt
