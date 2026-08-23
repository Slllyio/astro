"""Gochara — transit by Ashtakavarga (BPHS-70). Transit quality from the planet's BAV count.

Pins the rule direction (more benefic points -> favourable), the thresholds around the 0..8 midpoint,
full-graha coverage, and an end-to-end run on a real transit date. Citation resolves.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.chart.ephemeris import transit_signs
from app.parashara.doctrine import gochara
from app.parashara.doctrine.sources import verify
from app.parashara.primitives import ashtakavarga as av


def _canonical_signs():
    ch = cast(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5, latitude=12.97,
              longitude=77.59)
    return {g: int(ch.longitudes[g] % 360.0 // 30) + 1 for g in av.PLANETS}, ch.asc_sign


class TestTransitQuality:
    def test_high_bindus_favourable_low_unfavourable(self):
        signs, asc = _canonical_signs()
        jbav = av.bhinnashtakavarga("Jupiter", signs, asc_sign=asc)
        hi = max(jbav, key=jbav.get)
        lo = min(jbav, key=jbav.get)
        assert gochara.transit_quality("Jupiter", hi, signs, asc_sign=asc).quality == "favourable"
        assert gochara.transit_quality("Jupiter", lo, signs, asc_sign=asc).quality == "unfavourable"

    def test_quality_thresholds(self):
        # direct on the private helper via a crafted sign is simplest through the public path:
        signs, asc = _canonical_signs()
        for planet in av.PLANETS:
            bav = av.bhinnashtakavarga(planet, signs, asc_sign=asc)
            for sign, b in bav.items():
                q = gochara.transit_quality(planet, sign, signs, asc_sign=asc).quality
                assert q == ("favourable" if b >= 5 else "unfavourable" if b <= 3 else "mixed")

    def test_out_of_range_raises(self):
        signs, asc = _canonical_signs()
        with pytest.raises(ValueError):
            gochara.transit_quality("Sun", 13, signs, asc_sign=asc)


class TestAllTransits:
    def test_covers_seven_grahas_on_a_real_date(self):
        signs, asc = _canonical_signs()
        ts = transit_signs(year=2026, month=8, day=23)
        out = gochara.all_transits(signs, ts, asc_sign=asc)
        assert set(out) == set(av.PLANETS)
        for j in out.values():
            assert 0 <= j.bindus <= 8 and j.quality in ("favourable", "mixed", "unfavourable")


class TestEphemerisTransit:
    def test_transit_signs_are_valid(self):
        ts = transit_signs(year=2026, month=8, day=23)
        assert all(1 <= s <= 12 for s in ts.values())
        assert ts["Ketu"] == ((ts["Rahu"] - 1 + 6) % 12) + 1     # Ketu opposite Rahu


class TestCitation:
    def test_source_resolves(self):
        assert verify(gochara.SOURCE)
