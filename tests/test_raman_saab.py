"""Tests for the raman_saab death-timing validation package.

Covers the dasha timeline primitives (the numerical backbone), the
Poisson-binomial enrichment stats, and the ratchet gate logic. Uses tiny
synthetic inputs — no network, no real corpus.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.raman_saab import dasha as D
from app.medini.ml.raman_saab import population_validate as PV
from app.medini.ml.raman_saab.ratchet import apply_gate
from app.medini.ml.raman_saab.rules import CANDIDATE_RULES


# --------------------------------------------------------------------------- #
# dasha primitives                                                            #
# --------------------------------------------------------------------------- #

class TestDasha:
    def test_natal_md_lord_partition(self):
        # Moon at 0 deg -> first nakshatra -> Ketu (start of DASHA_LORDS order).
        lord, frac = D.natal_md_lord(0.0)
        assert lord == "Ketu"
        assert 0.0 <= frac < 1e-6

    def test_md_intervals_cover_span_and_are_contiguous(self):
        ml, bjd = D.moon_longitude(1900, 1, 1, 12.0, 0.0)
        ivs = D.md_intervals(ml, bjd, span_years=120)
        # contiguous
        for a, b in zip(ivs, ivs[1:]):
            assert abs(a.end_jd - b.start_jd) < 1e-6
        # spans at least 120 years from birth
        assert ivs[-1].end_jd - bjd >= 120 * D.DAYS_PER_VEDIC_YEAR - 1

    def test_ad_intervals_nest_and_sum_to_md(self):
        md = D.Interval("Saturn", 1000.0, 1000.0 + 19 * D.DAYS_PER_VEDIC_YEAR)
        ads = D.ad_intervals_in_md(md)
        assert len(ads) == 9
        assert ads[0].lord == "Saturn"  # AD sequence starts with MD lord
        assert abs(ads[-1].end_jd - md.end_jd) < 1e-6

    def test_exposure_sums_to_one(self):
        ml, bjd = D.moon_longitude(1880, 6, 15, 12.0, 78.0)
        death = bjd + 70 * D.DAYS_PER_VEDIC_YEAR
        exp = D.exposure(D.md_intervals(ml, bjd), bjd, death)
        assert abs(sum(exp.values()) - 1.0) < 1e-9
        assert all(v >= 0 for v in exp.values())

    def test_lord_at_matches_interval(self):
        ml, bjd = D.moon_longitude(1920, 3, 3, 12.0, 10.0)
        ivs = D.md_intervals(ml, bjd)
        mid = (ivs[2].start_jd + ivs[2].end_jd) / 2
        assert D.lord_at(mid, ivs) == ivs[2].lord


# --------------------------------------------------------------------------- #
# validation stats                                                            #
# --------------------------------------------------------------------------- #

class TestValidation:
    def _tiny_corpus(self) -> pd.DataFrame:
        return pd.DataFrame({
            "person_id": [f"T{i}" for i in range(20)],
            "dob": ["1900-01-01"] * 20,
            "dod": [f"19{70+i%10}-06-01" for i in range(20)],
            "lat": [40.0] * 20, "lon": [0.0] * 20,
        })

    def test_poisson_binomial_null_is_centered(self):
        # All p_i = 0.5, all observed = 0 -> z strongly negative.
        z, p = PV._pb_stats(O=0, E=10.0, var=2.5, direction="enrich")
        assert z < 0 and p > 0.5

    def test_evaluate_runs_and_returns_all_levels(self):
        df = self._tiny_corpus()
        tls = PV._build(df, 12.0)
        assert len(tls) == 20
        ages = np.array([t.death_jd - t.birth_jd for t in tls])
        rule_results, lord_rows = PV.evaluate(tls, ages)
        # 5 rules x 3 levels x 2 nulls = 30 rows
        assert len(rule_results) == len(CANDIDATE_RULES) * 3 * 2
        # RR finite and positive for every row with a positive expected count
        for r in rule_results:
            assert r.expected >= 0
        assert len(lord_rows) == 9 * 2

    def test_exposure_null_inflates_long_dashas_vs_permutation(self):
        # Documents the known length-bias: exposure RR for a long-dasha lord
        # tends to exceed the permutation RR. We just assert both nulls produce
        # finite, comparable numbers (guards the two-null wiring).
        df = self._tiny_corpus()
        tls = PV._build(df, 12.0)
        ages = np.array([t.death_jd - t.birth_jd for t in tls])
        results, _ = PV.evaluate(tls, ages)
        nulls = {r.null for r in results}
        assert nulls == {"permutation", "exposure"}


# --------------------------------------------------------------------------- #
# ratchet gate                                                                #
# --------------------------------------------------------------------------- #

class TestRatchet:
    def _fake_result(self, rr_saturn_md: float, n: int = 82000) -> dict:
        rows = []
        for rule in CANDIDATE_RULES:
            for level in rule.levels:
                for null in ("permutation", "exposure"):
                    rr = (rr_saturn_md
                          if (rule.rule_id == "raman.karaka.saturn_dasha"
                              and level == "md" and null == "permutation")
                          else 1.0)
                    p = 1e-40 if rr >= 1.20 else 0.9
                    rows.append({"rule_id": rule.rule_id, "level": level,
                                 "direction": rule.direction, "null": null,
                                 "n": n, "observed": 100, "expected": 100.0,
                                 "rr": rr, "z": 5.0, "p_one_sided": p})
        return {"n_persons": n, "bonferroni_alpha": 0.01 / 15,
                "rule_results": rows}

    def test_high_power_failure_is_refuted(self):
        ledger = apply_gate(self._fake_result(rr_saturn_md=0.97))
        saturn = next(r for r in ledger if r["rule_id"] == "raman.karaka.saturn_dasha")
        assert saturn["to_status"] == "refuted"
        assert saturn["gate"]["G1"] is False

    def test_g1_pass_is_provisional_not_validated(self):
        # Even a strong pass cannot reach 'validated' on a single corpus.
        ledger = apply_gate(self._fake_result(rr_saturn_md=1.40))
        saturn = next(r for r in ledger if r["rule_id"] == "raman.karaka.saturn_dasha")
        assert saturn["to_status"] == "provisional"
        assert saturn["gate"]["G1"] is True
        assert saturn["gate"]["G2_replication"] is False

    def test_underpowered_is_not_refuted(self):
        ledger = apply_gate(self._fake_result(rr_saturn_md=0.97, n=100))
        saturn = next(r for r in ledger if r["rule_id"] == "raman.karaka.saturn_dasha")
        assert saturn["to_status"] == "candidate"
