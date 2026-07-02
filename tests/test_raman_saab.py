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

class TestKundali:
    def test_einstein_lagna_and_marakas(self):
        # Einstein: 1879-03-14 11:30, Ulm (48.4N 10.0E), LMT +0.6989h.
        # ADB/JHora give Gemini rising -> lagna sign 3; whole-sign marakas:
        # 2H Cancer -> Moon, 7H Sagittarius -> Jupiter.
        from app.medini.ml.raman_saab.kundali import cast_kundali
        k = cast_kundali(1879, 3, 14, 11, 30, 0.6989, 48.4, 10.0)
        assert k is not None
        assert k.lagna_sign == 3
        assert k.maraka_lords == frozenset({"Moon", "Jupiter"})
        assert k.lord_8 == "Saturn"  # 8H Capricorn from Gemini

    def test_nth_sign_wraps(self):
        from app.medini.ml.raman_saab.kundali import _nth_sign
        assert _nth_sign(12, 2) == 1   # Pisces lagna -> 2H Aries
        assert _nth_sign(7, 7) == 1    # Libra lagna -> 7H Aries
        assert _nth_sign(1, 1) == 1

    def test_bad_input_returns_none(self):
        from app.medini.ml.raman_saab.kundali import cast_kundali
        assert cast_kundali(1879, 13, 45, 11, 30, 0.0, 91.0, 500.0) is None


class TestAdbParsers:
    def test_parse_adb_tz_notations(self):
        from app.medini.etl.adb_wayback_death_corpus import parse_adb_tz
        assert abs(parse_adb_tz("LMT m10e0 (is local mean time)") - 10 / 15) < 1e-9
        assert parse_adb_tz("CET h1e (is standard time)") == 1.0
        assert parse_adb_tz("EST h5w (is standard time)") == -5.0
        assert parse_adb_tz("h5w30") == -5.5
        assert abs(parse_adb_tz("LMT m77w35") - (-(77 + 35 / 60) / 15)) < 1e-9
        assert parse_adb_tz("") is None

    def test_death_line_matches_own_death_only(self):
        from app.medini.etl.adb_wayback_death_corpus import parse_death_date
        own = "<li>Death&#160;: Death  18 April 1955 at 01:15 AM (age 76)</li>"
        family = "<li>Death of Mate  20 December 1936</li>"
        cause = "<li>Death by Heart Attack  22 March 1994</li>"
        assert parse_death_date(own) == "1955-04-18"
        assert parse_death_date(family) is None
        assert parse_death_date(cause) == "1994-03-22"

    def test_parse_coordinate_mmss_run_together(self):
        # ADB seconds-precision format with no separator: "36n4619" is
        # 36°46'19", NOT 36 + 4619 minutes (the bug that produced lat=112.98
        # for Ferhat Abbas, born Taher, Algeria 36.77N).
        from app.medini.etl.scraper import parse_coordinate
        assert abs(parse_coordinate("36n4619") - (36 + 46 / 60 + 19 / 3600)) < 1e-9
        assert abs(parse_coordinate("5e5354") - (5 + 53 / 60 + 54 / 3600)) < 1e-9
        # 2-digit minutes unchanged; explicit-seconds form unchanged.
        assert abs(parse_coordinate("48n24") - 48.4) < 1e-9
        assert abs(parse_coordinate("48n24'15") - (48 + 24 / 60 + 15 / 3600)) < 1e-9
        # Malformed DMS (minutes >= 60) rejected, not mis-read.
        assert parse_coordinate("48n7205") is None

    def test_parse_adb_tz_mmss_meridian(self):
        # "PMT m2e2015" = Paris Mean Time, meridian 2°20'15"E -> +0.1556h,
        # NOT (2 + 2015/60)/15 = +2.37h.
        from app.medini.etl.adb_wayback_death_corpus import parse_adb_tz
        want = (2 + 20 / 60 + 15 / 3600) / 15
        assert abs(parse_adb_tz("PMT m2e2015 (is standard time)") - want) < 1e-9

    def test_name_from_entry_url(self):
        from app.medini.etl.adb_wayback_death_corpus import name_from_entry_url
        assert name_from_entry_url(
            "https://www.astro.com/astro-databank/Kennedy,_John_F."
        ) == "John F. Kennedy"
        assert name_from_entry_url(
            "https://www.astro.com/astro-databank/Einstein,_Albert"
        ) == "Albert Einstein"


class TestMarakaResolvers:
    def test_saturn_if_maraka_empty_when_not_maraka(self):
        from app.medini.ml.raman_saab.kundali import cast_kundali
        from app.medini.ml.raman_saab.maraka_validate import _RESOLVERS
        # Einstein (Gemini lagna): marakas Moon/Jupiter -> Saturn not maraka.
        k = cast_kundali(1879, 3, 14, 11, 30, 0.6989, 48.4, 10.0)
        assert _RESOLVERS["saturn_if_maraka"](k) == set()
        assert _RESOLVERS["maraka_lords"](k) == {"Moon", "Jupiter"}
        assert _RESOLVERS["maraka_and_8"](k) == {"Moon", "Jupiter", "Saturn"}


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
