"""Tests for app/medini/ml/dasha_doctrine_pooled.py.

Pins the Mantel-Haenszel pooling primitives + birth_jd deduplication:
- log-RR variance is 1/n_top + 1/n_bot under Poisson
- pooled estimator is inverse-variance-weighted average
- Cochran's Q homogeneity test fires when strata truly disagree
- birth_jd dedup keeps ADB > WD > LA precedence
"""
from __future__ import annotations

import pytest

pytest.importorskip("app.medini.ml.dasha_doctrine_score")  # in-flight module not present on this branch

import math

import numpy as np
import pandas as pd
import pytest

from app.medini.ml.dasha_doctrine_pooled import (
    CorpusRR,
    _CORPUS_PRECEDENCE,
    _dedup_by_birth_jd,
    _mantel_haenszel_log_rr,
    _per_corpus_rr,
)


class TestCorpusRRDataclass:
    """The CorpusRR dataclass holds per-stratum stats for MH pooling."""

    def test_log_rr_is_log_of_rr(self):
        """log_rr property is just np.log(rr)."""
        c = CorpusRR(
            corpus="X", n_events_top=10, exp_top_days=100.0,
            n_events_bot=5, exp_bot_days=100.0,
            rr=2.0, log_rr_var=0.3,
        )
        assert math.isclose(c.log_rr, math.log(2.0), rel_tol=1e-9)

    def test_log_rr_handles_nan_rr(self):
        """nan rr should produce nan log_rr (used as filter signal)."""
        c = CorpusRR(corpus="X", n_events_top=0, exp_top_days=100.0,
                     n_events_bot=5, exp_bot_days=100.0,
                     rr=float("nan"), log_rr_var=1.0)
        assert math.isnan(c.log_rr)


class TestMantelHaenszelPool:
    """Inverse-variance-weighted pooling under Poisson assumption."""

    def test_single_stratum_returns_that_stratum_rr(self):
        """One stratum → pooled RR equals the stratum's RR."""
        only = CorpusRR(corpus="ADB", n_events_top=20, exp_top_days=100.0,
                        n_events_bot=10, exp_bot_days=100.0,
                        rr=2.0, log_rr_var=1.0/20 + 1.0/10)
        result = _mantel_haenszel_log_rr([only])
        assert math.isclose(result["rr_pooled"], 2.0, rel_tol=1e-9)
        assert result["k"] == 1

    def test_two_identical_strata_pooled_equals_individual(self):
        """Two identical strata → pooled RR matches either stratum."""
        s1 = CorpusRR(corpus="A", n_events_top=20, exp_top_days=100.0,
                      n_events_bot=10, exp_bot_days=100.0,
                      rr=2.0, log_rr_var=1.0/20 + 1.0/10)
        s2 = CorpusRR(corpus="B", n_events_top=20, exp_top_days=100.0,
                      n_events_bot=10, exp_bot_days=100.0,
                      rr=2.0, log_rr_var=1.0/20 + 1.0/10)
        result = _mantel_haenszel_log_rr([s1, s2])
        assert math.isclose(result["rr_pooled"], 2.0, rel_tol=1e-9)
        assert result["k"] == 2

    def test_pooled_weights_low_variance_more(self):
        """A precise stratum (small variance) should dominate the pool."""
        precise = CorpusRR(corpus="P", n_events_top=1000, exp_top_days=100.0,
                           n_events_bot=500, exp_bot_days=100.0,
                           rr=2.0, log_rr_var=1.0/1000 + 1.0/500)
        noisy = CorpusRR(corpus="N", n_events_top=2, exp_top_days=100.0,
                         n_events_bot=10, exp_bot_days=100.0,
                         rr=0.2, log_rr_var=1.0/2 + 1.0/10)
        result = _mantel_haenszel_log_rr([precise, noisy])
        # Precise stratum should dominate; pooled ≈ 2.0, not 0.2.
        assert result["rr_pooled"] > 1.5

    def test_cochrans_q_low_when_strata_agree(self):
        """Homogeneous strata → Q_p high (cannot reject homogeneity)."""
        agree1 = CorpusRR(corpus="A", n_events_top=100, exp_top_days=100.0,
                          n_events_bot=50, exp_bot_days=100.0,
                          rr=2.0, log_rr_var=1.0/100 + 1.0/50)
        agree2 = CorpusRR(corpus="B", n_events_top=200, exp_top_days=100.0,
                          n_events_bot=100, exp_bot_days=100.0,
                          rr=2.0, log_rr_var=1.0/200 + 1.0/100)
        result = _mantel_haenszel_log_rr([agree1, agree2])
        assert result["q_p"] > 0.5  # plenty of agreement

    def test_cochrans_q_high_when_strata_disagree(self):
        """Heterogeneous strata → Q_p low (reject homogeneity)."""
        s1 = CorpusRR(corpus="A", n_events_top=200, exp_top_days=100.0,
                      n_events_bot=50, exp_bot_days=100.0,
                      rr=4.0, log_rr_var=1.0/200 + 1.0/50)
        s2 = CorpusRR(corpus="B", n_events_top=50, exp_top_days=100.0,
                      n_events_bot=200, exp_bot_days=100.0,
                      rr=0.25, log_rr_var=1.0/50 + 1.0/200)
        result = _mantel_haenszel_log_rr([s1, s2])
        # Wildly disagreeing strata → Q_p should be very low.
        assert result["q_p"] < 0.05

    def test_empty_input_returns_nan(self):
        """No valid strata → nan-filled result."""
        result = _mantel_haenszel_log_rr([])
        assert math.isnan(result["rr_pooled"])
        assert result["k"] == 0


class TestPerCorpusRR:
    """_per_corpus_rr computes top-vs-bottom quintile RR with exposure."""

    def test_returns_none_when_no_events_at_all(self):
        """No events at all → can't compute RR → None."""
        df = pd.DataFrame({
            "mix_score": [float(i) for i in range(40)],
            "dasha_start_jd": [0.0] * 40,
            "dasha_end_jd": [10.0] * 40,
            "event_marriage": [0] * 40,
        })
        result = _per_corpus_rr(df, event_class="marriage", n_bins=5)
        assert result is None

    def test_rr_exceeds_one_when_high_score_eventful(self):
        """If events cluster in the top score quintile, RR > 1.

        50 rows. Bottom quintile (lowest 10 scores): 1 event.
        Top quintile (highest 10 scores): 5 events.
        Same exposure each → RR top-vs-bottom = 5.0.
        """
        rows = []
        for i in range(50):
            # Top quintile is i ∈ {40..49} after ranking; put 5 events there.
            # Bottom quintile is i ∈ {0..9}; put 1 event there.
            had_event = (i == 0) or (40 <= i < 45)
            rows.append({
                "mix_score": float(i),
                "dasha_start_jd": 0.0,
                "dasha_end_jd": 10.0,
                "event_marriage": 1 if had_event else 0,
            })
        df = pd.DataFrame(rows)
        result = _per_corpus_rr(df, event_class="marriage", n_bins=5)
        assert result is not None
        # Top quintile (5 events) vs bottom (1 event), same exposure → RR=5.
        assert result.rr >= 4.0


class TestBirthJdDedup:
    """ADB > WD > LA precedence when persons share birth_jd."""

    def test_higher_precedence_kept_when_birth_jd_collides(self):
        """Same birth_jd in ADB and WD: keep ADB, drop WD; LA empty kept empty."""
        adb_natal = pd.DataFrame({
            "name_norm": ["agatha"], "birth_jd": [2411626.0931],
        })
        wd_natal = pd.DataFrame({
            "name_norm": ["q35064"], "birth_jd": [2411626.0931],  # same person
        })
        la_natal = pd.DataFrame({
            "name_norm": [], "birth_jd": [],
        })
        dasha_dfs = {
            "ADB": pd.DataFrame({"name_norm": ["agatha"], "birth_jd": [2411626.0931]}),
            "WD":  pd.DataFrame({"name_norm": ["q35064"], "birth_jd": [2411626.0931]}),
            "LA":  pd.DataFrame({"name_norm": [], "birth_jd": []}),
        }
        natal_dfs = {"ADB": adb_natal, "WD": wd_natal, "LA": la_natal}
        out_dasha, out_natal, n_dropped = _dedup_by_birth_jd(dasha_dfs, natal_dfs)
        assert n_dropped == 1
        assert len(out_natal["ADB"]) == 1
        assert len(out_natal["WD"]) == 0  # WD copy dropped

    def test_corpus_precedence_constants_are_canonical(self):
        """ADB > WD > LA per project convention."""
        assert _CORPUS_PRECEDENCE["ADB"] > _CORPUS_PRECEDENCE["WD"]
        assert _CORPUS_PRECEDENCE["WD"] > _CORPUS_PRECEDENCE["LA"]
