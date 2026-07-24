"""B1 effective-strength fold (`house_template._effective_strength`).

The fold MUST be a strict no-op at the shipped all-zero affliction weights (so the golden ratchet is
untouched), and must apply exactly the documented penalties/bonus when a weight is set (the tuner's
search space). See NH_GAP_ANALYSIS 2026-07-24 — the weights ship at 0.0; only the holdout-locked tuner
raises them.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges import house_template as ht
from app.raman_saab.primitives.shadbala import total as shadbala_total


def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def test_noop_at_shipped_default_weights():
    """All EFF_W_* default to 0.0 -> the fold returns the raw Rupas unchanged (strict no-op)."""
    assert shadbala_total.EFF_W_PAPAKARTARI == 0.0
    assert shadbala_total.EFF_W_DIGNITY == 0.0
    chart = _chart({"Mars": 225.0})              # Mars in the 8th (a dusthana), Aries lagna
    assert ht._effective_strength("Mars", 6.0, chart) == 6.0


def test_dusthana_penalty(monkeypatch):
    """A dusthana (6/8/12) placement subtracts EFF_W_DUSTHANA."""
    monkeypatch.setattr(shadbala_total, "EFF_W_DUSTHANA", 2.0)
    chart = _chart({"Mars": 225.0})              # Mars in Scorpio = the 8th
    assert ht._effective_strength("Mars", 6.0, chart) == 4.0
    # A non-dusthana placement is untouched.
    assert ht._effective_strength("Mars", 6.0, _chart({"Mars": 5.0})) == 6.0   # Mars in the 1st


def test_dignity_bonus(monkeypatch):
    """An exalted/own/moolatrikona planet adds EFF_W_DIGNITY."""
    monkeypatch.setattr(shadbala_total, "EFF_W_DIGNITY", 1.5)
    chart = _chart({"Sun": 10.0})                # Sun exalted in Aries
    assert ht._effective_strength("Sun", 5.0, chart) == 6.5


def test_papakartari_penalty(monkeypatch):
    """A planet hemmed by malefics (papakartari) subtracts EFF_W_PAPAKARTARI."""
    monkeypatch.setattr(shadbala_total, "EFF_W_PAPAKARTARI", 2.0)
    # Aries lagna: Venus in the 4th (Cancer, h4); malefics in its 2nd (h5) and 12th (h3) hem it.
    chart = _chart({"Venus": 95.0, "Saturn": 135.0, "Mars": 65.0})
    assert ht._effective_strength("Venus", 6.0, chart) == 4.0
