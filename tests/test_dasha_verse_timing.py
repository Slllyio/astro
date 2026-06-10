"""Tests for verse-level dictum timing — predicates + the within-person statistic."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.dasha_verse_timing import (
    _house_from, _person_facts, cond_7L, cond_pos_benefic, cond_pos_malefic,
    within_person_lift,
)


def test_house_from_wraps() -> None:
    assert _house_from(7, 7) == 1          # planet on the dasha lord
    assert _house_from(1, 7) == 7          # 7th from
    assert _house_from(6, 8) == 11         # wrap-around


def _crow(**houses):
    base = {"person_id": "p", "birth_jd_used": 2451545.0, "asc_sign": 1}
    # default everyone in sign 1 / house 1 unless overridden
    for g in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
              "rahu", "ketu"):
        base[f"{g}_sign"] = houses.pop(f"{g}_sign", 1)
        base[f"{g}_house"] = houses.pop(f"{g}_house", 1)
    base.update(houses)
    return pd.Series(base)


def test_positional_predicates() -> None:
    # asc=1 (Aries) → 7th house sign = Libra(7), lord = Venus.
    # put Mercury(MD) in house 1, Venus(AD) in house 5 → 5th from MD = benefic.
    f = _person_facts(_crow(mercury_house=1, venus_house=5), None)
    assert cond_pos_benefic("Mercury", "Venus", f)
    assert not cond_pos_malefic("Mercury", "Venus", f)
    # Venus in house 8 from Mercury(h1) → 8th = malefic.
    f2 = _person_facts(_crow(mercury_house=1, venus_house=8), None)
    assert cond_pos_malefic("Mercury", "Venus", f2)


def test_7L_identity() -> None:
    f = _person_facts(_crow(), None)              # asc Aries → 7L = Venus
    assert cond_7L("Venus", "Sun", f)
    assert cond_7L("Sun", "Venus", f)
    assert not cond_7L("Sun", "Moon", f)


def _planted_dataset(signal: bool, n=150, seed=0):
    """Each native: 8 windows; if signal, the marriage sits where AD is benefic
    from MD. Uses houses so the predicate fires deterministically."""
    rng = np.random.default_rng(seed)
    charts, windows, events = [], [], []
    # asc Aries; place planets so we can drive AD-from-MD position via md/ad lords.
    for i in range(n):
        pid = f"p{i}"
        charts.append({"person_id": pid, "birth_jd_used": 2451545.0, "asc_sign": 1,
                       **{f"{g}_sign": 1 for g in ("sun", "moon", "mars", "mercury",
                          "jupiter", "venus", "saturn", "rahu", "ketu")},
                       # houses: Mercury h1, Venus h5 (benefic from Merc), Saturn h8.
                       **{f"{g}_house": h for g, h in
                          [("sun", 1), ("moon", 1), ("mars", 1), ("mercury", 1),
                           ("jupiter", 1), ("venus", 5), ("saturn", 8), ("rahu", 1),
                           ("ketu", 1)]}})
        # 8 windows; one "benefic" window Merc→Venus, others Merc→Saturn (malefic).
        seqs = []
        for j in range(8):
            ad = "Venus" if j == 3 else "Saturn"
            md = "Mercury"
            start = 2451545.0 + j * 1000
            windows.append({"person_id": pid, "md_lord": md, "ad_lord": ad,
                            "md_seq": 0, "ad_seq": j, "start_jd": start,
                            "end_jd": start + 1000, "duration_days": 1000.0})
            seqs.append(j)
        ev_j = 3 if signal else int(rng.integers(0, 8))
        # age ~ between window mid and birth; band marriage (16,55): keep mid-age in band
        windows[-8 + ev_j]  # noop
        events.append({"person_id": pid, "event_class": "marriage",
                       "event_jd": 2451545.0 + ev_j * 1000 + 500,
                       "md_seq": 0, "ad_seq": ev_j})
    # shift birth so window mid-ages land in the marriage band (~age 20-40).
    for c in charts:
        c["birth_jd_used"] = 2451545.0 - 30 * 365.25
    return (pd.DataFrame(charts), pd.DataFrame(windows), pd.DataFrame(events))


def test_within_person_lift_detects_planted_signal() -> None:
    charts, windows, events = _planted_dataset(signal=True)
    res = within_person_lift(windows, charts, None, events, "marriage")
    c = res["conditions"]["AD_benefic_from_MD"]
    assert c["lift"] > 2.0 and c["p"] < 1e-6 and c["z"] > 4


def test_within_person_lift_null_is_flat() -> None:
    charts, windows, events = _planted_dataset(signal=False, seed=7)
    res = within_person_lift(windows, charts, None, events, "marriage")
    c = res["conditions"]["AD_benefic_from_MD"]
    assert 0.5 < c["lift"] < 2.0 and c["p"] > 0.05
