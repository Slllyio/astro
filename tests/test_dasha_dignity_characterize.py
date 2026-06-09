"""Tests for the dignity-anatomy characterization.

Pin the dignity-state annotation, the ladder/within-lord/side-decomp
maths on a constructed corpus with a known per-lord gradient.
"""
from __future__ import annotations

import pandas as pd

from app.medini.ml.dasha_dignity_characterize import (
    _safe_dignity,
    annotate,
    dignity_ladder,
    side_decomposition,
    within_lord_contrast,
)

LIBRA, ARIES, TAURUS, CANCER = 7, 1, 2, 4


def test_safe_dignity_states_and_nodes() -> None:
    assert _safe_dignity("Saturn", LIBRA) == "exalted"
    assert _safe_dignity("Saturn", ARIES) == "debilitated"
    assert _safe_dignity("Rahu", LIBRA) in {"unknown", "friendly", "neutral", "inimical"}
    assert _safe_dignity("Sun", None) == "unknown"


def _corpus():
    # Two people: p1 has exalted Saturn (Libra), p2 debilitated Saturn (Aries).
    charts = pd.DataFrame([
        {"person_id": "p1", "asc_sign": TAURUS, "saturn_sign": LIBRA},
        {"person_id": "p2", "asc_sign": CANCER, "saturn_sign": ARIES},
    ])
    rows = []
    # p1 (exalted Saturn): 18 beneficial, 2 adverse, all prime, Saturn MD.
    for i in range(20):
        rows.append({"person_id": "p1", "event_class": "x",
                     "event_subtype": "Beneficial" if i < 18 else "Adverse",
                     "md_lord_at_event": "Saturn", "ad_lord_at_event": "Saturn",
                     "age_at_event_years": 33.0})
    # p2 (debilitated Saturn): 6 beneficial, 14 adverse.
    for i in range(20):
        rows.append({"person_id": "p2", "event_class": "x",
                     "event_subtype": "Beneficial" if i < 6 else "Adverse",
                     "md_lord_at_event": "Saturn", "ad_lord_at_event": "Saturn",
                     "age_at_event_years": 33.0})
    return pd.DataFrame(rows), charts


def test_annotate_dignity_states() -> None:
    events, charts = _corpus()
    a = annotate(events, charts)
    assert set(a[a.person_id == "p1"]["md_dignity"]) == {"exalted"}
    assert set(a[a.person_id == "p2"]["md_dignity"]) == {"debilitated"}
    assert set(a["valence"]) == {1, -1}


def test_ladder_orders_and_lifts() -> None:
    events, charts = _corpus()
    a = annotate(events, charts)
    lad = dignity_ladder(a, stage="prime", min_support=5)
    ex = lad[lad.md_dignity == "exalted"].iloc[0]
    deb = lad[lad.md_dignity == "debilitated"].iloc[0]
    assert ex["benefit_share"] > deb["benefit_share"]
    assert ex["lift"] > 1.0 > deb["lift"]


def test_within_lord_contrast_positive_and_significant() -> None:
    events, charts = _corpus()
    a = annotate(events, charts)
    w = within_lord_contrast(a, stage="prime", min_support=5)
    sat = w[w.lord == "Saturn"].iloc[0]
    assert sat["benefit_well"] > sat["benefit_ill"]
    assert sat["contrast"] > 0.4
    assert sat["p"] < 0.05


def test_side_decomposition_keys() -> None:
    events, charts = _corpus()
    a = annotate(events, charts)
    s = side_decomposition(a, stage="prime", min_support=5)
    assert s["well_share"] > s["ill_share"]
    assert "strong_side_lift" in s and "weak_side_drag" in s
