from __future__ import annotations

from app.raman_saab.chart import mean_longitudes as ml


def test_epoch_method_matches_ramans_stated_means():
    """Standard Horoscope I=6862.578 days, t=18. Reproduce GBB-6:99/104 means to ≤0.2°."""
    out = ml.mean_and_seeg_from_interval(6862.578, t=18)
    assert abs(out["mean"]["Sun"] - 181.2275) < 0.2
    assert abs(out["mean"]["Mars"] - 266.34) < 0.2
    assert abs(out["mean"]["Jupiter"] - 66.91) < 0.2
    assert abs(out["mean"]["Saturn"] - 111.23) < 0.2
    assert abs(out["seeg"]["Mercury"] - 174.49) < 0.2
    assert abs(out["seeg"]["Venus"] - 158.35) < 0.2
    # superior seegrochchas == Mean Sun
    assert out["seeg"]["Mars"] == out["mean"]["Sun"]


def test_interval_from_jd_for_standard_horoscope():
    """16 Oct 1918, 08:50 UT → interval ≈ 6862.578 days from the 76°E epoch."""
    import swisseph as swe
    # 16 Oct 1918, 13:54 Ujjain (76E) = 08:50 UT. Interval ~6862.578 days from epoch.
    jd = swe.julday(1918, 10, 16, 8 + 50 / 60.0, swe.GREG_CAL)
    I = ml.interval_days(jd)
    assert abs(I - 6862.578) < 0.6   # within ~half a day (tune if needed)
