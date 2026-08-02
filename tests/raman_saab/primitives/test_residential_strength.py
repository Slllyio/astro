"""Residential strength (Bhavavastha) — `primitives/residential_strength.py`.

Pins Raman's GBB-1 §§12-17 method. The critical property is the DIRECTION of the arc: it is
measured from the bounding Bhava Sandhi, not from the Madhya, so strength is 0 at a sandhi
("utterly powerless", GBB-1:38-42) and 1 at the madhya. An inverted implementation passes a
midpoint-only test, so both halves and both endpoints are pinned separately.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart import cusps
from app.raman_saab.primitives.residential_strength import (
    residential_strength,
    residential_strengths,
)

#: Equal 30-degree bhavas with madhyas at 15, 45, 75 ... — sandhis land on 0, 30, 60 ...
_MADHYAS = tuple(15.0 + 30.0 * i for i in range(12))
_SANDHIS = cusps.sandhis_from_madhyas(_MADHYAS)


class TestGeometry:
    def test_madhya_gives_full_strength(self):
        """At the Bhava Madhya the planet delivers the whole of the Bhava's effect."""
        bhava, s = residential_strength(15.0, _MADHYAS, _SANDHIS)
        assert bhava == 1
        assert s == pytest.approx(1.0, abs=1e-9)

    def test_arambha_sandhi_gives_zero(self):
        """GBB-1:38-42 — a planet in a Bhava Sandhi is 'utterly powerless'."""
        _bhava, s = residential_strength(30.0, _MADHYAS, _SANDHIS)
        assert s == pytest.approx(0.0, abs=1e-9)

    def test_virama_sandhi_gives_zero(self):
        """Approached from inside the bhava, the closing sandhi is equally powerless."""
        _bhava, s = residential_strength(29.999999, _MADHYAS, _SANDHIS)
        assert s == pytest.approx(0.0, abs=1e-5)

    def test_poorvabhaga_measures_from_the_arambha_sandhi(self):
        """First half: arc = planet - arambha, over the poorvabhaga. Quarter in => 0.5."""
        _bhava, s = residential_strength(7.5, _MADHYAS, _SANDHIS)     # 7.5 of 15 deg
        assert s == pytest.approx(0.5, abs=1e-9)

    def test_uttarabhaga_measures_back_from_the_virama_sandhi(self):
        """Second half: arc = virama - planet. The MIRROR of the poorvabhaga case — an
        implementation that measures from the madhya in both halves fails exactly here."""
        _bhava, s = residential_strength(22.5, _MADHYAS, _SANDHIS)    # 7.5 short of 30 deg
        assert s == pytest.approx(0.5, abs=1e-9)

    def test_strength_is_symmetric_about_the_madhya(self):
        for d in (1.0, 3.75, 7.5, 11.25, 14.0):
            _b1, lo = residential_strength(15.0 - d, _MADHYAS, _SANDHIS)
            _b2, hi = residential_strength(15.0 + d, _MADHYAS, _SANDHIS)
            assert lo == pytest.approx(hi, abs=1e-9), f"asymmetric at {d} deg from madhya"

    def test_wraps_across_zero_aries(self):
        """The 12th bhava straddles 360/0. Circular arithmetic, not naive subtraction —
        the same 359/2-degree cusp trap CLAUDE.md locks for orb distance."""
        madhyas = tuple((345.0 + 30.0 * i) % 360.0 for i in range(12))
        sandhis = cusps.sandhis_from_madhyas(madhyas)
        bhava, s = residential_strength(345.0, madhyas, sandhis)
        assert bhava == 1 and s == pytest.approx(1.0, abs=1e-9)
        _b, edge = residential_strength(0.0, madhyas, sandhis)         # the 345+15 sandhi
        assert edge == pytest.approx(0.0, abs=1e-9)

    def test_every_bhava_scores_full_at_its_own_madhya(self):
        for i, m in enumerate(_MADHYAS):
            bhava, s = residential_strength(m, _MADHYAS, _SANDHIS)
            assert bhava == i + 1
            assert s == pytest.approx(1.0, abs=1e-9)


class TestContract:
    def test_strength_is_always_a_unit_fraction(self):
        for lon in range(0, 360):
            _b, s = residential_strength(float(lon), _MADHYAS, _SANDHIS)
            assert 0.0 <= s <= 1.0, f"{lon} deg scored {s}"

    def test_malformed_cusps_raise_rather_than_score(self):
        """A broken cusp set must fail loudly, not quietly score against a bad chart."""
        with pytest.raises(ValueError, match="12 madhyas"):
            residential_strength(10.0, _MADHYAS[:5], _SANDHIS)

    def test_nodes_are_scored_too(self):
        """Unlike Shadbala (7 visible grahas, GBB-3), Raman's own residential-strength table
        lists Rahu and Kethu — this is a positional quantity, so the nodes qualify."""
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.chart.model import BirthData

        chart = cast_chart(BirthData("t", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59),
                           ayanamsa="raman")
        out = residential_strengths(chart)
        assert {"Rahu", "Ketu"} <= set(out)
        assert all(0.0 <= s <= 1.0 for _b, s in out.values())
        assert all(1 <= b <= 12 for b, _s in out.values())
