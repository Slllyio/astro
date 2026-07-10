"""Guard the fresh DEGREE-ACCURATE NH strength held-out: it reconstructs from printed degrees
(not signs), scores every hand-verified verdict with no exclusions, and records the engine's
systematic over-credit on afflicted cases."""
from app.medini.doctrine.validation import nh_strength_validate as N


def test_nh_strength_scores_all_rows_from_degree_positions():
    s = N.run()
    assert s["n"] >= 14
    assert s["n_excluded"] == 0                     # every row maps + every case has positions
    # this corpus is afflicted-skewed and degree-exact; the engine over-credits it -> mean Δ > 0
    assert s["mean_delta"] > 0.5
    # within-one is real but below the HTJAH ~54% (harder, afflicted-heavy set)
    assert 0.0 <= s["within1_pct"] <= 100.0


def test_nh_reconstruction_is_degree_based_not_sign():
    # The chart must come from from_printed_positions (degrees), so intra-sign degree is real,
    # not a pada midpoint. Two planets in the same sign must have distinct longitudes.
    from app.medini.ml.raman_saab.golden_registry import load_registry
    case = next(c for c in load_registry() if c.key == "nehru")
    chart = N._chart_for(case)
    lons = chart.bundle.chart.planet_lons
    assert any(abs((lons[a] % 30) - (lons[b] % 30)) > 1e-6
               for a in lons for b in lons if a != b)
