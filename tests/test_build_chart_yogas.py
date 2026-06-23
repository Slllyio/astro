"""Tests for the chart_yogas builder over app.core.yogas.detect_yogas."""
from __future__ import annotations

import pandas as pd

from app.medini.etl.build_chart_yogas import build_chart_yogas

_GRAHAS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")


def _row(person_id: str, asc_sign: int, **signs: int) -> dict:
    base = {f"{g}_sign": 2 for g in _GRAHAS}  # default Taurus (neutral)
    base.update({f"{k}_sign": v for k, v in signs.items()})
    return {"person_id": person_id, "asc_sign": asc_sign, **base}


def test_detects_gajakesari_moon_jupiter_kendra() -> None:
    # Moon sign 1, Jupiter sign 4 -> 3 signs apart -> mutual kendra -> Gajakesari.
    df = pd.DataFrame([_row("p1", asc_sign=1, moon=1, jupiter=4)])
    out = build_chart_yogas(df)
    assert "Gajakesari" in set(out["yoga"])


def test_detects_ruchaka_mars_own_sign_in_kendra() -> None:
    # Lagna Aries(1); Mars in Aries(1) = own + house 1 (kendra) -> Ruchaka.
    df = pd.DataFrame([_row("p2", asc_sign=1, mars=1)])
    out = build_chart_yogas(df)
    assert "Ruchaka" in set(out["yoga"])


def test_no_spurious_yogas_for_neutral_chart() -> None:
    # All grahas in Taurus, Lagna Aries — no PMP dignity, no Moon/Jup kendra here.
    df = pd.DataFrame([_row("p3", asc_sign=1)])
    out = build_chart_yogas(df)
    assert "Ruchaka" not in set(out["yoga"])
    assert "Bhadra" not in set(out["yoga"])


def test_output_schema_and_multiperson() -> None:
    df = pd.DataFrame([
        _row("p1", asc_sign=1, moon=1, jupiter=4),
        _row("p3", asc_sign=1),
    ])
    out = build_chart_yogas(df)
    assert list(out.columns) == ["person_id", "yoga", "yoga_type", "planets"]
    assert set(out["person_id"]).issubset({"p1", "p3"})
