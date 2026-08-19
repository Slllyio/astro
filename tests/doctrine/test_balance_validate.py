"""Guard the NH printed-balance validation: the engine's Vimśottarī start-balance reproduces
Raman's printed 'Balance of X Dasa at birth' line for the great majority of golden cases."""
from app.medini.doctrine.validation import balance_validate as B


def test_engine_balance_matches_ramans_printed_lines():
    s = B.run()
    assert s["n"] >= 25
    # MD-lord exact on >= 90% (28/30); the <=2 misses are Moon-longitude OCR, not engine error.
    assert s["lord_pct"] >= 90.0
    # where the lord matches, the printed duration matches to within 0.5y just as often.
    assert s["dur_within_tol"] == s["lord_exact"]


def test_balance_is_computed_from_the_moon_only():
    # Vimśottarī balance is a pure function of the Moon; changing the JD must not move it.
    from app.core.ephemeris_engine import calculate_vimshottari_mahadasha
    a = calculate_vimshottari_mahadasha(200.75, 2451545.0)
    b = calculate_vimshottari_mahadasha(200.75, 2400000.0)
    assert a["mahadasha_lord"] == b["mahadasha_lord"]
    assert abs(a["years_remaining"] - b["years_remaining"]) < 1e-9
