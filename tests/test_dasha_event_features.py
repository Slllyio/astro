"""Tests for native-kundli event-feature enrichment + deep-dive maths."""
from __future__ import annotations

import pandas as pd

from app.medini.ml.dasha_event_features import (
    _chart_features,
    _functional,
    _house_kind,
    _lord_features,
    _natural,
    _safe_dignity,
    enrich_events,
    feature_benefit_table,
)

LIBRA, ARIES, CANCER, LEO = 7, 1, 4, 5


def test_natural_nature() -> None:
    assert _natural("Jupiter") == "benefic"
    assert _natural("Moon") == "benefic"
    assert _natural("Saturn") == "malefic"
    assert _natural("Rahu") == "malefic"


def test_house_kind_categories() -> None:
    assert _house_kind(1) == "lagna"
    assert _house_kind(8) == "dusthana"
    assert _house_kind(5) == "trikona"
    assert _house_kind(10) == "kendra"
    assert _house_kind(11) == "upachaya"
    assert _house_kind(2) == "maraka"
    assert _house_kind(None) == "unknown"


def test_safe_dignity_handles_nodes() -> None:
    assert _safe_dignity("Saturn", LIBRA) == "exalted"
    assert _safe_dignity("Rahu", LIBRA) == "unknown" or isinstance(
        _safe_dignity("Rahu", LIBRA), str)
    assert _safe_dignity("Sun", None) == "unknown"


def test_functional_mars_yogakaraka_for_leo() -> None:
    # Mars rules 4 (Scorpio) & 9 (Aries) from Leo lagna → functional benefic/YK.
    assert _functional("Mars", LEO) == "benefic"
    assert _functional("Mars", None) == "unknown"


def _chart_row() -> pd.Series:
    d = {"person_id": "p1", "asc_sign": LEO, "saturn_sign": LIBRA,
         "saturn_house": 3, "jupiter_sign": ARIES, "jupiter_house": 1,
         "venus_sign": ARIES, "venus_house": 9, "sun_sign": LEO, "sun_house": 1,
         "moon_sign": CANCER, "moon_house": 12, "mars_sign": ARIES,
         "mars_house": 9, "mercury_sign": LEO, "mercury_house": 1,
         "rahu_sign": ARIES, "ketu_sign": LIBRA, "rahu_house": 9, "ketu_house": 3}
    return pd.Series(d)


def test_lord_features_keys_and_values() -> None:
    f = _lord_features(_chart_row(), "Jupiter", "md")
    assert f["md_natural"] == "benefic"
    assert f["md_house"] == 1
    assert f["md_house_kind"] == "lagna"
    assert f["md_is_kendra"] is True and f["md_is_trikona"] is True
    # Jupiter in Aries (Mars-ruled, a friend) → "friendly".
    assert f["md_dignity"] == "friendly"


def test_chart_features_counts() -> None:
    c = _chart_features(_chart_row())
    assert c["chart_lagna_lord"] == "Sun"
    assert c["chart_benefics_in_kendra"] >= 1  # Jupiter/Mercury in 1
    assert "chart_kendra_net" in c and "chart_n_yogakaraka" in c


def test_enrich_and_benefit_table() -> None:
    events = pd.DataFrame([
        {"person_id": "p1", "event_class": "career", "event_subtype": "Beneficial",
         "md_lord_at_event": "Jupiter", "ad_lord_at_event": "Venus",
         "age_at_event_years": 33.0},
        {"person_id": "p1", "event_class": "health", "event_subtype": "Adverse",
         "md_lord_at_event": "Saturn", "ad_lord_at_event": "Saturn",
         "age_at_event_years": 34.0},
    ])
    charts = pd.DataFrame([_chart_row().to_dict()])
    enr = enrich_events(events, charts)
    assert "md_natural" in enr.columns and "pair_naisargika" in enr.columns
    assert enr["valence"].tolist() == [1, -1]
    tab = feature_benefit_table(enr, "md_natural", stage="prime", min_support=1)
    assert not tab.empty and {"benefit_share", "lift", "p_vs_base"} <= set(tab.columns)
