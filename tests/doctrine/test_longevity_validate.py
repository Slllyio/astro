"""Guards for the longevity-class outcome-classification pilot.

Pins the pilot's contract: the labelled set loads and scores, the dependency-free Spearman
matches a hand-computed value, and the headline finding holds — the 8th-BHAVA score is the
positive predictor of longevity class while the lord/karaka scores are not.
"""
from app.medini.doctrine.validation import longevity_validate as L


def test_spearman_matches_known_value():
    # perfect monotone -> rho = 1.0; a hand case with one swap
    rho, _ = L._spearman([1, 2, 3, 4], [1, 2, 3, 4])
    assert abs(rho - 1.0) < 1e-9
    rho, _ = L._spearman([1, 2, 3, 4], [1, 2, 4, 3])
    assert abs(rho - 0.8) < 1e-9


def test_run_scores_all_labels():
    s = L.run()
    assert s["n"] == 14
    assert s["n_skipped"] == 0
    # every class ordinal present (0..3)
    assert {r["ord"] for r in s["rows"]} == {0, 1, 2, 3}


def test_bhava_is_the_positive_predictor():
    s = L.run()
    sp = s["spearman"]
    # the headline: 8th-bhava strength positively tracks longevity class...
    assert sp["bhava"]["rho"] > 0.4
    assert sp["bhava"]["p"] < 0.1
    # ...while the lord/karaka (general benefic-strength) do not (trend negative).
    assert sp["lord"]["rho"] < 0
    assert sp["karaka"]["rho"] < 0
    # bhava is the strongest positive signal of all factors
    assert sp["bhava"]["rho"] == max(v["rho"] for v in sp.values())


def test_ayushkaraka_fix_does_not_work():
    """Track L result: the Āyushkāraka gap is NOT closable by re-scoping the karaka.
    Every lord/karaka strength anti-correlates with longevity (Raman selects afflicted-
    looking-yet-long-lived teaching charts), and the dignity+placement scoping -- the
    hypothesised Ayurdaya fix -- is the WORST, not a rescue."""
    sp = L.run()["spearman"]
    assert sp["karaka_digplace"]["rho"] < 0          # the "fix" fails...
    assert sp["karaka_digplace"]["rho"] < sp["karaka"]["rho"]   # ...and is worse than the raw karaka
    # only the bhava (and, weakly, the Lagna) carry the longevity signal
    assert sp["bhava"]["rho"] > 0 and sp["lagna"]["rho"] > 0
