"""Regression gate on the HTJAH calibration corpora.

The corpora in docs/raman_doctrine/audit/ calibrate the strength point-scheme
against Raman's worked verdicts. This pins two invariants so a future scheme edit
cannot silently drift the calibration:

- the ch. IV Charts 12-14 anchor stays 8/8 within-one (a fixed calibration point);
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
    # Established floor (post Phase 2.1). Improvements should raise this; a drop
    # below it is a calibration regression to investigate before committing.
    assert ok >= 79, f"corpus within-one regressed to {ok}/104 (floor 79)"
