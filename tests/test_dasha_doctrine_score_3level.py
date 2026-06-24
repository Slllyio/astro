"""Unit tests for app.medini.ml.dasha_doctrine_score_3level.

Pins the §5.8 multi-layer formula end-to-end:
  * exponent constants W_MD, W_AD, W_PD sum to 1.0
  * multi_layer_relevance clips negatives to 0 (both-witnesses-agree)
  * single zero layer collapses the product
  * symmetric layer ordering changes weight (MD weighted highest)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.medini.ml.dasha_doctrine_score_3level import (
    W_AD,
    W_MD,
    W_PD,
    _annotate_with_multi_relevance,
    additive_relevance,
    multi_layer_relevance,
)


class TestConstants:
    def test_exponents_sum_to_one(self) -> None:
        """Per BPHS 47.10 / §5.8 — exponents are temporal-importance weights
        that must sum to 1. Lock this in case someone tweaks them later."""
        assert W_MD + W_AD + W_PD == pytest.approx(1.0)

    def test_md_dominates(self) -> None:
        """MD layer carries the principal weight per BPHS 47.10."""
        assert W_MD > W_AD > W_PD


class TestMultiLayerRelevance:
    def test_all_positive_layers_combine(self) -> None:
        """Smoke: all three layers positive → finite positive product."""
        md = np.array([4.0])
        ad = np.array([2.0])
        pd = np.array([1.0])
        out = multi_layer_relevance(md, ad, pd)
        expected = 4.0 ** W_MD * 2.0 ** W_AD * 1.0 ** W_PD
        assert out[0] == pytest.approx(expected)

    def test_negative_layer_clipped_to_zero_collapses_product(self) -> None:
        """The 'both-witnesses-agree' rule: any negative-relevance layer
        drives the composite to zero (no imaginary numbers from negative
        bases with fractional exponents)."""
        md = np.array([4.0])
        ad = np.array([-0.5])
        pd = np.array([1.0])
        out = multi_layer_relevance(md, ad, pd)
        assert out[0] == 0.0

    def test_zero_layer_collapses_product(self) -> None:
        """A lord uninvolved with the event class (R=0) should collapse
        the product — that's the natural semantics, not a bug."""
        md = np.array([4.0])
        ad = np.array([0.0])
        pd = np.array([1.0])
        out = multi_layer_relevance(md, ad, pd)
        assert out[0] == 0.0

    def test_layer_weight_ordering_matches_doctrine(self) -> None:
        """Swapping MD and PD relevance values should change the composite
        because W_MD > W_PD. Pin this so a constants edit doesn't quietly
        flip the layer hierarchy."""
        # Case A: MD high, PD low
        a = multi_layer_relevance(
            np.array([8.0]), np.array([2.0]), np.array([1.0]),
        )
        # Case B: MD low, PD high (everything else equal)
        b = multi_layer_relevance(
            np.array([1.0]), np.array([2.0]), np.array([8.0]),
        )
        assert a[0] > b[0], (
            f"MD-weighted relevance should exceed PD-weighted: {a[0]} vs {b[0]}"
        )

    def test_vectorized_over_arrays(self) -> None:
        """Function must handle batched arrays (not just single-element)."""
        md = np.array([4.0, 1.0, 0.0])
        ad = np.array([2.0, 2.0, 5.0])
        pd = np.array([1.0, 0.0, 1.0])
        out = multi_layer_relevance(md, ad, pd)
        assert len(out) == 3
        assert out[1] == 0.0  # ad=2, pd=0 → collapses
        assert out[2] == 0.0  # md=0 → collapses


class TestAdditiveRelevance:
    """Additive combiner — Phaladeepika 15 'AD modifies, doesn't trigger'."""

    def test_pure_md_signal_passes_through(self) -> None:
        """When AD and PD are 0, additive composite is W_MD * R_md.
        Earlier product combiner collapsed this to 0 — fixed here."""
        md = np.array([4.0])
        ad = np.array([0.0])
        pd = np.array([0.0])
        out = additive_relevance(md, ad, pd)
        assert out[0] == pytest.approx(W_MD * 4.0)

    def test_negative_layer_clipped_to_zero_not_canceling(self) -> None:
        """An obstructive lord (negative R) contributes 0 to the sum,
        rather than canceling the MD layer."""
        md = np.array([4.0])
        ad = np.array([-0.5])
        pd = np.array([1.0])
        out = additive_relevance(md, ad, pd)
        expected = W_MD * 4.0 + W_AD * 0.0 + W_PD * 1.0
        assert out[0] == pytest.approx(expected)

    def test_layer_weight_ordering(self) -> None:
        """Same total relevance distributed differently — MD-weighted
        should rank higher because W_MD > W_PD."""
        a = additive_relevance(
            np.array([8.0]), np.array([1.0]), np.array([1.0]),
        )
        b = additive_relevance(
            np.array([1.0]), np.array([1.0]), np.array([8.0]),
        )
        assert a[0] > b[0]

    def test_no_zero_collapse_unlike_product(self) -> None:
        """For typical inputs (MD nonzero, AD or PD zero), additive
        produces a positive composite while product gives 0. This is the
        whole reason the additive variant exists."""
        md = np.array([2.0])
        ad = np.array([0.0])
        pd = np.array([3.0])
        add = additive_relevance(md, ad, pd)
        prod = multi_layer_relevance(md, ad, pd)
        assert add[0] > 0.0
        assert prod[0] == 0.0


class TestAnnotation:
    """End-to-end annotation on a synthetic 3-level df."""

    def test_annotate_adds_four_columns(self) -> None:
        """Output has md_relevance, ad_relevance, pd_relevance, relevance_full."""
        # Synthetic 1-row mdadpd df
        mdadpd_df = pd.DataFrame([{
            "name_norm": "test_person",
            "md_lord": "Jupiter", "ad_lord": "Venus", "pd_lord": "Moon",
            "window_start_jd": 0.0, "window_end_jd": 10.0,
            "event_fame": 0,
        }])
        # Synthetic natal row — Jupiter rules 10H (fame house), Venus is a
        # fame karaka? actually karaka_map["fame"] = {Sun, Jupiter}.
        natal_df = pd.DataFrame([{
            "name_norm": "test_person",
            "rules_jupiter": [10], "occ_jupiter": -1, "aspects_jupiter": [],
            "rules_venus": [2, 7], "occ_venus": -1, "aspects_venus": [],
            "rules_moon": [4], "occ_moon": -1, "aspects_moon": [],
            "rules_sun": [], "occ_sun": -1, "aspects_sun": [],
            "rules_mars": [], "occ_mars": -1, "aspects_mars": [],
            "rules_mercury": [], "occ_mercury": -1, "aspects_mercury": [],
            "rules_saturn": [], "occ_saturn": -1, "aspects_saturn": [],
            "rules_rahu": [], "occ_rahu": -1, "aspects_rahu": [],
            "rules_ketu": [], "occ_ketu": -1, "aspects_ketu": [],
        }])
        out = _annotate_with_multi_relevance(mdadpd_df, natal_df, "fame")
        assert set(["md_relevance", "ad_relevance",
                    "pd_relevance", "relevance_full"]) <= set(out.columns)
        # MD = Jupiter rules 10H (fame primary, w=1.0) + Jupiter karaka (w=1.0)
        # → md_relevance = 1.0 (lordship channel) * 1.0 (house weight) + 1.0 (karaka)
        # plus functional_modifier (Jupiter rules only 10H, kendra non-1 → 0)
        # = 2.0
        assert out["md_relevance"].iloc[0] == pytest.approx(2.0, abs=0.5)
        # AD = Venus, karaka_map["fame"] = {Sun, Jupiter} → Venus not karaka
        # Venus rules 2H + 7H, no fame-house overlap, no karaka. functional_mod
        # for Venus ruling 2/7 = kendra/upachaya non-1 → 0
        # ad_relevance = 0
        assert out["ad_relevance"].iloc[0] == pytest.approx(0.0, abs=0.5)
        # PD = Moon, Moon rules 4H, no overlap with fame houses {10,1,5,11},
        # no karaka → 0. So composite collapses.
        assert out["pd_relevance"].iloc[0] == pytest.approx(0.0, abs=0.5)
        assert out["relevance_full"].iloc[0] == 0.0
