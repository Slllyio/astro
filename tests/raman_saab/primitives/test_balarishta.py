from __future__ import annotations

from app.raman_saab.primitives.balarishta import balarishta
from app.raman_saab.chart.model import RamanChart


def _c(lons: dict, asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon,
        ayanamsa="raman",
    )


def test_moon_in_7_8_12_with_malefic_triggers_balarishta():
    """Moon in 8th (Scorpio 220°) conjoined Saturn, no benefic with it -> applies, not cancelled.

    Raman HPA-14:96-98: Moon in the 7th/8th/12th with malefics (and no benefic aspect).
    """
    c = _c({"Moon": 220.0, "Saturn": 225.0}, asc_lon=0.0)
    st = balarishta(c)
    assert st.applies is True
    assert any("moon_7_8_12_malefic" in r for r in st.reasons)


def test_jupiter_in_lagna_cancels():
    """Jupiter in the ascendant removes Balarishta (HPA-14:232).

    Same affliction as above but Jupiter added to the 1st house -> cancelled=True.
    """
    c = _c({"Moon": 220.0, "Saturn": 225.0, "Jupiter": 5.0}, asc_lon=0.0)
    st = balarishta(c)
    assert st.applies is True and st.cancelled is True
    assert any("jupiter_in_lagna" in r for r in st.reasons)


def test_clean_chart_no_balarishta():
    """Moon in 4th with Jupiter conjunct — no malefic with Moon -> applies=False."""
    c = _c({"Moon": 100.0, "Jupiter": 100.0}, asc_lon=0.0)
    assert balarishta(c).applies is False
