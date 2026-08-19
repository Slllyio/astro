"""Phase D.0 — guards for the kāraka-ceiling separability diagnostic.

Pins the measurement contract (not an engine behaviour): the decomposition is faithful to the
live engine's findings, and the plan's falsification invariant holds — ch70's Moon, besieged
only by whole-sign aspects, must show ZERO same-sign conjunctions, so a conjunction-orb feature
provably cannot touch it.
"""
import math

from app.medini.doctrine.validation import ceiling_diagnostic as CD


def _run():
    return CD.run()  # all held-out corpora


def test_falsification_ch70_moon_has_no_same_sign_conjunction():
    rows = _run()["rows"]
    ch70 = [r for r in rows if r["chart"] == 70 and "ch07" in r["src"]]
    assert ch70, "ch70 (4th-house) over-credit rows should be present"
    for r in ch70:
        assert r["subject"] == "Moon"
        assert r["n_conj_malefic"] == 0        # alone in Capricorn — aspect-besieged only
        assert r["n_aspect_malefic"] >= 2      # Saturn 3rd + Mars 8th
        assert r["min_orb_deg"] is None


def test_overcredit_rows_are_lord_or_karaka_and_positive_delta():
    for r in _run()["rows"]:
        assert r["factor"] in ("lord", "karaka")
        assert r["delta"] >= CD._OVERCREDIT


def test_classification_partitions_every_row():
    s = _run()
    # each row is exactly one of: conjunction-present / aspect-only / offset-only
    assert s["conj_present"] + s["aspect_only"] + s["offset_only"] == s["n_overcredit_rows"]
    # the headline finding: conjunctions are the minority (aspect+offset dominate)
    assert s["aspect_only"] + s["offset_only"] >= s["conj_present"]


def test_pada_orbs_are_quantized_to_3p33():
    # every reported conjunction orb is a whole number of padas (pada-midpoint reconstruction)
    for r in _run()["rows"]:
        for c in r["conj_malefics"]:
            assert math.isclose(c["orb_padas"], round(c["orb_padas"]), abs_tol=0.02)
