"""House judge: fired rules + strength pillars -> an ordinal verdict (spec §6.3)."""
from __future__ import annotations

import pytest

from corpus_presence import needs_corpus

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.doctrine.karakas import BHAVA_KARAKA
from app.raman_saab.judges import house_judge as hj


def _track_b(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def test_verdict_is_an_ordinal():
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    for hv in hj.judge_all_houses(chart):
        assert hv.verdict in ("favourable", "mixed", "afflicted", "insufficient-evidence")
        assert hv.karaka == BHAVA_KARAKA[hv.house]
        assert hv.lord in chart.planets            # the bhava lord is a real graha


def test_track_b_decides_on_polarity_when_no_shadbala():
    # No Shadbala on a from_stated_positions chart -> verdict by rule polarity alone.
    # Aries lagna, Saturn (malefic) in the 8th -> H8.P.Saturn (malefic) fires; lord/karaka strength None.
    chart = _track_b({"Saturn": 220.0})
    hv = hj.judge_house(chart, 8)
    assert hv.lord_strong is None and hv.karaka_strong is None
    assert hv.verdict in ("afflicted", "mixed", "insufficient-evidence")


def test_mixed_when_benefic_and_malefic_both_fire():
    # House 7: Venus (7th lord) in 1st -> H7.L.1 (benefic); Saturn in 7th -> H7.P.Saturn (malefic).
    chart = _track_b({"Venus": 5.0, "Saturn": 185.0})
    hv = hj.judge_house(chart, 7)
    assert hv.benefic and hv.malefic           # both polarities fired
    assert hv.verdict == "mixed"


@needs_corpus
def test_evidence_is_cited():
    from app.raman_saab.doctrine.sources import verify
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    hv = hj.judge_house(chart, 7)
    for fr in hv.benefic + hv.malefic + hv.neutral:
        assert verify(fr.rule.source)          # every piece of evidence cites a real line
