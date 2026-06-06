"""Thin CI wrapper around the golden-extractor machinery.

``tools/raman_saab/extract_goldens.py`` ships an internal ``_self_test()`` that
exercises the keyword lexicon, the ``condition_solver`` (solvable + refusal paths),
and the ``GoldenRecord`` JSON round-trip. That self-test is normally only reachable
via the CLI (``--self-test``); this module puts the same machinery on the pytest /
CI path so the extractor cannot silently rot.

It does two things:

* runs ``_self_test()`` end-to-end and asserts it returns 0; and
* parametrises the lexicon + condition_solver cases individually, so a regression
  points at the exact failing case rather than a single opaque pass/fail.

Run:
    py -3.12 -m pytest tests/raman_saab/test_extract_goldens.py -q
"""
from __future__ import annotations

import pytest

from app.raman_saab.doctrine import conditions as C
from tools.raman_saab import extract_goldens as eg


def test_extract_goldens_self_test_passes() -> None:
    """The extractor's built-in machinery self-test returns 0 (all checks pass)."""
    assert eg._self_test() == 0


# --- lexicon cases (mirror extract_goldens._self_test, parametrised) ---------
_LEXICON_CASES = [
    ("He died early, the son was lost.", "afflicted"),
    ("Rose to great eminence and long life.", "favourable"),
    ("Owned then lost the property; gains and losses throughout.", "mixed"),
    ("Great learning but premature death.", "afflicted"),   # affliction dominates
    ("Strong Lagna but checkered career.", "mixed"),
    ("He was wealthy but never at peace.", "mixed"),         # concession demotes
    ("The native travelled south.", "insufficient-evidence"),
    ("", "insufficient-evidence"),
]


@pytest.mark.parametrize("prose,want", _LEXICON_CASES,
                         ids=[w + ":" + (p[:24] or "<empty>") for p, w in _LEXICON_CASES])
def test_classify_prose(prose: str, want: str) -> None:
    """classify_prose maps a Raman verdict sentence to the documented DRAFT ordinal."""
    assert eg.classify_prose(prose) == want


# --- condition_solver: solvable cases ---------------------------------------

def test_condition_solver_and_inrashihouse_conjunct() -> None:
    """And(InRashiHouse, Conjunct) -> both planets land in the pinned house; chart full."""
    stated = eg.condition_solver(C.And(C.InRashiHouse("Saturn", 7),
                                       C.Conjunct("Mars", "Saturn")))
    assert stated["Saturn"]["bhava"] == 7
    assert stated["Mars"]["bhava"] == 7
    assert len(stated) == len(eg._ALL_PLANETS)


def test_condition_solver_lordin_and_inhousefrom_lagna() -> None:
    """LordIn + InHouseFrom(LAGNA, 5) -> Jupiter is placed in the 5th."""
    stated = eg.condition_solver(C.And(C.LordIn(7, 1),
                                       C.InHouseFrom("Jupiter", "LAGNA", 5)))
    assert stated["Jupiter"]["bhava"] == 5


# --- condition_solver: refusal cases (never fabricate a chart) ---------------
_REFUSAL_CASES = [
    (C.Not(C.InRashiHouse("Sun", 1)), "Not()"),
    (C.HasDignity("Sun", {"exalt"}), "unknown-predicate"),
    (C.And(C.InRashiHouse("Mars", 1), C.InRashiHouse("Mars", 7)), "contradiction"),
]


@pytest.mark.parametrize("cond,label", _REFUSAL_CASES, ids=[c[1] for c in _REFUSAL_CASES])
def test_condition_solver_refuses(cond: C.Condition, label: str) -> None:
    """The solver escalates (UnsolvableCondition) rather than fabricate a chart."""
    with pytest.raises(eg.UnsolvableCondition):
        eg.condition_solver(cond)
