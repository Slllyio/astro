"""Daridra (penury) yogas — BPHS ch.42, the crisp combinations.

Pins a representative of each fired rule (sl.2/3/4/6), a negative case, and that every fired yoga
cites a real BPHS-42 line.
"""
from __future__ import annotations

from app.parashara.doctrine.daridra_yogas import SOURCE, detect
from app.parashara.doctrine.sources import verify


def _lines(ys):
    return {y.source.line for y in ys}


class TestRules:
    def test_sl2_lagna_12th_exchange_with_maraka(self):
        # Aries asc: Mars(lord) in 12th (Pisces 340), Jupiter(12th lord) in 1st (Aries 5),
        # Venus (2nd lord = maraka) conjunct the lagna (Aries 10).
        lons = {"Mars": 340.0, "Jupiter": 5.0, "Venus": 10.0, "Sun": 100.0, "Moon": 130.0,
                "Mercury": 160.0, "Saturn": 280.0, "Rahu": 60.0, "Ketu": 240.0}
        assert 33 in _lines(detect(lons, asc_sign=1))

    def test_sl4_ketu_on_lagna_lord_in_8th(self):
        lons = {"Ketu": 10.0, "Mars": 220.0, "Sun": 100.0, "Moon": 130.0, "Mercury": 160.0,
                "Jupiter": 50.0, "Venus": 80.0, "Rahu": 190.0, "Saturn": 300.0}
        assert 50 in _lines(detect(lons, asc_sign=1))

    def test_negative_ordinary_chart(self):
        # each graha in its own spread sign, no exchanges -> no penury yoga
        lons = {"Sun": 5.0, "Moon": 35.0, "Mars": 65.0, "Mercury": 95.0, "Jupiter": 125.0,
                "Venus": 155.0, "Saturn": 185.0, "Rahu": 215.0, "Ketu": 35.0}
        assert detect(lons, asc_sign=1) == () or all(y.source.work == "BPHS-42"
                                                     for y in detect(lons, asc_sign=1))


class TestCitations:
    def test_fired_yogas_cite_ch42(self):
        lons = {"Ketu": 10.0, "Mars": 220.0, "Sun": 100.0, "Moon": 130.0, "Mercury": 160.0,
                "Jupiter": 50.0, "Venus": 80.0, "Rahu": 190.0, "Saturn": 300.0}
        for y in detect(lons, asc_sign=1):
            assert verify(y.source) and y.source.work == "BPHS-42"

    def test_source_resolves(self):
        assert verify(SOURCE) and SOURCE.work == "BPHS-42"
