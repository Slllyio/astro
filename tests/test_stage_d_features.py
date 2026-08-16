"""Tests for Fork-A Stage D feature pipeline."""
from __future__ import annotations

import pandas as pd
import pytest

from corpus_presence import needs_file

_needs_smoke = needs_file("app/medini/data/dasha_mdadpd_smoke.parquet")
_needs_full = needs_file("app/medini/data/dasha_mdadpd_corpus.parquet")

from app.medini.ml.stage_d_features import (
    QUALIFYING_EVENT_CLASSES,
    load_corpus,
)


class TestQualifyingClasses:
    def test_count_is_30(self) -> None:
        """Spec §1 + Appendix A — K=30 qualifying event classes."""
        assert len(QUALIFYING_EVENT_CLASSES) == 30

    def test_career_and_fame_first(self) -> None:
        """Appendix A is sorted by descending positives; fame=2297 > career=2243."""
        assert QUALIFYING_EVENT_CLASSES[0] == "fame"
        assert QUALIFYING_EVENT_CLASSES[1] == "career"

    def test_no_excluded_classes_present(self) -> None:
        """The 26 excluded classes (e.g., mental_health n=4) must NOT appear."""
        excluded = {"mental_health", "death_by_homicide", "misc.", "mundane"}
        assert excluded.isdisjoint(QUALIFYING_EVENT_CLASSES)


class TestLoadCorpus:
    @_needs_smoke
    def test_load_smoke_returns_dataframe(self) -> None:
        """load_corpus(smoke=True) returns a DataFrame with the leaf-window schema."""
        df = load_corpus(smoke=True)
        assert isinstance(df, pd.DataFrame)
        required_cols = {"name_norm", "md_lord", "ad_lord", "pd_lord",
                         "window_duration_days"}
        assert required_cols.issubset(df.columns)

    @_needs_full
    def test_load_full_returns_dataframe(self) -> None:
        """load_corpus(smoke=False) loads the full mdadpd corpus."""
        df = load_corpus(smoke=False)
        assert len(df) > 0


@_needs_smoke
class TestJoinNatalTensor:
    def test_join_preserves_window_count(self) -> None:
        """Joining natal Vedic Tensor doesn't drop windows (left-join)."""
        from app.medini.ml.stage_d_features import join_natal_vedic_tensor

        corpus = load_corpus(smoke=True)
        joined = join_natal_vedic_tensor(corpus)
        assert len(joined) == len(corpus), "left-join must not drop rows"

    def test_join_adds_vedic_tensor_columns(self) -> None:
        """Tensor adds substantial column count from feature_engineering.

        The Vedic Tensor schema has evolved over time:
          * Legacy ml_astro_features.parquet (14,070 persons): ~199 cols
            (Base 70 + Kinematic 63 + Vedic 50 + meta 10 + a few extras).
          * Full-coverage ml_astro_features_full.parquet (10,239 persons,
            built 2026-05-25): ~530 cols (feature_engineering has gained
            new derived features since the original spec was written).

        Test accepts either schema with a permissive lower bound (must add
        at least the original ~150 cols) and a generous upper bound
        (current full-coverage is 530; allow up to 1000 for future growth).
        """
        from app.medini.ml.stage_d_features import join_natal_vedic_tensor

        corpus = load_corpus(smoke=True)
        joined = join_natal_vedic_tensor(corpus)
        new_cols = set(joined.columns) - set(corpus.columns)
        assert 150 <= len(new_cols) <= 1000, f"got {len(new_cols)} new cols"


@_needs_smoke
class TestActiveDashaEncoding:
    def test_md_lord_one_hot_sums_to_one(self) -> None:
        """Each row has exactly one MD lord one-hot active."""
        from app.medini.ml.stage_d_features import add_active_dasha_encoding

        corpus = load_corpus(smoke=True)
        with_dasha = add_active_dasha_encoding(corpus)
        md_one_hots = [c for c in with_dasha.columns if c.startswith("md_lord_is_")]
        assert len(md_one_hots) == 9, "Vimshottari has 9 lords"
        # Each row sums to exactly 1 across the MD one-hots.
        assert (with_dasha[md_one_hots].sum(axis=1) == 1).all()

    def test_n_relevant_lords_is_0_to_3(self) -> None:
        """The 'n_relevant_lords_career' rate-ladder column is in {0,1,2,3}."""
        from app.medini.ml.stage_d_features import add_active_dasha_encoding

        corpus = load_corpus(smoke=True)
        with_dasha = add_active_dasha_encoding(corpus)
        col = "n_relevant_lords_career"
        assert col in with_dasha.columns
        assert with_dasha[col].between(0, 3).all()

    def test_ad_lord_one_hot_sums_to_one(self) -> None:
        """Each row has exactly one AD lord one-hot active (parity with MD test)."""
        from app.medini.ml.stage_d_features import add_active_dasha_encoding

        corpus = load_corpus(smoke=True)
        with_dasha = add_active_dasha_encoding(corpus)
        ad_one_hots = [c for c in with_dasha.columns if c.startswith("ad_lord_is_")]
        assert len(ad_one_hots) == 9
        assert (with_dasha[ad_one_hots].sum(axis=1) == 1).all()

    def test_pd_lord_one_hot_sums_to_one(self) -> None:
        """Each row has exactly one PD lord one-hot active (parity with MD test)."""
        from app.medini.ml.stage_d_features import add_active_dasha_encoding

        corpus = load_corpus(smoke=True)
        with_dasha = add_active_dasha_encoding(corpus)
        pd_one_hots = [c for c in with_dasha.columns if c.startswith("pd_lord_is_")]
        assert len(pd_one_hots) == 9
        assert (with_dasha[pd_one_hots].sum(axis=1) == 1).all()

    def test_empty_attribution_emits_all_zeros(self) -> None:
        """Classes with no classical attribution ('personal', 'general') emit 0."""
        from app.medini.ml.stage_d_features import add_active_dasha_encoding

        corpus = load_corpus(smoke=True)
        with_dasha = add_active_dasha_encoding(corpus)
        assert (with_dasha["n_relevant_lords_personal"] == 0).all()
        assert (with_dasha["n_relevant_lords_general"] == 0).all()


@_needs_smoke
class TestActiveYogas:
    def test_natal_strength_cols_present(self) -> None:
        """Each of 16 yogas contributes a `<yoga>_natal_strength` col."""
        from app.medini.ml.stage_d_features import (
            add_yoga_features_with_dasha_gating,
            YOGA_NAMES,
        )

        assert len(YOGA_NAMES) == 16
        corpus = load_corpus(smoke=True)
        with_yogas = add_yoga_features_with_dasha_gating(corpus)
        for yoga in YOGA_NAMES:
            assert f"{yoga}_natal_strength" in with_yogas.columns

    def test_dasha_active_is_binary(self) -> None:
        """`<yoga>_dasha_active` is 0/1 per window."""
        from app.medini.ml.stage_d_features import (
            add_yoga_features_with_dasha_gating,
            YOGA_NAMES,
        )

        corpus = load_corpus(smoke=True)
        with_yogas = add_yoga_features_with_dasha_gating(corpus)
        for yoga in YOGA_NAMES:
            col = f"{yoga}_dasha_active"
            assert set(with_yogas[col].unique()).issubset({0, 1})

    def test_moon_configurational_yogas_have_zero_dasha_active(self) -> None:
        """Sunapha/Anapha/Durudhura/Kemadruma are Moon-configurational
        (not lord-gated); their dasha_active column is intentionally all 0
        (see docstring on _YOGA_PLANETS)."""
        from app.medini.ml.stage_d_features import add_yoga_features_with_dasha_gating

        corpus = load_corpus(smoke=True)
        with_yogas = add_yoga_features_with_dasha_gating(corpus)
        for yoga in ("sunapha", "anapha", "durudhura", "kemadruma"):
            assert (with_yogas[f"{yoga}_dasha_active"] == 0).all()


@_needs_smoke
class TestStageEFeatures:
    def test_lord_house_columns_present(self) -> None:
        """Stage-E adds 'rules_<planet>', 'occ_<planet>', 'aspects_<planet>' cols."""
        from app.medini.ml.stage_d_features import add_stage_e_features

        corpus = load_corpus(smoke=True)
        with_e = add_stage_e_features(corpus)
        for planet in ("sun", "moon", "saturn", "jupiter"):
            assert f"rules_{planet}" in with_e.columns
            assert f"occ_{planet}" in with_e.columns
            assert f"aspects_{planet}" in with_e.columns

    def test_doctrine_score_per_class_or_skipped(self) -> None:
        """Doctrine parquet is OPTIONAL (spec §2). When present, adds 30 cols.
        When absent, add_doctrine_scores is a no-op and the test is skipped."""
        from pathlib import Path
        import pytest
        from app.medini.ml.stage_d_features import (
            add_doctrine_scores, _DOCTRINE_PARQUET, QUALIFYING_EVENT_CLASSES,
        )

        if not _DOCTRINE_PARQUET.exists():
            pytest.skip(
                f"Optional doctrine parquet missing at {_DOCTRINE_PARQUET}; "
                "add_doctrine_scores is a documented no-op (returns df unchanged)."
            )
        corpus = load_corpus(smoke=True)
        with_doc = add_doctrine_scores(corpus)
        for cls in QUALIFYING_EVENT_CLASSES:
            assert f"doctrine_score_{cls}" in with_doc.columns

    def test_doctrine_no_op_returns_unchanged(self) -> None:
        """When doctrine parquet is absent, add_doctrine_scores returns df unchanged."""
        from app.medini.ml.stage_d_features import add_doctrine_scores, _DOCTRINE_PARQUET

        if _DOCTRINE_PARQUET.exists():
            # Doctrine parquet exists; this test would not apply. Skip cleanly.
            import pytest
            pytest.skip("doctrine parquet present; no-op behavior only relevant when absent")
        corpus = load_corpus(smoke=True)
        out = add_doctrine_scores(corpus)
        # Same shape, same columns.
        assert out.shape == corpus.shape
        assert list(out.columns) == list(corpus.columns)


@_needs_smoke
class TestMaterialize:
    # Corpus-level metadata that's expected to be in the materialized parquet.
    # These are NOT feature-leak — they're consumed by stage_d_dataset.py
    # for label construction and censoring time, not selected as features.
    _CORPUS_METADATA_JD_COLS: tuple[str, ...] = (
        "birth_jd", "window_start_jd", "window_end_jd",
    )

    def test_no_unexpected_jd_columns_in_materialized_parquet(self) -> None:
        """F3 in spec §6 — no `*_jd` columns beyond the known corpus metadata
        should appear in the materialized parquet (would signal feature leak)."""
        from app.medini.ml.stage_d_features import materialize

        out = materialize(smoke=True, write=False)
        unexpected_jd = [
            c for c in out.columns
            if c.endswith("_jd") and c not in self._CORPUS_METADATA_JD_COLS
        ]
        assert not unexpected_jd, f"unexpected JD cols (potential leak): {unexpected_jd}"

    def test_no_death_feature_columns(self) -> None:
        """F3 in spec §6 — no `death*` columns may be features, EXCEPT the
        `event_death_*` label columns which are legitimate (they're per-class
        labels, used by stage_d_dataset.py to build the survival event vector)."""
        from app.medini.ml.stage_d_features import materialize

        out = materialize(smoke=True, write=False)
        forbidden = [
            c for c in out.columns
            if c.startswith("death") and not c.startswith("event_")
        ]
        assert not forbidden, f"forbidden death-feature cols: {forbidden}"

    def test_smoke_has_positive_class_coverage(self) -> None:
        """Sub-gate D.0 (smoke approximation) — at least 60% of qualifying
        classes have ≥1 positive in the 100-person smoke corpus.

        Why 60% (not 80% or 100%): the smoke corpus samples just 100 persons,
        so rare classes (e.g., death_of_father n=69 in full → expected <1 in
        smoke) legitimately land at 0. The 60% threshold catches catastrophic
        failures (smoke parquet truncated or corrupted) without flagging the
        ~11 naturally-zero classes. Full sub-gate D.0 — requiring all 30
        classes present — is checked separately on the FULL materialized
        parquet (run `py -3.12 -m app.medini.ml.stage_d_features` without
        --smoke to verify)."""
        from app.medini.ml.stage_d_features import (
            materialize, QUALIFYING_EVENT_CLASSES,
        )

        out = materialize(smoke=True, write=False)
        for cls in QUALIFYING_EVENT_CLASSES:
            assert f"event_{cls}" in out.columns, f"missing label column: event_{cls}"

        coverage = [
            (cls, int(out[f"event_{cls}"].sum())) for cls in QUALIFYING_EVENT_CLASSES
        ]
        nonzero = sum(1 for _, n in coverage if n >= 1)
        total = len(QUALIFYING_EVENT_CLASSES)
        zero_classes = [cls for cls, n in coverage if n == 0]
        # 60% floor: catches gross failures while tolerating the 11 known
        # zero-classes in the 100-person smoke cohort.
        assert nonzero / total >= 0.60, (
            f"only {nonzero}/{total} ({100*nonzero/total:.0f}%) classes "
            f"have ≥1 positive in smoke; zero-classes: {zero_classes}"
        )
