"""The LIVE ch. IV anchor gate (P0 of the engine overhaul).

`test_audit_anchor.py` gates the hand-decoded HARNESS representation (frozen findings
through validate_house.predict) — increment 15b proved the live engine drifted to ~1/8
on these very charts while that test read 8/8. THIS test is the authoritative anchor
gate for the live engine:

- faithfulness: the corpus casts must keep matching Raman's prose-stated placements;
- a RATCHET floor on within-one (raise it in the same commit as any landing that
  improves it — never lower it);
- a per-row grade LEDGER: any change to any anchor grade must be deliberate and shows
  up here as an explicit diff to update alongside the audit increment that caused it.
"""
import pytest

from app.medini.doctrine.validation import anchor_live_validate as A


@pytest.fixture(scope="module")
def summary():
    return A.run()


def test_casts_are_faithful(summary):
    # chart_for() raises AssertionError on any expected-sign mismatch; reaching here
    # with 8 scored rows means every anchor placement still matches Raman's prose.
    assert summary["n"] == 8


# RATCHET: the honest live-engine number at P0 (2026-07-11) is 1/8 within-one,
# mean delta -3.75 (all misses UNDER-credits; see HOUSE_SCHEME_AUDIT increment 16).
# Raise this floor in the same commit as any landing that improves it.
_WITHIN1_FLOOR = 1


def test_anchor_live_within_one_floor(summary):
    assert summary["within1"] >= _WITHIN1_FLOOR, (
        f"live anchor fell below the ratchet floor: {summary['within1']}/8 "
        f"< {_WITHIN1_FLOOR} — an engine change regressed Raman's own calibration charts"
    )


# LEDGER: the current per-row engine grades. An intentional engine change that moves
# any of these must update this dict IN THE SAME COMMIT, citing its audit increment.
# Updated at increment 17 (sutra-fed strength): within-one unchanged at 1/8, mean
# delta unchanged (-3.75); intra-band shuffles only -- 13-bhava improved (-5 -> -3),
# 12/13-lord moved weak -> afflicted (ch. IV lord-in-8th/12th sutras fire unfavorably;
# doctrinally correct testimony Raman himself overrides on these charts -- P3's case).
_LEDGER = {
    (12, "bhava"): "moderate",
    (12, "lord"): "afflicted",
    (12, "karaka"): "afflicted",
    (13, "bhava"): "moderate",
    (13, "lord"): "afflicted",
    (13, "karaka"): "weak",
    (14, "lord"): "afflicted",
    (14, "karaka"): "afflicted",
}


def test_anchor_grade_ledger(summary):
    got = {(r["chart"], r["factor"]): r["engine"] for r in summary["rows"]}
    assert got == _LEDGER, (
        "live anchor grades moved — if intentional, UPDATE _LEDGER in the same commit "
        f"and cite the audit increment. diff: "
        f"{ {k: (got.get(k), _LEDGER.get(k)) for k in set(got) | set(_LEDGER) if got.get(k) != _LEDGER.get(k)} }"
    )


def test_structural_vargottama_override(summary):
    # Chart 14's bhava: vargottama lagna is a decoded hard override -> very powerful.
    (row,) = summary["structural"]
    assert row["engine"] == "very powerful"
