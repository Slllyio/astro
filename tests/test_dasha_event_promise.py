"""Tests for native-chart promise extraction + promise/timing analysis."""
from __future__ import annotations

import pandas as pd

from app.medini.ml.dasha_event_promise import (
    _bucket,
    _dscore,
    _placement,
    _sign_in_house,
    bhava_promise,
    enrich_promise,
    promise_benefit_table,
    timing_within_class,
)

ARIES, TAURUS, CANCER, LEO, LIBRA, CAPRICORN = 1, 2, 4, 5, 7, 10


def test_sign_in_house_wholesign() -> None:
    # Aries lagna → house 1 = Aries, house 7 = Libra, house 10 = Capricorn.
    assert _sign_in_house(1, ARIES) == ARIES
    assert _sign_in_house(7, ARIES) == LIBRA
    assert _sign_in_house(10, ARIES) == CAPRICORN
    # Cancer lagna → house 7 = Capricorn.
    assert _sign_in_house(7, CANCER) == CAPRICORN


def test_placement_and_dscore() -> None:
    assert _placement(1) == 0.5 and _placement(10) == 0.5   # kendra/trikona
    assert _placement(8) == -0.5                            # dusthana
    assert _placement(3) == 0.0
    assert _dscore("Saturn", LIBRA) == 1.0                  # exalted
    assert _dscore("Saturn", ARIES) == -1.0                 # debilitated


def test_bucket_thresholds() -> None:
    assert _bucket(0.5) == "strong"
    assert _bucket(0.0) == "medium"
    assert _bucket(-0.5) == "weak"


def _chart() -> pd.Series:
    # Cancer lagna; 7th house (Capricorn) lord Saturn exalted in Libra (4th),
    # Venus (7th karaka) in own/strong → high 7th-house promise.
    return pd.Series({
        "person_id": "p1", "asc_sign": CANCER,
        "saturn_sign": LIBRA, "saturn_house": 4,
        "venus_sign": LIBRA, "venus_house": 4,
        "jupiter_sign": CANCER, "jupiter_house": 1,
        "moon_sign": CANCER, "moon_house": 1,
        "mars_sign": CAPRICORN, "mars_house": 7,
        "mercury_sign": LEO, "mercury_house": 2,
        "sun_sign": LEO, "sun_house": 2,
        "rahu_sign": ARIES, "rahu_house": 10,
        "ketu_sign": LIBRA, "ketu_house": 4,
    })


def test_bhava_promise_components() -> None:
    crow = _chart()
    houses = {p: int(crow[f"{p.lower()}_house"]) for p in
              ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
               "Rahu", "Ketu")}
    signs = {p: int(crow[f"{p.lower()}_sign"]) for p in houses}
    pr = bhava_promise(crow, 7, asc=CANCER, houses=houses, signs=signs)
    assert pr["house_lord"] == "Saturn"          # Capricorn lord
    assert pr["house_lord_dignity"] == "exalted"  # Saturn in Libra
    assert pr["karakas"] == "Venus"
    assert isinstance(pr["promise_score"], float)
    assert pr["promise_score"] > 0                # strong components → positive


def test_enrich_promise_timing_activation() -> None:
    events = pd.DataFrame([
        # marriage (7th) under Venus (7th karaka) → timing activates.
        {"person_id": "p1", "event_class": "marriage", "event_subtype": "Beneficial",
         "md_lord_at_event": "Venus", "ad_lord_at_event": "Venus",
         "age_at_event_years": 30.0},
        # career (10th) under Moon (not 10th lord/karaka) → not activated.
        {"person_id": "p1", "event_class": "career", "event_subtype": "Beneficial",
         "md_lord_at_event": "Moon", "ad_lord_at_event": "Moon",
         "age_at_event_years": 35.0},
    ])
    enr = enrich_promise(events, pd.DataFrame([_chart().to_dict()]))
    assert enr.loc[0, "domain_bhava"] == 7
    assert bool(enr.loc[0, "timing_activates_domain"]) is True
    assert enr.loc[1, "domain_bhava"] == 10
    assert bool(enr.loc[1, "timing_activates_domain"]) is False
    assert enr["valence"].tolist() == [1, 1]


def test_within_class_and_benefit_tables_run() -> None:
    rows = []
    for i in range(60):
        rows.append({"person_id": "p1", "event_class": "career",
                     "event_subtype": "Beneficial" if i % 4 else "Adverse",
                     "md_lord_at_event": "Saturn" if i % 2 else "Moon",
                     "ad_lord_at_event": "Venus", "age_at_event_years": 33.0})
    enr = enrich_promise(pd.DataFrame(rows), pd.DataFrame([_chart().to_dict()]))
    bt = promise_benefit_table(enr, stage="prime")
    assert bt.empty or {"promise", "benefit_share", "lift"} <= set(bt.columns)
    wc = timing_within_class(enr, stage="prime", min_support=5)
    assert wc.empty or {"event_class", "gap"} <= set(wc.columns)
