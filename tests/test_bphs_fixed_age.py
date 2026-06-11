"""Tests for BPHS fixed-age yoga predicates."""
from __future__ import annotations

import pandas as pd

from app.medini.ml.bphs_fixed_age import YOGAS, _err, _f, _seventh_from


def _crow(asc=1, **over):
    base = {"asc_sign": asc}
    for g in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
              "rahu", "ketu"):
        base[f"{g}_sign"] = over.pop(f"{g}_sign", 1)
        base[f"{g}_house"] = over.pop(f"{g}_house", 1)
    base.update(over)
    return pd.Series(base)


def test_seventh_from_wraps() -> None:
    assert _seventh_from(1) == 7
    assert _seventh_from(7) == 1
    assert _seventh_from(12) == 6


def test_err_nearest_prediction() -> None:
    assert _err(20.0, (12, 19)) == 1.0
    assert _err(30.0, (31, 33)) == 1.0


def test_yoga_18_27_predicate() -> None:
    # Moon in 1 → Venus must be in 7; Saturn in 7th-from-Venus = 1.
    f = _f(_crow(moon_sign=1, venus_sign=7, saturn_sign=1))
    pred, ages = YOGAS["18.27 Venus 7th-from-Moon + Saturn 7th-from-Venus → 18"]
    assert pred(f) and ages == (18,)
    f2 = _f(_crow(moon_sign=1, venus_sign=6, saturn_sign=1))
    assert not pred(f2)


def test_yoga_18_34_predicate() -> None:
    # asc=1 → 7H sign=7 (Libra), 7L=Venus... but Venus must be in 1H AND 7L in
    # 7H — impossible for asc=1 (7L IS Venus). Use asc=2: 7H sign=8, 7L=Mars.
    f = _f(_crow(asc=2, venus_house=1, mars_house=7))
    pred, _ = YOGAS["18.34 Venus in 1H + 7L in 7H → 27,30"]
    assert pred(f)
    assert not pred(_f(_crow(asc=2, venus_house=2, mars_house=7)))
