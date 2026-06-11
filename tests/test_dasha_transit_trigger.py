"""Tests for transit trigger predicates and grid."""
from __future__ import annotations

import numpy as np

from app.medini.ml import dasha_transit_trigger as tt


def test_trines_wraps() -> None:
    assert tt.trines(1) == {1, 5, 9}
    assert tt.trines(7) == {7, 11, 3}
    assert tt.trines(12) == {12, 4, 8}


def test_influences_special_drishti() -> None:
    # Jupiter in sign 1 aspects 1 (conj), 5, 7, 9.
    assert tt._influences(1, 5, tt._JUP_DRISHTI)
    assert tt._influences(1, 7, tt._JUP_DRISHTI)
    assert not tt._influences(1, 4, tt._JUP_DRISHTI)
    # Saturn in sign 1 aspects 1, 3, 7, 10.
    assert tt._influences(1, 3, tt._SAT_DRISHTI)
    assert tt._influences(1, 10, tt._SAT_DRISHTI)
    assert not tt._influences(1, 5, tt._SAT_DRISHTI)


def test_double_transit_and_sade_sati_predicates() -> None:
    t = {"house_sign": 7, "moon_sign": 4}
    # Jupiter in 7 (conj) + Saturn in 10 (10th from 10? pos of 7 from 10 = 10) →
    # Saturn in sign 10 aspects ((7-10)%12)+1 = 10 ∈ drishti → both influence.
    assert tt.double_transit_house(7, 10, t)
    assert not tt.double_transit_house(8, 11, t)   # Jup in 8: pos 12 → no
    # Saturn in 3rd..5th from Moon(4): signs 3,4,5 are 12th/1st/2nd from Moon.
    assert tt.sat_12_1_2_from_moon(1, 3, t)
    assert tt.sat_12_1_2_from_moon(1, 4, t)
    assert tt.sat_12_1_2_from_moon(1, 5, t)
    assert not tt.sat_12_1_2_from_moon(1, 7, t)


def test_grid_signs_change_slowly() -> None:
    g = tt.TransitGrid(2440000.0, 2440000.0 + 3650.0)   # 10 years
    # Jupiter ~12 signs/12yr: expect ~9-11 distinct transitions, never jumping >1.
    diffs = np.abs(np.diff(g.jup))
    diffs = diffs[diffs > 0]
    assert ((diffs == 1) | (diffs == 11)).all()          # adjacent (with wrap)
    j, s = g.at(np.array([2440100.0]))
    assert 1 <= int(j[0]) <= 12 and 1 <= int(s[0]) <= 12
