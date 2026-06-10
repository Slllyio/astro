"""Tests for the classical-dictum (astrologer's-way) hit-rate engine."""
from __future__ import annotations

import pandas as pd

from app.medini.ml.dasha_classical_dictums import (
    DICTUMS, _person_exposure, _significator_set, classical_hitrate,
    mangal_dosha, marriage_delay,
)

ARIES, TAURUS, LIBRA, AQUARIUS = 1, 2, 7, 11


def _chart(pid="p1", asc=ARIES, mars_house=7):
    d = {"person_id": pid, "asc_sign": asc}
    houses = {"sun": 1, "moon": 2, "mars": mars_house, "mercury": 3,
              "jupiter": 5, "venus": 7, "saturn": 10, "rahu": 9, "ketu": 3}
    for g, h in houses.items():
        d[f"{g}_house"] = h
        d[f"{g}_sign"] = ((asc - 1 + h - 1) % 12) + 1
    return d


def test_significator_set_marriage_aries() -> None:
    crow = pd.Series(_chart())
    S = _significator_set(crow, None, DICTUMS["marriage"])
    # Aries asc: 7th=Libra→Venus, 2nd=Taurus→Venus, 11th=Aquarius→Saturn; karaka Venus.
    assert "Venus" in S and "Saturn" in S
    # Venus occupies the 7th here too → still in set; all members are real grahas.
    assert S <= {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                 "Rahu", "Ketu"}


def test_person_exposure_union_md_ad() -> None:
    win = pd.DataFrame([
        {"md_lord": "Venus", "ad_lord": "Sun", "duration_days": 40.0},   # md hit
        {"md_lord": "Sun", "ad_lord": "Venus", "duration_days": 30.0},   # ad hit
        {"md_lord": "Sun", "ad_lord": "Moon", "duration_days": 30.0},    # miss
    ])
    assert _person_exposure(win, {"Venus"}) == 70.0 / 100.0


def _corpus():
    charts = pd.DataFrame([_chart("p1", ARIES, 7), _chart("p2", TAURUS, 3)])
    rows, wins = [], []
    for pid in ("p1", "p2"):
        for i in range(60):
            rows.append({"person_id": pid, "event_class": "marriage",
                         "md_lord_at_event": "Venus" if i % 2 else "Sun",
                         "ad_lord_at_event": "Mars", "age_at_event_years": 28.0 + i % 10})
        for i in range(50):
            rows.append({"person_id": pid, "event_class": "divorce",
                         "md_lord_at_event": "Saturn", "ad_lord_at_event": "Sun",
                         "age_at_event_years": 40.0})
        for lord in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                     "Saturn", "Rahu", "Ketu"):
            wins.append({"person_id": pid, "md_lord": lord, "ad_lord": "Sun",
                         "duration_days": 13.0})
    return pd.DataFrame(rows), charts, pd.DataFrame(wins)


def test_classical_hitrate_shape_and_columns() -> None:
    events, charts, windows = _corpus()
    tab = classical_hitrate(events, charts, None, windows)
    assert {"hit_rate", "chance", "lift", "set_size"} <= set(tab.columns)
    mar = tab[tab.event_class == "marriage"].iloc[0]
    assert 0 <= mar["hit_rate"] <= 1


def test_mangal_dosha_and_delay_run() -> None:
    events, charts, _ = _corpus()
    k = mangal_dosha(events, charts)
    assert "kuja_rate" in k and "divorce" in k and "ratio" in k["divorce"]
    d = marriage_delay(events, charts)
    assert "delay_years" in d
