"""Royal-association yogas — BPHS ch.40, the crisp chara-karaka combinations.

Pins the Amatyakaraka house rule (sl.5), the kendra/trikona rule (sl.6), and citation resolution on
a real cast chart (which yields AK=Sun, AmK=Jupiter).
"""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.doctrine.royal_association import SOURCE, detect
from app.parashara.doctrine.sources import verify


def _chart():
    return cast(year=1990, month=7, day=15, hour=12, minute=0,
                tz_offset=5.5, latitude=12.97, longitude=77.59)


def test_fires_on_canonical_and_cites_ch40():
    ch = _chart()
    ys = detect(ch.longitudes, asc_sign=ch.asc_sign)
    assert ys, "expected at least one royal-association yoga on the canonical chart"
    for y in ys:
        assert verify(y.source) and y.source.work == "BPHS-40"


def test_amatyakaraka_in_5th_or_9th_rule():
    # Distinct degrees so AmK is unambiguously Jupiter (2nd-highest degree-in-sign) placed in the
    # 9th from Aries (Sagittarius): Sun 28 (AK), Jupiter 25 (AmK).
    lons = {"Sun": 28.0, "Jupiter": 265.0, "Moon": 50.0, "Mars": 100.0, "Mercury": 135.0,
            "Venus": 168.0, "Saturn": 305.0}
    ys = detect(lons, asc_sign=1)
    assert any("1st/5th/9th" in y.name for y in ys)


def test_no_karakas_no_yoga():
    # only nodes present -> chara_karakas empty of AK/AmK -> no yoga, no crash
    assert detect({"Rahu": 10.0, "Ketu": 190.0}, asc_sign=1) == ()


def test_source_resolves():
    assert verify(SOURCE) and SOURCE.work == "BPHS-40"
