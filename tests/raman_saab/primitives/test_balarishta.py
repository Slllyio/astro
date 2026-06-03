from __future__ import annotations

import dataclasses

from app.raman_saab.primitives.balarishta import balarishta
from app.raman_saab.primitives.shadbala import total as shadbala_total
from app.raman_saab.chart.model import RamanChart, ShadbalaBreakdown


def _c(lons: dict, asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon,
        ayanamsa="raman",
    )


def _with_shadbala(chart: RamanChart, planet: str, total_rupas: float) -> RamanChart:
    """Attach a synthetic ShadbalaBreakdown of `total_rupas` Rupas to one planet."""
    br = ShadbalaBreakdown(
        sthana=0.0, dig=0.0, kala=0.0, cheshta=0.0, naisargika=0.0,
        drik=0.0, total=total_rupas * 60.0,
    )
    p = dataclasses.replace(chart.planets[planet], shadbala_rupas=br)
    planets = {**chart.planets, planet: p}
    return dataclasses.replace(chart, planets=planets)


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


# ── Phase 1c-3 backfill: real-Shadbala strong-lagna-lord antidote ────────────────

def _afflicted_aries_chart() -> RamanChart:
    """Aries lagna (lord Mars), Moon in 8th (Scorpio) with Saturn -> balarishta applies.

    Mars (the lagna lord) sits in the 3rd house (Gemini), which is NEITHER kendra/trikona
    NOR a strong dignity for Mars (neutral in Gemini) -> the v1 proxy does NOT fire the
    strong-lagna-lord antidote, isolating the real-Shadbala branch.
    """
    return _c({"Moon": 220.0, "Saturn": 225.0, "Mars": 65.0}, asc_lon=0.0)


def test_strong_lagna_lord_antidote_fires_via_real_shadbala():
    """A powerfully-situated lagna lord (total Shadbala >= MIN_REQUIRED) cancels balarishta."""
    c = _afflicted_aries_chart()
    # Proxy must NOT fire on its own (control): Mars in 3rd, neutral dignity.
    assert "strong_lagna_lord" not in balarishta(c).reasons
    # Now attach a strong Shadbala (Mars MIN_REQUIRED = 5.0 Rupas) -> real branch fires.
    strong = _with_shadbala(c, "Mars", total_rupas=shadbala_total.MIN_REQUIRED["Mars"] + 0.5)
    st = balarishta(strong)
    assert st.applies is True
    assert "strong_lagna_lord" in st.reasons


def test_weak_lagna_lord_shadbala_does_not_fire_antidote():
    """A lagna lord below MIN_REQUIRED does NOT trigger the strong-lagna-lord antidote."""
    c = _afflicted_aries_chart()
    weak = _with_shadbala(c, "Mars", total_rupas=shadbala_total.MIN_REQUIRED["Mars"] - 1.0)
    assert "strong_lagna_lord" not in balarishta(weak).reasons


def test_track_b_proxy_still_works_without_shadbala():
    """Track-B fallback: lagna lord in a kendra/trikona (no Shadbala) still cancels."""
    # Aries lagna; Mars (lord) in the 1st (kendra+trikona) -> proxy fires.
    c = _c({"Moon": 220.0, "Saturn": 225.0, "Mars": 5.0}, asc_lon=0.0)
    st = balarishta(c)
    assert st.applies is True
    assert "strong_lagna_lord" in st.reasons
