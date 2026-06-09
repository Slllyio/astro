"""Tests for the robustness battery + split-half replication.

Pin the filter masks and the orchestration shape on a small synthetic
corpus; the statistical engine itself is tested in
test_dasha_dignity_permutation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.dasha_dignity_robustness import (
    _class_polarity,
    _mask_concordant,
    _mask_hard,
    _mask_one_per_person,
    battery,
    one_per_person_stability,
    split_half,
)

LIBRA, ARIES = 7, 1


def test_class_polarity() -> None:
    assert _class_polarity("death") == -1
    assert _class_polarity("marriage") == 1
    assert _class_polarity("other") == 0
    assert _class_polarity(None) == 0


def _events() -> pd.DataFrame:
    return pd.DataFrame([
        # p1: two events — death/Adverse (concordant, hard) + other/Beneficial (soft)
        {"person_id": "p1", "event_class": "death", "event_subtype": "Adverse",
         "event_jd": 10.0, "md_lord_at_event": "Saturn",
         "ad_lord_at_event": "Saturn", "age_at_event_years": 33.0},
        {"person_id": "p1", "event_class": "other", "event_subtype": "Beneficial",
         "event_jd": 20.0, "md_lord_at_event": "Jupiter",
         "ad_lord_at_event": "Jupiter", "age_at_event_years": 40.0},
        # p2: marriage/Adverse — DISCORDANT (class + vs subtype −)
        {"person_id": "p2", "event_class": "marriage", "event_subtype": "Adverse",
         "event_jd": 5.0, "md_lord_at_event": "Venus",
         "ad_lord_at_event": "Venus", "age_at_event_years": 30.0},
    ])


def test_mask_concordant_drops_discordant_and_soft() -> None:
    e = _events()
    m = _mask_concordant(e)
    assert m.tolist() == [True, False, False]  # only death/Adverse survives


def test_mask_hard_keeps_classed_events() -> None:
    e = _events()
    assert _mask_hard(e).tolist() == [True, False, True]  # death, marriage


def test_mask_one_per_person_picks_exactly_one() -> None:
    e = _events()
    m = _mask_one_per_person(e, seed=0)
    picked = e[m]
    assert picked.groupby("person_id").size().max() == 1
    assert set(picked["person_id"]) == {"p1", "p2"}


def _charts() -> pd.DataFrame:
    return pd.DataFrame([
        {"person_id": "p1", "asc_sign": LIBRA, "saturn_sign": LIBRA,
         "jupiter_sign": ARIES, "venus_sign": ARIES, "sun_sign": ARIES,
         "moon_sign": ARIES, "mars_sign": ARIES, "mercury_sign": ARIES,
         "rahu_sign": ARIES, "ketu_sign": LIBRA},
        {"person_id": "p2", "asc_sign": ARIES, "saturn_sign": ARIES,
         "jupiter_sign": LIBRA, "venus_sign": LIBRA, "sun_sign": LIBRA,
         "moon_sign": LIBRA, "mars_sign": LIBRA, "mercury_sign": LIBRA,
         "rahu_sign": LIBRA, "ketu_sign": ARIES},
    ])


def test_battery_returns_all_rows() -> None:
    bat = battery(_events(), _charts(), k=5, seed=0)
    assert list(bat["filter"]) == [
        "none (baseline)", "one_per_person", "concordant", "hard_only",
        "strict (all 3)"]
    assert {"n_events", "real", "z", "p"} <= set(bat.columns)


def test_stability_and_split_half_shapes() -> None:
    stab = one_per_person_stability(_events(), _charts(), k=5, seeds=(0, 1))
    assert len(stab) == 2 and "z" in stab.columns
    split = split_half(_events(), _charts(), k=5, seeds=(0,))
    assert set(split["half"]) <= {"A", "B"}
    assert (split["n_people"] >= 1).all()
