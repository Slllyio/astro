"""Rasi drishti — Jaimini sign aspects (JS 1.1). Movable<->fixed except adjacent; dual<->dual."""
from __future__ import annotations

from app.raman_saab.primitives import rasi_drishti as rd


def test_aries_aspects_leo_scorpio_aquarius():
    assert rd.signs_aspected_by(1) == frozenset({5, 8, 11})


def test_gemini_dual_aspects_other_duals():
    assert rd.signs_aspected_by(3) == frozenset({6, 9, 12})


def test_fixed_taurus_aspects_movable_except_adjacent_aries():
    assert rd.signs_aspected_by(2) == frozenset({4, 7, 10})        # not Aries (the adjacent movable)


def test_relation_is_mutual():
    for a in range(1, 13):
        for b in rd.signs_aspected_by(a):
            assert rd.sign_aspects_sign(b, a), (a, b)


def test_no_sign_aspects_itself_or_its_own_modality_neighbours_wrongly():
    for s in range(1, 13):
        assert s not in rd.signs_aspected_by(s)
        assert len(rd.signs_aspected_by(s)) == 3       # always exactly three signs aspected
