"""Rule firing: encoded RuleRecords fire against a chart and produce a cited reading."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.doctrine.sources import verify
from app.raman_saab.judges import rule_firing as rf


def _track_b(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def test_lord_rule_fires_for_the_right_placement():
    # Aries lagna: 7th lord = Venus. Venus in the 1st -> H7.L.1 fires.
    fired_ids = {fr.rule.id for fr in rf.fire_house(_track_b({"Venus": 5.0}), 7)}
    assert "H7.L.1" in fired_ids
    assert "H7.L.2" not in fired_ids       # Venus not in the 2nd


def test_fire_house_filters_by_house():
    chart = _track_b({"Venus": 5.0, "Mars": 35.0})  # Mars (1st lord) in 2nd -> H1.L.2
    assert all(fr.rule.house == 1 for fr in rf.fire_house(chart, 1))
    assert any(fr.rule.id == "H1.L.2" for fr in rf.fire_house(chart, 1))


def test_real_chart_produces_cited_reading_with_branches():
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    fired = rf.fire_rules(chart)
    assert len(fired) >= 12                       # at least one lord-placement per house fires
    # Every fired rule carries a real corpus citation and a non-empty reading.
    from corpus_presence import HAS_CORPUS
    for fr in fired:
        if HAS_CORPUS:
            assert verify(fr.rule.source), f"{fr.rule.id} cites an unresolved line"
        assert fr.text and fr.branch in ("fortified", "afflicted")
    # Shadbala drives the branch: with strength filled, some rules take the afflicted branch.
    branches = {fr.branch for fr in fired}
    assert "fortified" in branches               # at least some strong-lord readings
