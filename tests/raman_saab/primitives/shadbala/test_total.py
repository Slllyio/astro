from __future__ import annotations

from app.raman_saab.primitives.shadbala import total
from app.raman_saab.chart.model import ShadbalaBreakdown

# GBB Standard Horoscope component values (Shashtiamsas): (sthana,dig,kala,cheshta,naisargika,drik)
_COMP = {
    "Sun":     (147.975, 48.070, 104.490,  0.000, 60.000,  16.720),
    "Moon":    (141.650, 32.250, 202.750,  0.000, 51.430, -11.900),
    "Mars":    (194.700, 55.030,  28.390, 22.280, 17.140,   5.350),
    "Mercury": (294.800, 21.860, 219.920,  2.130, 25.700,  16.050),
    "Jupiter": (157.450, 10.450, 211.930, 35.330, 34.280,  -6.570),
    "Venus":   (157.925, 14.950, 116.810,  5.760, 42.850,  18.670),
    "Saturn":  (162.400, 56.700, 115.690, 21.060,  8.570,   7.370),
}
_EXPECTED_RUPAS = {
    "Sun": 6.288, "Moon": 6.936, "Mars": 5.381, "Mercury": 9.674,
    "Jupiter": 7.381, "Venus": 5.949, "Saturn": 6.196,
}


def test_assembly_reproduces_total_rupas():
    """assemble_shadbala sums all 6 components into ShadbalaBreakdown.total (Shashtiamsas);
    dividing by 60 reproduces GBB Standard Horoscope Total-Rupas for all 7 planets
    (Mercury 9.674 — OCR-corrected from printed 9.743)."""
    for p, c in _COMP.items():
        br = total.assemble_shadbala(*c)
        assert isinstance(br, ShadbalaBreakdown)
        assert abs(br.total / 60.0 - _EXPECTED_RUPAS[p]) < 0.01, f"{p}: {br.total / 60.0}"


def test_drik_is_signed_in_the_sum():
    """Moon's negative Drik (−11.9) must subtract; total = 416.180 Sh."""
    br = total.assemble_shadbala(*_COMP["Moon"])
    assert abs(br.total - 416.180) < 0.1


def test_min_required_thresholds_and_all_powerful():
    """MIN_REQUIRED matches GBB-8:303-312; all 7 Standard Horoscope planets are powerful;
    Saturn at 4.9 Rupas (below threshold of 5.0) is not powerful."""
    assert total.MIN_REQUIRED == {
        "Sun": 5.0, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
        "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0,
    }
    for p, r in _EXPECTED_RUPAS.items():
        assert total.is_powerful(p, r) is True          # fixture: all 7 powerful
    assert total.is_powerful("Saturn", 4.9) is False
