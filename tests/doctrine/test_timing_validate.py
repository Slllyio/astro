"""Guards for the daśā/timing validation harness (Phase C).

Pins the balance→timeline seeding and event placement so the MD/AD arithmetic that
reproduces Raman's stated event timings stays correct.
"""
from app.medini.doctrine.validation import timing_validate as T


def test_balance_years_conversion():
    # 2 years, 1 month, 25 days -> ~2.152 Vedic years
    y = T.balance_years({"lord": "Ketu", "years": 2, "months": 1, "days": 25})
    assert 2.14 < y < 2.16


def test_maha_sequence_seeded_from_balance():
    # Ketu balance 2.152y: Ketu window first, then Venus (20y), Sun (6y), ...
    seq = T.maha_sequence_from_balance("Ketu", 2.152)
    assert seq[0][0] == "Ketu" and abs(seq[0][2] - 2.152) < 1e-6
    assert [l for l, _, _ in seq[:4]] == ["Ketu", "Venus", "Sun", "Moon"]
    # Venus (20y) spans 2.152 -> 22.152
    assert abs(seq[1][2] - seq[1][1] - 20.0) < 1e-6


def test_event_placement_exact_cases():
    # ch72: mother died age 3 -> Venus MD, Venus AD (Raman).
    got = T.locate(3.0, "Ketu", T.balance_years({"years": 2, "months": 1, "days": 25}))
    assert got["md"] == "Venus" and got["ad"] == "Venus"
    # ch92: father died age 41 -> Jupiter MD, Mercury AD (Raman).
    got = T.locate(41.0, "Sun", T.balance_years({"years": 0, "months": 1, "days": 4}))
    assert got["md"] == "Jupiter" and got["ad"] == "Mercury"


def test_run_on_corpus_matches_all_mds():
    import json
    from pathlib import Path
    path = Path("docs/raman_doctrine/validation/corpora/heldout_timing.json")
    s = T.run(str(path))
    assert s["n_events"] >= 4
    # every event lands in the mahadasha Raman names; every bhukti is within one of his.
    assert s["md_exact"] == s["n_events"]
    assert s["ad_within_one_bhukti"] == s["ad_n"]
