"""Phase-2 aspect backfills: the conjunction-only Phase-1 deferrals now use the
drishti engine. Each test isolates the ASPECT path (no conjunction / kendra route)."""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import balarishta, bhangas, maraka


def _c(lons: dict[str, float]) -> RamanChart:  # Aries lagna (asc 0)
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=0.0, ayanamsa="raman")


def test_neecha_bhanga_via_dispositor_aspect():
    # Saturn debilitated in Aries; dispositor Mars in the 6th (Virgo) casts its 8th aspect
    # on Saturn (house 1). Mars is NOT in a kendra and NOT conjunct -> only the aspect path.
    c = _c({"Saturn": 25.0, "Mars": 155.0})
    assert bhangas.neecha_bhanga("Saturn", c) is True
    # Mars in the 3rd (Gemini): neither aspects Saturn nor sits in a kendra -> no cancellation.
    c2 = _c({"Saturn": 25.0, "Mars": 65.0})
    assert bhangas.neecha_bhanga("Saturn", c2) is False


def test_maraka_aspect_associate():
    # Aries lagna: 2nd & 7th lord = Venus (in the 1st). Saturn in the 11th (Aquarius) casts
    # its 3rd aspect on Venus -> Saturn is a primary maraka by aspect (not by lordship/conjunction).
    c = _c({"Venus": 5.0, "Saturn": 305.0})
    primary = {u.graha for u in maraka.maraka_points(c).units if u.tier == "primary"}
    assert "Saturn" in primary


def test_balarishta_benefic_aspect_protects_moon():
    # Moon in 8th with Saturn = affliction -> yoga fires.
    assert balarishta.balarishta(_c({"Moon": 220.0, "Saturn": 225.0})).applies is True
    # Add Jupiter in the 4th (Cancer): it aspects the Moon (5th aspect) -> yoga 3 protected.
    st = balarishta.balarishta(_c({"Moon": 220.0, "Saturn": 225.0, "Jupiter": 100.0}))
    assert not any("moon_7_8_12" in r for r in st.reasons)
