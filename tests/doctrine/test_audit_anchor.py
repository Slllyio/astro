"""Regression gate on the HTJAH calibration corpora — HARNESS representation only.

SCOPE (re-framed at P0 of the engine overhaul; HOUSE_SCHEME_AUDIT increment 16): these
corpora store hand-decoded typed findings in the audit harness's own weight vocabulary,
evaluated through ``validate_house.predict`` — NOT through the live
``judge_house_doctrine``. The 8/8 anchor below therefore pins the DECODED-HARNESS
calibration against silent drift of `validate_house`, and nothing more. Increment 15b
proved the live engine can (and did) drift on these very charts while this test stayed
green. **The authoritative live-engine anchor gate is ``test_anchor_live.py``**, backed
by the faithfulness-gated cast corpus ``htjah_anchor_live.json``.

Pinned here:
- the ch. IV Charts 12-14 anchor stays 8/8 within-one under the harness;
- the pooled corpus stays at or above its established within-one floor.

The harness lives under docs/ (provenance, not shipped code), so it is imported by
path here.
"""
import importlib.util
import json
from pathlib import Path

import pytest

_AUDIT = Path(__file__).resolve().parents[2] / "docs" / "raman_doctrine" / "audit"
_CORPORA = _AUDIT / "corpora"


def _load_harness():
    spec = importlib.util.spec_from_file_location(
        "raman_validate_house", _AUDIT / "validate_house.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _within_one(mod, *corpus_names):
    idx = mod.IDX
    total = ok = 0
    for name in corpus_names:
        corpus = json.loads((_CORPORA / name).read_text())
        for row in corpus["rows"]:
            pred, _score = mod.predict(row)
            total += 1
            if abs(idx[pred] - idx[row["expected"]]) <= 1:
                ok += 1
    return ok, total


@pytest.fixture(scope="module")
def harness():
    return _load_harness()


def test_anchor_stays_eight_of_eight(harness):
    ok, total = _within_one(harness, "htjah_anchor_calibration.json")
    assert (ok, total) == (8, 8), f"ch.IV anchor drifted: {ok}/{total} within-one"


def test_corpus_within_one_floor(harness):
    ok, total = _within_one(
        harness, "htjah_h2_calibration.json", "htjah_h7_calibration.json",
        "htjah_h9_calibration.json", "htjah_h11_calibration.json")
    assert total == 104
    # Floor raised to 81 by Phase 2.2 (no-phantom-frame blend). Improvements should
    # raise it further; a drop below is a calibration regression to investigate.
    assert ok >= 81, f"corpus within-one regressed to {ok}/104 (floor 81)"
