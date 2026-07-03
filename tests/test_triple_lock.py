"""Tests for the run-3 Triple-Lock harness and parameterized gate.

Synthetic PersonContexts with analytically known null probabilities — no
corpus files, no network. The ingress tables build from Moshier in-process.
"""
from __future__ import annotations

import numpy as np
import pytest
import swisseph as swe

from app.medini.ml.raman_saab import population_validate as PV
from app.medini.ml.raman_saab import triple_lock as TL
from app.medini.ml.raman_saab.ayurdaya import AyuBand
from app.medini.ml.raman_saab.run3_gate import (
    apply_gate_run3, power_at_threshold,
)

_JD0 = swe.julday(1900, 1, 1, 12.0, swe.GREG_CAL)


def _person(*, maraka_all: bool, band: AyuBand, death_age_years: float,
            asc: int = 1, moon: int = 1) -> TL.PersonContext:
    """One-interval dasha timeline; maraka mask all-on or all-off."""
    mask = np.ones(PV._N, dtype=bool) if maraka_all else np.zeros(PV._N, bool)
    return TL.PersonContext(
        person_id="synth", birth_jd=_JD0,
        death_jd=_JD0 + death_age_years * 365.2425,
        ad_start=np.array([_JD0 - 1e6]),
        ad_lord=np.array([0], dtype=np.int8),
        ad_pmd_lord=np.array([0], dtype=np.int8),
        asc_sign=asc, moon_sign=moon,
        maraka_mask=mask, ayu_band=int(band), rodden="AA", lat=10.0,
    )


class TestEvaluateAnalytic:
    def test_leg1_degenerate_probabilities(self):
        """maraka_all -> p_i=1 and observed=1 -> RR exactly 1; all-off -> 0/0."""
        ages = np.array([75.0, 80.0, 85.0]) * 365.2425
        res = TL.evaluate([_person(maraka_all=True, band=AyuBand.PURNAYU,
                                   death_age_years=80.0)], ages)
        rows = {r["test"]: r for r in res["rows"]}
        assert rows["leg1_maraka"]["observed"] == 1
        assert rows["leg1_maraka"]["expected"] == pytest.approx(1.0)
        assert rows["leg1_maraka"]["rr"] == pytest.approx(1.0)
        res0 = TL.evaluate([_person(maraka_all=False, band=AyuBand.PURNAYU,
                                    death_age_years=80.0)], ages)
        rows0 = {r["test"]: r for r in res0["rows"]}
        assert rows0["leg1_maraka"]["observed"] == 0
        assert rows0["leg1_maraka"]["expected"] == pytest.approx(0.0)

    def test_leg3_band_match_probability(self):
        """Sampled ages 50/60/80: PURNAYU prediction -> p=1/3; death at 75
        (PURNAYU) -> observed hit."""
        ages = np.array([50.0, 60.0, 80.0]) * 365.2425
        p = _person(maraka_all=True, band=AyuBand.PURNAYU, death_age_years=75.0)
        res = TL.evaluate([p], ages)
        rows = {r["test"]: r for r in res["rows"]}
        # rows round expected to 2 decimals for readability (stats use the
        # unrounded accumulators)
        assert rows["leg3_ayurdaya"]["expected"] == pytest.approx(1 / 3, abs=0.005)
        assert rows["leg3_ayurdaya"]["observed"] == 1

    def test_joint_null_uses_shared_draws(self):
        """Joint E <= min(leg E): conjunction cannot exceed a component."""
        ages = np.array([30.0, 50.0, 75.0, 90.0]) * 365.2425
        p = _person(maraka_all=True, band=AyuBand.MADHYAYU, death_age_years=50.0)
        res = TL.evaluate([p], ages)
        rows = {r["test"]: r for r in res["rows"]}
        assert rows["triple_lock"]["expected"] <= min(
            rows["leg1_maraka"]["expected"],
            rows["leg2_gochara"]["expected"],
            rows["leg3_ayurdaya"]["expected"]) + 1e-12

    def test_death_age_override_moves_observed(self):
        """The preflight override changes the observed moment, not the null."""
        ages = np.array([40.0, 75.0]) * 365.2425
        p = _person(maraka_all=True, band=AyuBand.PURNAYU, death_age_years=75.0)
        res_true = TL.evaluate([p], ages)
        res_over = TL.evaluate([p], ages,
                               death_ages_override=np.array([40.0 * 365.2425]))
        t = {r["test"]: r for r in res_true["rows"]}
        o = {r["test"]: r for r in res_over["rows"]}
        assert t["leg3_ayurdaya"]["observed"] == 1
        assert o["leg3_ayurdaya"]["observed"] == 0
        assert t["leg3_ayurdaya"]["expected"] == o["leg3_ayurdaya"]["expected"]

    def test_confusion_matrix_and_kappa(self):
        ages = np.array([75.0]) * 365.2425
        people = [
            _person(maraka_all=True, band=AyuBand.PURNAYU, death_age_years=80.0),
            _person(maraka_all=True, band=AyuBand.ALPAYU, death_age_years=80.0),
        ]
        res = TL.evaluate(people, ages)
        cm = res["ayurdaya_confusion"]
        assert cm["accuracy"] == pytest.approx(0.5)
        assert np.array(cm["matrix_pred_x_obs"]).sum() == 2


class TestGate:
    def _result(self, rr: float, expected: float = 500.0, n: int = 2000) -> dict:
        rows = []
        for t, thr in (("leg1_maraka", 1.2), ("leg2_gochara", 1.2),
                       ("leg3_ayurdaya", 1.2), ("triple_lock", 1.5)):
            E = expected
            var = E * 0.7
            O = rr * E if t == "triple_lock" else E
            z = (O - E) / np.sqrt(var)
            from scipy.stats import norm
            rows.append({"test": t, "tier": "primary", "null": "permutation",
                         "n": n, "observed": int(O), "expected": E,
                         "var": var, "rr": round(O / E, 4),
                         "z": round(float(z), 3),
                         "p_one_sided": float(norm.sf(z))})
        return {"results": rows, "n_persons": n}

    def test_pass_capped_at_provisional(self):
        ledger = apply_gate_run3(self._result(rr=1.8))
        joint = next(e for e in ledger
                     if e["rule_id"] == "raman.triple_lock.triple_lock")
        assert joint["to_status"] == "provisional"
        assert joint["gate"]["G1"] is True

    def test_fail_with_power_is_refuted(self):
        ledger = apply_gate_run3(self._result(rr=1.0))
        joint = next(e for e in ledger
                     if e["rule_id"] == "raman.triple_lock.triple_lock")
        assert joint["to_status"] == "refuted"
        assert joint["gate"]["power_at_threshold"] >= 0.90

    def test_fail_underpowered_stays_candidate(self):
        # Tiny E -> no power -> candidate, not refuted.
        ledger = apply_gate_run3(self._result(rr=1.0, expected=5.0))
        joint = next(e for e in ledger
                     if e["rule_id"] == "raman.triple_lock.triple_lock")
        assert joint["to_status"] == "candidate"

    def test_power_monotone_in_expected(self):
        p_small = power_at_threshold(1.5, 20.0, 14.0, 0.0025)
        p_big = power_at_threshold(1.5, 200.0, 140.0, 0.0025)
        assert p_big > p_small
