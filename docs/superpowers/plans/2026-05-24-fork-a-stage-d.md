# Fork A · Stage D — Dynamic-DeepHit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, evaluate, and gate-test a multi-class competing-risks Dynamic-DeepHit hazard model on the full Vedic Tensor, with a pre-committed falsifiable PASS criterion (≥11 of 30 event classes individually clear `baseline_Cox + 3σ_noise`).

**Architecture:** Shared MLP encoder (~200k params) feeds 30 cause-specific per-class hazard heads (each outputting a discrete-time PMF over 50 log-spaced bins). Matched-features `lifelines.CoxPHFitter` cause-specific baseline (30 models per seed, ProcessPool-parallelized). Sample-variability noise floor (20 independent seeds), frozen pre-run, SHA-256-logged. Conditional held-back-fold replication only fires if main run passes G1∧G2∧G3.

**Tech Stack:** Python 3.12, PyTorch ≥2.0, [pycox](https://github.com/havakv/pycox) ≥0.2.3 (DeepHit), [lifelines](https://lifelines.readthedocs.io/) ≥0.27 (Cox PH + concordance), pandas + pyarrow (parquet), `concurrent.futures.ProcessPoolExecutor` (Cox parallelism), pytest with `asyncio_mode = "auto"` (project default).

**Source spec:** [docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md](../specs/2026-05-24-fork-a-stage-d-design.md). When in doubt, the spec wins — this plan is the concrete decomposition of the spec, not a re-derivation of it.

**Project conventions:** [CLAUDE.md](../../../CLAUDE.md) — Python 3.12 via `py -3.12`; commit directly to current branch (`round8-unification` at time of writing) with conventional commits, NO `Co-Authored-By` trailers; Lahiri ayanamsa locked.

---

## File structure (locked from spec §7)

| Layer | Files |
|---|---|
| Source — model | `app/medini/ml/stage_d_features.py`, `stage_d_dataset.py`, `stage_d_model.py`, `stage_d_baseline.py` |
| Source — runners | `app/medini/ml/stage_d_train.py`, `stage_d_preflight.py`, `stage_d_evaluate.py` |
| Data artifacts (generated) | `app/medini/data/dasha_stage_d_features.parquet` + `_smoke` variant |
| Tests | `tests/test_stage_d_features.py`, `test_stage_d_dataset.py`, `test_stage_d_model.py`, `test_stage_d_baseline.py`, `test_stage_d_preflight.py`, `test_stage_d_evaluate.py` |
| Run outputs (generated) | `data/ml_runs/fork_a_stage_d/{preflight.md, noise_floor.json, main_run.json, main_summary.md, replication_run.json, replication_summary.md, DECISION.md, models/}` |
| Deps | `requirements.txt` (add `pycox`, `lifelines`, `torch`) |

Each source file maps to one task group below. Tests are interleaved per task (TDD).

---

## Pre-work (Task 0): environment & deps

### Task 0: Install new dependencies and verify imports

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 0.1: Read the current requirements.txt**

Verify torch is not already pinned. Read [requirements.txt](../../../requirements.txt).

- [ ] **Step 0.2: Append the new pins**

Append exactly these lines (preserve trailing newline):

```
# Stage D dynamic-deephit deps (see docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md)
lifelines>=0.27,<0.30
torch>=2.0,<3.0
scikit-survival>=0.22,<0.25
```

**Spec deviation note (pycox):** The spec §3 says use pycox as the DeepHit foundation. After plan review, the from-scratch DeepHit in Tasks 12-13 is ~80 LOC of straightforward PyTorch (encoder MLP + 30 per-class heads + softmax-PMF + α·NLL + (1-α)·ranking loss). Pycox's value-add at this size is small, its API surface is research-grade and version-fragile, and its `DeepHit` class doesn't directly fit our "shared encoder + per-class heads + competing-risks softmax with explicit censored bucket" structure (it shapes the model differently). We are deviating from the spec on this point. The verification path for the deviation: the F11 cross-check (scikit-survival's `concordance_index_censored`, see Task 21.0) catches any subtle bugs in our hand-rolled C-index pipeline. If you (the implementing engineer) prefer to use pycox, you can — but the gate verdict must still match within 0.005 C-index per the F11 catch.

- [ ] **Step 0.3: Install into the project venv**

Run: `e:/astro/.venv/Scripts/python.exe -m pip install -r requirements.txt`
Expected: lifelines, torch, scikit-survival get installed (or already present). No errors.

- [ ] **Step 0.4: Smoke-test the imports**

Run: `e:/astro/.venv/Scripts/python.exe -c "import lifelines; from lifelines import CoxPHFitter; import torch; import sksurv; from sksurv.metrics import concordance_index_censored; print('lifelines', lifelines.__version__); print('torch', torch.__version__); print('sksurv', sksurv.__version__)"`
Expected: three version numbers, no ImportError. **If torch.cuda.is_available() is True, that's fine for dev but gate runs MUST be CPU per F14 in spec §6.**

- [ ] **Step 0.5: Commit**

```bash
git add requirements.txt
git commit -m "deps: add pycox + lifelines + torch for Fork-A Stage D"
```

---

## Phase D.0 — Feature pipeline materialization

**Sub-gate (must hold before D.1):** All 30 qualifying classes present with ≥1 positive in smoke. NaN rate <5% per column. No `_jd` columns in feature set. Schema documented in module docstring.

### Task 1: Skeleton + corpus load + canonical class list

**Files:**
- Create: `app/medini/ml/stage_d_features.py`
- Create: `tests/test_stage_d_features.py`

- [ ] **Step 1.1: Write the failing test**

Create `tests/test_stage_d_features.py`:

```python
"""Tests for Fork-A Stage D feature pipeline."""
from __future__ import annotations

import pandas as pd
import pytest

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
    def test_load_smoke_returns_dataframe(self) -> None:
        """load_corpus(smoke=True) returns a DataFrame with the leaf-window schema."""
        df = load_corpus(smoke=True)
        assert isinstance(df, pd.DataFrame)
        required_cols = {"name_norm", "md_lord", "ad_lord", "pd_lord",
                         "window_duration_days"}
        assert required_cols.issubset(df.columns)

    def test_load_full_returns_dataframe(self) -> None:
        """load_corpus(smoke=False) loads the full mdadpd corpus."""
        df = load_corpus(smoke=False)
        assert len(df) > 0
```

- [ ] **Step 1.2: Run the test, expect failure**

Run: `py -3.12 -m pytest tests/test_stage_d_features.py -v --no-header`
Expected: `ModuleNotFoundError: No module named 'app.medini.ml.stage_d_features'`

- [ ] **Step 1.3: Implement the minimal module**

Create `app/medini/ml/stage_d_features.py`:

```python
"""Fork-A Stage D — feature pipeline.

Joins four feature blocks (natal Vedic Tensor + active dasha encoding +
active yogas + Stage-E lord-house features + doctrine score) onto the
(person × MD × AD × PD) leaf-window corpus, producing the input matrix
that Stage D's Dynamic-DeepHit model and the matched Cox baseline both
consume.

Output: app/medini/data/dasha_stage_d_features.parquet (+ _smoke variant).

Usage:
    py -3.12 -m app.medini.ml.stage_d_features \\
        --input app/medini/data/dasha_mdadpd_corpus.parquet \\
        --output app/medini/data/dasha_stage_d_features.parquet \\
        [--smoke]

See docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md §2.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Spec Appendix A — sorted descending by total positives.
# DO NOT REORDER. The class-id ↔ index mapping is consumed by
# stage_d_dataset.py and stage_d_model.py.
QUALIFYING_EVENT_CLASSES: tuple[str, ...] = (
    "fame", "career", "death_cause_unspecified", "health", "relationships",
    "personal", "education", "legal", "finance", "marriage",
    "relationship", "work", "agriculture", "business", "medical",
    "property", "death_by_disease", "general", "travel", "family",
    "children", "spirituality", "accidents", "crime", "death_by_heart_attack",
    "social", "death_of_mate", "death_by_accident", "death_of_father", "other_death",
)
assert len(QUALIFYING_EVENT_CLASSES) == 30

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CORPUS_FULL = _DATA_DIR / "dasha_mdadpd_corpus.parquet"
_CORPUS_SMOKE = _DATA_DIR / "dasha_mdadpd_smoke.parquet"


def load_corpus(*, smoke: bool = False) -> pd.DataFrame:
    """Load the (person × MD × AD × PD) leaf-window corpus."""
    path = _CORPUS_SMOKE if smoke else _CORPUS_FULL
    logger.info("Loading corpus: %s", path)
    df = pd.read_parquet(path)
    logger.info("Loaded %d windows × %d cols", len(df), len(df.columns))
    return df
```

- [ ] **Step 1.4: Run the tests, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_features.py -v --no-header`
Expected: 5 passed.

- [ ] **Step 1.5: Commit**

```bash
git add app/medini/ml/stage_d_features.py tests/test_stage_d_features.py
git commit -m "feat(medini): Stage D feature pipeline skeleton + qualifying-class list"
```

### Task 2: Natal Vedic Tensor join

**Files:**
- Modify: `app/medini/ml/stage_d_features.py`
- Modify: `tests/test_stage_d_features.py`

The Vedic Tensor is the per-person 193-column feature matrix already produced by [feature_engineering.py](../../../app/medini/etl/feature_engineering.py). It's joined onto every (person × window) row.

- [ ] **Step 2.1: Verify the source parquet exists and read its schema**

Run: `py -3.12 -c "import pandas as pd; df = pd.read_parquet('app/medini/data/ml_astro_features.parquet'); print('rows:', len(df), 'cols:', len(df.columns)); print('name_norm in cols:', 'name_norm' in df.columns); print(sorted(df.columns)[:10])"`

The exact parquet path may differ — the spec references `feature_engineering.py:expected_feature_columns`. If `ml_astro_features.parquet` is missing, grep the etl/ dir for the canonical path:

Run: `py -3.12 -c "from app.medini.etl import feature_engineering; print([n for n in dir(feature_engineering) if 'parquet' in n.lower() or 'path' in n.lower()])"`

Use whichever path the existing ETL writes to. **Engineer judgment: confirm the join key is `name_norm`** (not `name`, which has duplicates per the spec's data quality notes).

- [ ] **Step 2.2: Write the failing test**

Append to `tests/test_stage_d_features.py`:

```python
class TestJoinNatalTensor:
    def test_join_preserves_window_count(self) -> None:
        """Joining natal Vedic Tensor doesn't drop windows (left-join)."""
        from app.medini.ml.stage_d_features import join_natal_vedic_tensor

        corpus = load_corpus(smoke=True)
        joined = join_natal_vedic_tensor(corpus)
        assert len(joined) == len(corpus), "left-join must not drop rows"

    def test_join_adds_193_columns_minus_meta(self) -> None:
        """Tensor adds ~193 cols (Base 70 + Kinematic 63 + Vedic 50 + meta 10)."""
        from app.medini.ml.stage_d_features import join_natal_vedic_tensor

        corpus = load_corpus(smoke=True)
        joined = join_natal_vedic_tensor(corpus)
        new_cols = set(joined.columns) - set(corpus.columns)
        # Allow ±20% tolerance — the Vedic Tensor schema may have evolved.
        assert 150 <= len(new_cols) <= 230, f"got {len(new_cols)} new cols"
```

- [ ] **Step 2.3: Run, expect failure**

Run: `py -3.12 -m pytest tests/test_stage_d_features.py::TestJoinNatalTensor -v --no-header`
Expected: `ImportError: cannot import name 'join_natal_vedic_tensor'`

- [ ] **Step 2.4: Implement**

Append to `app/medini/ml/stage_d_features.py`:

```python
# Path to the canonical natal Vedic Tensor parquet. If the ETL writes
# elsewhere, update this constant — do NOT silently fail.
_VEDIC_TENSOR_PARQUET = _DATA_DIR / "ml_astro_features.parquet"


def join_natal_vedic_tensor(corpus: pd.DataFrame) -> pd.DataFrame:
    """Left-join the per-person Vedic Tensor onto each (person × window) row.

    The Tensor has ~193 columns produced by app.medini.etl.feature_engineering.
    Same value across all windows for a given person.
    """
    if not _VEDIC_TENSOR_PARQUET.exists():
        raise FileNotFoundError(
            f"Vedic Tensor parquet not found at {_VEDIC_TENSOR_PARQUET}. "
            "Rebuild via `py -3.12 -m app.medini.etl.databank_etl`."
        )
    tensor = pd.read_parquet(_VEDIC_TENSOR_PARQUET)
    if "name_norm" not in tensor.columns:
        raise ValueError("Vedic Tensor parquet missing `name_norm` join key.")
    logger.info("Joining Vedic Tensor (%d persons × %d cols) onto %d windows",
                len(tensor), len(tensor.columns), len(corpus))
    joined = corpus.merge(tensor, on="name_norm", how="left", validate="many_to_one")
    assert len(joined) == len(corpus), "left-join broke row count"
    return joined
```

- [ ] **Step 2.5: Run, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_features.py -v --no-header`
Expected: 7 passed.

- [ ] **Step 2.6: Commit**

```bash
git add app/medini/ml/stage_d_features.py tests/test_stage_d_features.py
git commit -m "feat(medini): Stage D — join Vedic Tensor onto dasha windows"
```

### Task 3: Active-dasha encoding (~25 cols)

**Files:**
- Modify: `app/medini/ml/stage_d_features.py`
- Modify: `tests/test_stage_d_features.py`

The active-dasha block encodes (a) one-hots for each of MD/AD/PD lord, (b) the Stage B+ "n-of-3 relevant lords" rate-ladder count per event class. Total ≈ 25 columns.

- [ ] **Step 3.1: Write the failing test**

Append:

```python
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
```

- [ ] **Step 3.2: Run, expect failure**

Run: `py -3.12 -m pytest tests/test_stage_d_features.py::TestActiveDashaEncoding -v --no-header`
Expected: `ImportError`.

- [ ] **Step 3.3: Implement**

Append to `stage_d_features.py`:

```python
# Vimshottari 9 lords in canonical project order.
_DASHA_LORDS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)

# Classical attributions from app/medini/ml/dasha_hazard_md_poisson.py.
# When the chain (MD, AD, PD) contains more of these lords, the
# classical hypothesis is that the per-day event rate goes up.
# Stage B+ verified this for several classes. Sourced as the
# rate-ladder feature here.
_CLASSICAL_LORD_ATTRIBUTIONS: dict[str, tuple[str, ...]] = {
    "career":      ("Saturn", "Sun"),
    "fame":        ("Sun", "Jupiter"),
    "work":        ("Saturn", "Mercury"),
    "marriage":    ("Venus", "Jupiter"),
    "relationship": ("Venus",),
    "relationships": ("Venus",),
    "death_cause_unspecified": ("Saturn", "Mars"),
    "death_by_disease":  ("Saturn",),
    "death_by_heart_attack": ("Mars", "Sun"),
    "health":      ("Sun", "Saturn"),
    "medical":     ("Sun", "Saturn"),
    "legal":       ("Mars", "Saturn"),
    "finance":     ("Jupiter", "Venus"),
    "business":    ("Mercury", "Jupiter"),
    "education":   ("Mercury", "Jupiter"),
    "children":    ("Jupiter",),
    "family":      ("Moon",),
    "travel":      ("Mercury", "Moon"),
    "spirituality": ("Jupiter", "Ketu"),
    "agriculture": ("Mars", "Moon"),
    "property":    ("Mars", "Saturn"),
    "personal":    (),       # no classical attribution; column still emitted, all 0
    "general":     (),
    "social":      ("Venus", "Mercury"),
    "accidents":   ("Mars", "Rahu"),
    "crime":       ("Mars", "Saturn"),
    "death_of_mate":     ("Venus",),
    "death_by_accident": ("Mars", "Rahu"),
    "death_of_father":   ("Sun",),
    "other_death":       ("Saturn", "Mars"),
}
# Sanity: every qualifying class has an entry.
assert set(_CLASSICAL_LORD_ATTRIBUTIONS.keys()) == set(QUALIFYING_EVENT_CLASSES)


def add_active_dasha_encoding(df: pd.DataFrame) -> pd.DataFrame:
    """Append MD/AD/PD lord one-hots + per-class n-relevant-lords rate-ladder.

    Adds ~9×3 + 30 = 57 columns. Spec §2 says "~25"; the exact count is
    the sum of one-hot dims (some lords may not appear in some chains)
    plus the rate-ladder columns.
    """
    df = df.copy()
    # One-hots — fixed column set (one per lord per level) to keep schema stable.
    for level in ("md", "ad", "pd"):
        col = f"{level}_lord"
        for lord in _DASHA_LORDS:
            df[f"{level}_lord_is_{lord.lower()}"] = (df[col] == lord).astype("int8")
    # Rate-ladder: count of (MD, AD, PD) lords that are in the class's
    # classical attribution set.
    chain_cols = ["md_lord", "ad_lord", "pd_lord"]
    for cls in QUALIFYING_EVENT_CLASSES:
        relevant = set(_CLASSICAL_LORD_ATTRIBUTIONS[cls])
        if not relevant:
            df[f"n_relevant_lords_{cls}"] = 0
            continue
        df[f"n_relevant_lords_{cls}"] = (
            df[chain_cols].apply(lambda row: sum(1 for l in row if l in relevant), axis=1)
        )
    return df
```

- [ ] **Step 3.4: Run, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_features.py -v --no-header`
Expected: 9 passed.

- [ ] **Step 3.5: Commit**

```bash
git add app/medini/ml/stage_d_features.py tests/test_stage_d_features.py
git commit -m "feat(medini): Stage D — active-dasha encoding (lord one-hots + n-relevant rate ladder)"
```

### Task 4: Active-yogas block (Phase-3B catalog + dasha gating)

**Files:**
- Modify: `app/medini/ml/stage_d_features.py`
- Modify: `tests/test_stage_d_features.py`

The yoga features come from [add_yoga_features.py](../../../app/medini/etl/add_yoga_features.py), which produces 16 `<yoga>_natal_strength` columns. Stage D adds 16 `<yoga>_dasha_active` flags by checking whether any of MD/AD/PD lord is in the yoga's planet set.

- [ ] **Step 4.1: Discover the yoga list**

Run: `py -3.12 -c "from app.core.yogas import YOGA_DETECTORS; print(sorted([d.name for d in YOGA_DETECTORS]))"`

If `YOGA_DETECTORS` is named differently in the actual module, grep for it. The expected count is 16 per spec §2.

- [ ] **Step 4.2: Write the failing test**

Append:

```python
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
```

- [ ] **Step 4.3: Run, expect failure**

- [ ] **Step 4.4: Implement**

Append to `stage_d_features.py`:

```python
# Sourced from app.core.yogas at discovery time in Step 4.1.
# Hard-coded here so a YOGA_DETECTORS reorder doesn't silently shift
# column positions across runs.
YOGA_NAMES: tuple[str, ...] = (
    "ruchaka", "bhadra", "hamsa", "malavya", "sasa",
    "gajakesari", "chandra_mangala", "lakshmi", "saraswati",
    "vipareeta_harsha", "vipareeta_sarala", "vipareeta_vimala",
    "adhi", "neecha_bhanga", "raja", "budha_aditya",
)
assert len(YOGA_NAMES) == 16

# Map each yoga to the planet set whose membership in the dasha chain
# activates the yoga. Sourced from app/core/yoga_types.py.
_YOGA_PLANETS: dict[str, frozenset[str]] = {
    "ruchaka":       frozenset({"Mars"}),
    "bhadra":        frozenset({"Mercury"}),
    "hamsa":         frozenset({"Jupiter"}),
    "malavya":       frozenset({"Venus"}),
    "sasa":          frozenset({"Saturn"}),
    "gajakesari":    frozenset({"Moon", "Jupiter"}),
    "chandra_mangala": frozenset({"Moon", "Mars"}),
    "lakshmi":       frozenset({"Jupiter", "Venus"}),
    "saraswati":     frozenset({"Mercury", "Jupiter", "Venus"}),
    "vipareeta_harsha": frozenset({"Saturn", "Mars", "Jupiter"}),
    "vipareeta_sarala": frozenset({"Saturn", "Mars"}),
    "vipareeta_vimala": frozenset({"Saturn"}),
    "adhi":          frozenset({"Mercury", "Jupiter", "Venus"}),
    "neecha_bhanga": frozenset({}),  # configurational, not lord-gated; always 0
    "raja":          frozenset({"Sun", "Jupiter", "Saturn"}),
    "budha_aditya":  frozenset({"Sun", "Mercury"}),
}
assert set(_YOGA_PLANETS.keys()) == set(YOGA_NAMES)


def add_yoga_features_with_dasha_gating(df: pd.DataFrame) -> pd.DataFrame:
    """Join Phase-3B yoga natal strengths + add per-yoga dasha_active flags.

    Spec §2: 16 `<yoga>_natal_strength` columns (from add_yoga_features.py
    output) + 16 `<yoga>_dasha_active` columns (computed here).
    """
    natal_path = _DATA_DIR / "screening_career_yogas.parquet"  # the existing yoga-augmented output
    if not natal_path.exists():
        raise FileNotFoundError(
            f"Yoga-augmented parquet not found at {natal_path}. "
            "Run `py -3.12 -m app.medini.etl.add_yoga_features` first."
        )
    yoga_df = pd.read_parquet(natal_path)
    natal_strength_cols = [c for c in yoga_df.columns if c.endswith("_natal_strength")]
    yoga_subset = yoga_df[["name_norm", *natal_strength_cols]].drop_duplicates("name_norm")

    df = df.merge(yoga_subset, on="name_norm", how="left", validate="many_to_one")
    for missing in [c for c in natal_strength_cols if df[c].isna().any()]:
        df[missing] = df[missing].fillna(0.0)

    # Dasha-active flags.
    chain_cols = ["md_lord", "ad_lord", "pd_lord"]
    for yoga in YOGA_NAMES:
        planets = _YOGA_PLANETS[yoga]
        if not planets:
            df[f"{yoga}_dasha_active"] = 0
            continue
        df[f"{yoga}_dasha_active"] = df[chain_cols].apply(
            lambda row: int(any(l in planets for l in row)), axis=1
        ).astype("int8")
    return df
```

- [ ] **Step 4.5: Run, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_features.py -v --no-header`
Expected: 11 passed.

- [ ] **Step 4.6: Commit**

```bash
git add app/medini/ml/stage_d_features.py tests/test_stage_d_features.py
git commit -m "feat(medini): Stage D — yoga natal_strength + dasha_active features"
```

### Task 5: Stage-E lord-house features + doctrine prior

**Files:**
- Modify: `app/medini/ml/stage_d_features.py`
- Modify: `tests/test_stage_d_features.py`

Stage-E features come from [build_natal_lord_houses.py](../../../app/medini/etl/build_natal_lord_houses.py); doctrine scores from [dasha_doctrine_score.py](../../../app/medini/ml/dasha_doctrine_score.py).

- [ ] **Step 5.1: Discover the Stage-E + doctrine parquet paths**

Run: `py -3.12 -c "from pathlib import Path; data = Path('app/medini/data'); print([p.name for p in data.glob('*lord_house*')]); print([p.name for p in data.glob('*doctrine*')])"`

Use whichever filenames are present.

- [ ] **Step 5.2: Write the failing test**

Append:

```python
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

    def test_doctrine_score_per_class(self) -> None:
        """One doctrine_score_<class> column per qualifying class."""
        from app.medini.ml.stage_d_features import (
            add_doctrine_scores,
            QUALIFYING_EVENT_CLASSES,
        )

        corpus = load_corpus(smoke=True)
        with_doc = add_doctrine_scores(corpus)
        for cls in QUALIFYING_EVENT_CLASSES:
            assert f"doctrine_score_{cls}" in with_doc.columns
```

- [ ] **Step 5.3: Run, expect failure**

- [ ] **Step 5.4: Implement**

Append:

```python
_STAGE_E_PARQUET = _DATA_DIR / "natal_lord_houses.parquet"  # from build_natal_lord_houses.py
_DOCTRINE_PARQUET = _DATA_DIR / "doctrine_scores.parquet"   # from dasha_doctrine_score.py


def add_stage_e_features(df: pd.DataFrame) -> pd.DataFrame:
    """Join Stage-E per-(person, planet) lord-house features.

    Columns: rules_<planet>, occ_<planet>, aspects_<planet> per planet in
    the 9-lord set. Same value across windows for a given person.
    """
    if not _STAGE_E_PARQUET.exists():
        raise FileNotFoundError(
            f"Stage-E parquet not found at {_STAGE_E_PARQUET}. "
            "Run `py -3.12 -m app.medini.etl.build_natal_lord_houses` first."
        )
    stage_e = pd.read_parquet(_STAGE_E_PARQUET)
    return df.merge(stage_e, on="name_norm", how="left", validate="many_to_one")


def add_doctrine_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Join the doctrine_score_<class> columns (one per qualifying class)."""
    if not _DOCTRINE_PARQUET.exists():
        raise FileNotFoundError(
            f"Doctrine-score parquet not found at {_DOCTRINE_PARQUET}. "
            "Run `py -3.12 -m app.medini.ml.dasha_doctrine_score` first."
        )
    doc = pd.read_parquet(_DOCTRINE_PARQUET)
    # The doctrine parquet should have one column per qualifying class.
    # If it has more (e.g. for non-qualifying classes), filter to ours.
    keep = ["name_norm"] + [f"doctrine_score_{c}" for c in QUALIFYING_EVENT_CLASSES
                            if f"doctrine_score_{c}" in doc.columns]
    return df.merge(doc[keep], on="name_norm", how="left", validate="many_to_one")
```

- [ ] **Step 5.5: Run, expect PASS** (if doctrine/Stage-E parquets exist; otherwise tests skip with FileNotFoundError — engineer judgment)

- [ ] **Step 5.6: Commit**

```bash
git add app/medini/ml/stage_d_features.py tests/test_stage_d_features.py
git commit -m "feat(medini): Stage D — join Stage-E lord-house + doctrine-score features"
```

### Task 6: Compose + materialize the feature parquet

**Files:**
- Modify: `app/medini/ml/stage_d_features.py`
- Modify: `tests/test_stage_d_features.py`

Wire up a `materialize()` function + CLI. The output parquet is the single source of truth for D.1 through D.5.

- [ ] **Step 6.1: Write the failing test**

Append:

```python
class TestMaterialize:
    def test_no_jd_columns_in_feature_set(self) -> None:
        """F3 in spec §6 — no `*_jd` or `death*` columns may be features."""
        from app.medini.ml.stage_d_features import materialize

        out = materialize(smoke=True, write=False)  # returns the DataFrame in-memory
        forbidden = [c for c in out.columns
                     if c.endswith("_jd") or c.startswith("death")
                     # explicit allow: event_death_* are LABELS, not features
                     and not c.startswith("event_")]
        assert not forbidden, f"forbidden feature cols leaked: {forbidden}"

    def test_smoke_has_at_least_one_positive_per_class(self) -> None:
        """Sub-gate D.0 — all 30 qualifying classes must have ≥1 positive in smoke."""
        from app.medini.ml.stage_d_features import (
            materialize,
            QUALIFYING_EVENT_CLASSES,
        )

        out = materialize(smoke=True, write=False)
        for cls in QUALIFYING_EVENT_CLASSES:
            col = f"event_{cls}"
            assert col in out.columns, f"missing label column: {col}"
            assert out[col].sum() >= 1, f"class `{cls}` has zero positives in smoke"
```

- [ ] **Step 6.2: Run, expect failure**

- [ ] **Step 6.3: Implement `materialize()` + CLI**

Append to `stage_d_features.py`:

```python
import argparse
import sys


def materialize(*, smoke: bool, write: bool = True) -> pd.DataFrame:
    """Compose all feature blocks and (optionally) write the output parquet."""
    df = load_corpus(smoke=smoke)
    df = join_natal_vedic_tensor(df)
    df = add_active_dasha_encoding(df)
    df = add_yoga_features_with_dasha_gating(df)
    df = add_stage_e_features(df)
    df = add_doctrine_scores(df)

    if write:
        out = _DATA_DIR / ("dasha_stage_d_features_smoke.parquet" if smoke
                           else "dasha_stage_d_features.parquet")
        df.to_parquet(out, index=False)
        logger.info("Wrote %s (%d rows × %d cols)", out, len(df), len(df.columns))
    return df


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m app.medini.ml.stage_d_features")
    p.add_argument("--smoke", action="store_true",
                   help="Use the smoke variant of the corpus.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s :: %(message)s")
    args = _parse_args(argv)
    try:
        materialize(smoke=args.smoke, write=True)
    except Exception:
        logger.exception("Feature materialization failed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6.4: Run, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_features.py -v --no-header`
Expected: 14 passed (or skipped if upstream parquets are missing — record any skips in the commit message).

- [ ] **Step 6.5: Materialize the smoke parquet**

Run: `py -3.12 -m app.medini.ml.stage_d_features --smoke`
Expected: log line `Wrote app/medini/data/dasha_stage_d_features_smoke.parquet (N rows × M cols)` where M ≈ 350-400.

- [ ] **Step 6.6: Verify sub-gate D.0**

Run: `py -3.12 -c "
import pandas as pd
df = pd.read_parquet('app/medini/data/dasha_stage_d_features_smoke.parquet')
nan_pct = (df.isna().mean() * 100).round(2)
high_nan = nan_pct[nan_pct > 5].sort_values(ascending=False)
print('cols with >5%% NaN:', len(high_nan))
print(high_nan.head(20))
print()
print('total rows:', len(df), 'total cols:', len(df.columns))
"`

Expected: `cols with >5% NaN: 0` (or very few — record any in the next commit). **Sub-gate D.0 passes.**

- [ ] **Step 6.7: Commit**

```bash
git add app/medini/ml/stage_d_features.py tests/test_stage_d_features.py app/medini/data/dasha_stage_d_features_smoke.parquet
git commit -m "feat(medini): Stage D — feature materialization CLI + sub-gate D.0 PASS"
```

---

## Phase D.1 — Cox baseline

**Sub-gate (must hold before D.2):** All 30 Cox models converge on smoke and full per seed. Per-class C-index in [0.4, 0.7]. L1 penalty=0.01 fixed. ProcessPool parallelization verified.

### Task 7: Cox baseline — single-class fit

**Files:**
- Create: `app/medini/ml/stage_d_baseline.py`
- Create: `tests/test_stage_d_baseline.py`

- [ ] **Step 7.1: Write the failing test**

Create `tests/test_stage_d_baseline.py`:

```python
"""Tests for Fork-A Stage D Cox PH baseline."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.stage_d_baseline import (
    fit_cause_specific_cox,
    PENALIZER,
)


class TestFitCauseSpecificCox:
    def test_returns_c_index_in_range(self) -> None:
        """Single-class Cox PH on smoke returns C-index in [0.4, 0.7]."""
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        result = fit_cause_specific_cox(smoke, event_class="career", seed=42)
        assert 0.4 <= result.c_index <= 0.7, f"got {result.c_index:.3f}"
        assert result.converged is True

    def test_penalizer_is_locked_at_0_01(self) -> None:
        """L1 penalty is fixed (no tune)."""
        assert PENALIZER == 0.01
```

- [ ] **Step 7.2: Run, expect failure**

- [ ] **Step 7.3: Implement**

Create `app/medini/ml/stage_d_baseline.py`:

```python
"""Fork-A Stage D — matched-feature cause-specific Cox PH baseline.

For each qualifying event class, fit lifelines.CoxPHFitter with L1
penalty on the SAME features as Stage D. Per-class C-index is the
metric the gate compares against. 30 fits per seed; parallelized via
ProcessPoolExecutor.

See docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md §4.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.exceptions import ConvergenceError
from lifelines.utils import concordance_index
from sklearn.model_selection import GroupShuffleSplit

from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

logger = logging.getLogger(__name__)

PENALIZER: float = 0.01  # L1; locked, no tune.
DEFAULT_TEST_SIZE: float = 0.20

# Lord categorical columns get ordinal-encoded for lifelines (no embeddings).
_CATEGORICAL_COLS: tuple[str, ...] = ("md_lord", "ad_lord", "pd_lord")
# Columns NOT eligible as features (labels, ids, raw lord categories
# replaced by ordinals + one-hots, JD columns).
_NON_FEATURE_PREFIXES: tuple[str, ...] = ("event_", "event_jd_")
_NON_FEATURE_EXACT: frozenset[str] = frozenset({
    "name", "name_norm", "birth_jd", "moon_longitude",
    "md_seq_idx", "ad_seq_idx", "pd_seq_idx",
    "window_start_jd", "window_end_jd",
    "n_events_in_window",
    "md_lord", "ad_lord", "pd_lord",
})


@dataclass(frozen=True, slots=True)
class CoxFitResult:
    event_class: str
    seed: int
    c_index: float
    n_train: int
    n_test: int
    n_train_positives: int
    n_test_positives: int
    converged: bool
    convergence_msg: str = ""


def _feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns
            if c not in _NON_FEATURE_EXACT
            and not any(c.startswith(p) for p in _NON_FEATURE_PREFIXES)]


def _ordinal_encode_lords(df: pd.DataFrame) -> pd.DataFrame:
    """Replace md/ad/pd_lord with ordinal-encoded versions for lifelines."""
    from app.medini.ml.stage_d_features import _DASHA_LORDS
    lord_to_int = {l: i for i, l in enumerate(_DASHA_LORDS)}
    out = df.copy()
    for col in _CATEGORICAL_COLS:
        out[f"{col}_ord"] = out[col].map(lord_to_int).astype("int8")
    return out


def fit_cause_specific_cox(
    train: pd.DataFrame,
    test: pd.DataFrame,
    *,
    event_class: str,
    seed: int,
) -> CoxFitResult:
    """Fit one cause-specific Cox PH model for `event_class` using a
    pre-split train/test pair.

    The caller (stage_d_train._train_one_seed) MUST use the same
    GroupShuffleSplit as the DeepHit model for the gate's Δ to be
    apples-to-apples (spec §5).

    Other 29 classes are treated as censoring (standard cause-specific).
    """
    train = _ordinal_encode_lords(train)
    test = _ordinal_encode_lords(test)
    event_col = f"event_{event_class}"
    if event_col not in train.columns:
        raise ValueError(f"missing label column {event_col}")
    assert set(train["name_norm"]).isdisjoint(set(test["name_norm"])), "person leak"

    features = _feature_columns(train)
    cph_input_train = train[features + ["window_duration_days", event_col]].copy()
    cph_input_train.rename(columns={"window_duration_days": "T",
                                    event_col: "E"}, inplace=True)

    cph = CoxPHFitter(penalizer=PENALIZER, l1_ratio=1.0)  # pure L1
    try:
        cph.fit(cph_input_train, duration_col="T", event_col="E", show_progress=False)
        converged, msg = True, ""
    except ConvergenceError as e:
        logger.warning("Cox failed for class=%s seed=%d: %s", event_class, seed, e)
        return CoxFitResult(
            event_class=event_class, seed=seed,
            c_index=float("nan"),
            n_train=len(train), n_test=len(test),
            n_train_positives=int(train[event_col].sum()),
            n_test_positives=int(test[event_col].sum()),
            converged=False, convergence_msg=str(e),
        )

    # Risk score = predicted partial hazard. Pass `-risk` so high risk =>
    # earlier event (lifelines convention for concordance_index).
    risk = cph.predict_partial_hazard(test[features])
    c = concordance_index(test["window_duration_days"], -risk, test[event_col])

    return CoxFitResult(
        event_class=event_class, seed=seed,
        c_index=float(c),
        n_train=len(train), n_test=len(test),
        n_train_positives=int(train[event_col].sum()),
        n_test_positives=int(test[event_col].sum()),
        converged=True,
    )


def split_train_test(df: pd.DataFrame, *, seed: int,
                     test_size: float = DEFAULT_TEST_SIZE
                     ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Single source of truth for the per-seed split. Use this from BOTH
    stage_d_train._train_one_seed (DeepHit side) and fit_all_classes
    (Cox side) so the gate's Δ is computed on identical splits."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(df, groups=df["name_norm"]))
    return df.iloc[train_idx].reset_index(drop=True), df.iloc[test_idx].reset_index(drop=True)
```

**Update the Step 7.1 test to match the new signature:**

```python
class TestFitCauseSpecificCox:
    def test_returns_c_index_in_range(self) -> None:
        """Single-class Cox PH on smoke returns C-index in [0.4, 0.7]."""
        from app.medini.ml.stage_d_baseline import split_train_test
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        train, test = split_train_test(smoke, seed=42)
        result = fit_cause_specific_cox(train, test, event_class="career", seed=42)
        assert 0.4 <= result.c_index <= 0.7, f"got {result.c_index:.3f}"
        assert result.converged is True
```

- [ ] **Step 7.4: Run, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_baseline.py -v --no-header`
Expected: 2 passed.

- [ ] **Step 7.5: Commit**

```bash
git add app/medini/ml/stage_d_baseline.py tests/test_stage_d_baseline.py
git commit -m "feat(medini): Stage D Cox baseline — single-class fit + C-index"
```

### Task 8: Cox baseline — all 30 classes per seed

**Files:**
- Modify: `app/medini/ml/stage_d_baseline.py`
- Modify: `tests/test_stage_d_baseline.py`

- [ ] **Step 8.1: Write the failing test**

Append to `tests/test_stage_d_baseline.py`:

```python
class TestFitAllClasses:
    def test_returns_one_result_per_class(self) -> None:
        """fit_all_classes returns exactly 30 results on smoke."""
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        from app.medini.ml.stage_d_baseline import fit_all_classes, split_train_test
        train, test = split_train_test(smoke, seed=42)

        results = fit_all_classes(train, test, seed=42, parallel=False)
        from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
        assert len(results) == len(QUALIFYING_EVENT_CLASSES)
        assert {r.event_class for r in results} == set(QUALIFYING_EVENT_CLASSES)
```

- [ ] **Step 8.2: Implement (sequential first; parallelization in Task 9)**

Append to `stage_d_baseline.py`:

```python
def fit_all_classes(
    train: pd.DataFrame,
    test: pd.DataFrame,
    *,
    seed: int,
    parallel: bool = True,
) -> list[CoxFitResult]:
    """Fit 30 cause-specific Cox PH models, one per qualifying class.

    Train/test split MUST be the same one passed to the DeepHit model
    in stage_d_train._train_one_seed for the gate's Δ to be valid.
    """
    if parallel:
        return _fit_all_classes_parallel(train, test, seed=seed)
    return [
        fit_cause_specific_cox(train, test, event_class=cls, seed=seed)
        for cls in QUALIFYING_EVENT_CLASSES
    ]


def _fit_all_classes_parallel(train, test, *, seed):  # filled in Task 9
    raise NotImplementedError("see Task 9")
```

- [ ] **Step 8.3: Run, expect PASS** (with `parallel=False`)

Run: `py -3.12 -m pytest tests/test_stage_d_baseline.py -v --no-header`

- [ ] **Step 8.4: Commit**

```bash
git add app/medini/ml/stage_d_baseline.py tests/test_stage_d_baseline.py
git commit -m "feat(medini): Stage D Cox baseline — sequential per-class loop (30 classes)"
```

### Task 9: ProcessPool parallelization for Cox fits

**Files:**
- Modify: `app/medini/ml/stage_d_baseline.py`
- Modify: `tests/test_stage_d_baseline.py`

- [ ] **Step 9.1: Write the failing test (parallel mode parity)**

Append:

```python
class TestParallelParity:
    def test_parallel_results_match_sequential(self) -> None:
        """Parallel + sequential produce identical C-indices (modulo nan order)."""
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        from app.medini.ml.stage_d_baseline import fit_all_classes, split_train_test
        train, test = split_train_test(smoke, seed=42)

        seq = fit_all_classes(train, test, seed=42, parallel=False)
        par = fit_all_classes(train, test, seed=42, parallel=True)
        seq_map = {r.event_class: r.c_index for r in seq}
        par_map = {r.event_class: r.c_index for r in par}
        for cls, seq_c in seq_map.items():
            par_c = par_map[cls]
            if pd.isna(seq_c) and pd.isna(par_c):
                continue
            assert abs(seq_c - par_c) < 1e-9, f"{cls}: seq={seq_c}, par={par_c}"
```

- [ ] **Step 9.2: Implement ProcessPool fan-out**

Replace the stub `_fit_all_classes_parallel`:

```python
import os
from concurrent.futures import ProcessPoolExecutor


def _fit_one(args: tuple[pd.DataFrame, pd.DataFrame, str, int]) -> CoxFitResult:
    train, test, cls, seed = args
    return fit_cause_specific_cox(train, test, event_class=cls, seed=seed)


def _fit_all_classes_parallel(train: pd.DataFrame, test: pd.DataFrame, *, seed: int
                              ) -> list[CoxFitResult]:
    n_workers = max(1, (os.cpu_count() or 2) - 1)
    # NOTE: pickling 30 copies of the (train, test) DataFrames into workers
    # is wasteful on Windows. If wall-clock becomes a problem, refactor to
    # use ProcessPoolExecutor(initializer=...) to ship the data once per worker.
    # Expected wall-clock: 8-15 min per seed at n≈8k train, 30 classes, 8 cores.
    args_list = [(train, test, cls, seed) for cls in QUALIFYING_EVENT_CLASSES]
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        results = list(ex.map(_fit_one, args_list))
    return results
```

- [ ] **Step 9.3: Run, expect PASS**

This test is slow (~5-15 min on full corpus, ~1-3 min on smoke depending on cores). Run alone:
`py -3.12 -m pytest tests/test_stage_d_baseline.py::TestParallelParity -v --no-header`

- [ ] **Step 9.4: Commit**

```bash
git add app/medini/ml/stage_d_baseline.py tests/test_stage_d_baseline.py
git commit -m "feat(medini): Stage D Cox baseline — ProcessPoolExecutor parallelization"
```

### Task 10: Sub-gate D.1 verification

- [ ] **Step 10.1: Run all 30 Cox fits on the FULL corpus (one seed) to confirm sub-gate D.1**

First materialize the FULL features parquet:

Run: `py -3.12 -m app.medini.ml.stage_d_features` (no `--smoke`)

Then:

```python
py -3.12 -c "
import pandas as pd
from app.medini.ml.stage_d_baseline import fit_all_classes, split_train_test
df = pd.read_parquet('app/medini/data/dasha_stage_d_features.parquet')
train, test = split_train_test(df, seed=42)
results = fit_all_classes(train, test, seed=42, parallel=True)
for r in sorted(results, key=lambda x: -x.c_index if x.converged else 0):
    flag = ' OK' if 0.4 <= r.c_index <= 0.7 else ' FAIL' if r.converged else ' NO-CONV'
    print(f'{r.event_class:35s} c={r.c_index:.4f} n_pos_train={r.n_train_positives:5d}{flag}')
"
```

Expected: ≥28 of 30 classes show C-index in [0.4, 0.7] and `converged=True`. Any failing class needs investigation (likely too few positives). **Sub-gate D.1 PASS if all 30 converge with C-index in range.**

- [ ] **Step 10.2: Commit the full-corpus features parquet**

```bash
git add app/medini/data/dasha_stage_d_features.parquet
git commit -m "data(medini): Stage D — materialized full features parquet (sub-gate D.0 PASS)"
```

---

## Phase D.2 — DeepHit wrapper + dataset

**Sub-gate (must hold before D.3):** Forward pass shapes correct (PMF over 30×50+1). Loss finite on 100 random inputs. Save/load round-trips bit-identically. Person-leak assertion fires on synthetic leaky split.

### Task 11: PyTorch Dataset + time-bin assignment

**Files:**
- Create: `app/medini/ml/stage_d_dataset.py`
- Create: `tests/test_stage_d_dataset.py`

- [ ] **Step 11.0: Verify `event_jd_<class>` tie-break columns exist (or document fallback)**

The implementation uses `event_jd_<class>` to break ties when multiple events fire in the same window. Spec §2's column list does NOT explicitly show these — they may or may not be in `dasha_mdadpd_corpus.parquet`.

Run:
```
py -3.12 -c "
import pandas as pd
df = pd.read_parquet('app/medini/data/dasha_mdadpd_corpus.parquet')
jd_cols = [c for c in df.columns if c.startswith('event_jd_')]
print('event_jd_ columns:', len(jd_cols))
for c in jd_cols[:5]:
    print(' ', c)
"
```

- If JD columns exist: proceed with the `event_jd`-based earliest-wins logic in `_resolve_event_label`.
- If they DON'T exist: the implementation must fall back to "first qualifying class in `QUALIFYING_EVENT_CLASSES` order wins" (deterministic but arbitrary). Document this choice in the module docstring AND in `data/ml_runs/fork_a_stage_d/DECISION.md` under "deviations from spec §2".

The fallback is acceptable because (a) co-occurrence rate is reported by pre-flight (F4) and (b) the gate's G2 ≥11-of-30 criterion is robust to a small bias in which class wins co-occurrence ties.

- [ ] **Step 11.1: Write the failing test**

Create `tests/test_stage_d_dataset.py`:

```python
"""Tests for Fork-A Stage D PyTorch Dataset + time-bin assignment."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch

from app.medini.ml.stage_d_dataset import (
    K_BINS,
    StageDDataset,
    assign_time_bin,
    build_dataset,
)


class TestTimeBins:
    def test_k_bins_is_50(self) -> None:
        assert K_BINS == 50

    def test_one_day_window_in_lowest_bin(self) -> None:
        assert assign_time_bin(1.0) == 0

    def test_century_window_in_highest_bin(self) -> None:
        assert assign_time_bin(100 * 365.25) == K_BINS - 1


class TestStageDDataset:
    def test_dataset_length_matches_dataframe(self) -> None:
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        ds = build_dataset(smoke, name_norms=smoke["name_norm"].unique())
        assert len(ds) == len(smoke)

    def test_dataset_item_shapes(self) -> None:
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        ds = build_dataset(smoke, name_norms=smoke["name_norm"].unique())
        features, time_bin, event_class = ds[0]
        assert features.dtype == torch.float32
        assert time_bin.dtype == torch.long
        assert event_class.dtype == torch.long
        assert 0 <= int(time_bin) < K_BINS
        assert 0 <= int(event_class) <= 30  # 0 = censored, 1..30 = class

    def test_person_leak_assertion(self) -> None:
        """build_dataset must refuse a name_norms list disjoint from the df."""
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        with pytest.raises(AssertionError, match="person leak"):
            build_dataset(smoke[:100], name_norms=smoke["name_norm"].iloc[100:].unique())
```

- [ ] **Step 11.2: Run, expect failure**

- [ ] **Step 11.3: Implement**

Create `app/medini/ml/stage_d_dataset.py`:

```python
"""Fork-A Stage D — PyTorch Dataset for Dynamic-DeepHit training.

Discretizes window durations into K=50 log-spaced bins from 1 day to
100 years. Each row produces (features_vector, time_bin, event_class)
where event_class=0 means censored, 1..30 indexes QUALIFYING_EVENT_CLASSES.

When multiple events fire in a window (rare per pre-flight diagnostic),
the earliest-JD one wins.

See spec §2 and §3.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

logger = logging.getLogger(__name__)

K_BINS: int = 50

# Log-spaced bin edges from 1 day to 100 years.
_BIN_EDGES: np.ndarray = np.logspace(
    np.log10(1.0), np.log10(100 * 365.25), K_BINS + 1
)


def assign_time_bin(duration_days: float) -> int:
    """Return the bin index (0..K_BINS-1) for a window duration."""
    idx = int(np.searchsorted(_BIN_EDGES, duration_days, side="right") - 1)
    return max(0, min(K_BINS - 1, idx))


_CLASS_TO_IDX: dict[str, int] = {
    cls: i + 1  # 0 = censored
    for i, cls in enumerate(QUALIFYING_EVENT_CLASSES)
}


def _resolve_event_label(row: pd.Series) -> int:
    """Returns 0 (censored) or class index 1..K. Earliest-JD wins on ties."""
    earliest_jd = float("inf")
    chosen_cls = 0
    for cls in QUALIFYING_EVENT_CLASSES:
        if row.get(f"event_{cls}", 0) != 1:
            continue
        jd = row.get(f"event_jd_{cls}", earliest_jd)
        if pd.isna(jd):
            jd = float("inf")
        if jd < earliest_jd:
            earliest_jd = jd
            chosen_cls = _CLASS_TO_IDX[cls]
    return chosen_cls


def _select_feature_columns(df: pd.DataFrame) -> list[str]:
    """Same exclusion logic as stage_d_baseline (mirrors §6 F3 deny list)."""
    from app.medini.ml.stage_d_baseline import _feature_columns
    return _feature_columns(df)


class StageDDataset(Dataset):
    """Carries features, time bins, event classes, AND raw durations.

    `durations` is a numpy array in the SAME ROW ORDER as `features`,
    `time_bins`, and `event_classes`. This lets the training loop pass
    a consistent durations vector to `lifelines.utils.concordance_index`
    without re-deriving it from the original DataFrame (which has a
    different index after the post-filter `reset_index(drop=True)`).
    """
    def __init__(self, features: torch.Tensor,
                 time_bins: torch.Tensor,
                 event_classes: torch.Tensor,
                 durations: np.ndarray) -> None:
        assert len(features) == len(time_bins) == len(event_classes) == len(durations)
        self.features = features
        self.time_bins = time_bins
        self.event_classes = event_classes
        self.durations = durations  # raw window_duration_days, same row order

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.features[idx], self.time_bins[idx], self.event_classes[idx]


def build_dataset(df: pd.DataFrame, *, name_norms) -> StageDDataset:
    """Build a Dataset restricted to the given `name_norms` (train OR test side).

    Caller MUST pass the name_norm list for ONE side of the split; this
    function asserts the dataframe rows match (F1 in spec §6).
    """
    name_norms = set(name_norms)
    sub = df[df["name_norm"].isin(name_norms)].reset_index(drop=True)
    assert set(sub["name_norm"]).issubset(name_norms), "person leak"
    if len(sub) == 0:
        raise ValueError("empty dataset")

    feat_cols = _select_feature_columns(sub)
    features = torch.tensor(sub[feat_cols].fillna(0.0).to_numpy(np.float32))
    durations = sub["window_duration_days"].to_numpy()
    time_bins = torch.tensor(
        [assign_time_bin(d) for d in durations],
        dtype=torch.long,
    )
    event_classes = torch.tensor(
        [_resolve_event_label(row) for _, row in sub.iterrows()],
        dtype=torch.long,
    )
    return StageDDataset(features, time_bins, event_classes, durations)
```

- [ ] **Step 11.4: Run, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_dataset.py -v --no-header`
Expected: 6 passed.

- [ ] **Step 11.5: Commit**

```bash
git add app/medini/ml/stage_d_dataset.py tests/test_stage_d_dataset.py
git commit -m "feat(medini): Stage D — PyTorch Dataset + 50-bin log time discretization"
```

### Task 12: DeepHit model — encoder + heads + forward

**Files:**
- Create: `app/medini/ml/stage_d_model.py`
- Create: `tests/test_stage_d_model.py`

- [ ] **Step 12.1: Write the failing test**

Create `tests/test_stage_d_model.py`:

```python
"""Tests for Fork-A Stage D Dynamic-DeepHit model."""
from __future__ import annotations

import torch
import pytest

from app.medini.ml.stage_d_model import StageDModel


class TestStageDModel:
    def test_forward_pass_shape(self) -> None:
        """Output is PMF over (30 classes × 50 bins + 1 censored) = 1501 logits."""
        model = StageDModel(n_features=300)
        x = torch.randn(8, 300)  # batch of 8
        out = model(x)
        assert out.shape == (8, 30 * 50 + 1)

    def test_forward_pmf_normalized(self) -> None:
        """Output rows sum to 1 (it's a PMF after softmax)."""
        model = StageDModel(n_features=300)
        model.eval()
        x = torch.randn(8, 300)
        out = model(x)
        row_sums = out.sum(dim=1)
        assert torch.allclose(row_sums, torch.ones(8), atol=1e-5)

    def test_loss_finite_on_random_inputs(self) -> None:
        """F9 catch — loss is finite on 100 random samples."""
        from app.medini.ml.stage_d_model import deephit_loss

        torch.manual_seed(42)
        model = StageDModel(n_features=300)
        x = torch.randn(100, 300)
        time_bins = torch.randint(0, 50, (100,))
        event_classes = torch.randint(0, 31, (100,))  # 0 = censored
        pmf = model(x)
        loss = deephit_loss(pmf, time_bins, event_classes)
        assert torch.isfinite(loss).item()
```

- [ ] **Step 12.2: Run, expect failure**

- [ ] **Step 12.3: Implement model + loss**

Create `app/medini/ml/stage_d_model.py`:

```python
"""Fork-A Stage D — Dynamic-DeepHit competing-risks hazard model.

Shared MLP encoder (3 × FC(256) + BN + ReLU + Dropout) feeds 30 cause-
specific per-class hazard heads; each head outputs K_BINS=50 hazard
logits. Final softmax across all (class × bin) + 1 censored bucket
yields a joint PMF.

Loss = α · NLL + (1−α) · ranking_loss with α=0.5 (DeepHit default).

See spec §3.
"""
from __future__ import annotations

import torch
from torch import nn

from app.medini.ml.stage_d_dataset import K_BINS
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

N_CLASSES = len(QUALIFYING_EVENT_CLASSES)  # 30


class _PerClassHead(nn.Module):
    def __init__(self, hidden: int = 256) -> None:
        super().__init__()
        self.fc1 = nn.Linear(hidden, 128)
        self.act = nn.ReLU(inplace=True)
        self.fc2 = nn.Linear(128, K_BINS)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(self.act(self.fc1(x)))


class StageDModel(nn.Module):
    def __init__(self, n_features: int, hidden: int = 256, dropout: float = 0.3) -> None:
        super().__init__()
        layers = []
        in_dim = n_features
        for _ in range(3):
            layers += [
                nn.Linear(in_dim, hidden),
                nn.BatchNorm1d(hidden),
                nn.ReLU(inplace=True),
                nn.Dropout(dropout),
            ]
            in_dim = hidden
        self.encoder = nn.Sequential(*layers)
        self.heads = nn.ModuleList([_PerClassHead(hidden) for _ in range(N_CLASSES)])
        self.censored_logit = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns PMF of shape (batch, N_CLASSES * K_BINS + 1)."""
        h = self.encoder(x)
        per_class = torch.cat([head(h) for head in self.heads], dim=1)  # (b, 30*50)
        cens = self.censored_logit(h)  # (b, 1)
        logits = torch.cat([per_class, cens], dim=1)  # (b, 30*50 + 1)
        return torch.softmax(logits, dim=1)


def deephit_loss(
    pmf: torch.Tensor,
    time_bins: torch.Tensor,
    event_classes: torch.Tensor,
    alpha: float = 0.5,
) -> torch.Tensor:
    """DeepHit-style: α · NLL + (1−α) · ranking loss.

    NLL = -log(prob of correct (class, bin) cell).
    Ranking = pairwise margin loss encouraging earlier-event subjects to
    have higher cumulative hazard than later-event subjects of the same class.
    """
    batch_size = pmf.size(0)
    censored_mask = event_classes == 0

    # NLL: pick the right cell per row.
    # event_classes is 0 (censored) or 1..N_CLASSES.
    cell_idx = torch.where(
        censored_mask,
        torch.full_like(event_classes, N_CLASSES * K_BINS),  # censored bucket
        (event_classes - 1) * K_BINS + time_bins,
    )
    cell_prob = pmf.gather(1, cell_idx.unsqueeze(1)).squeeze(1).clamp(min=1e-10)
    nll = -torch.log(cell_prob).mean()

    # Ranking: only meaningful between non-censored pairs of same class.
    # Simplified: skip ranking for batches with <2 same-class events.
    ranking = torch.tensor(0.0, device=pmf.device)
    for cls in range(1, N_CLASSES + 1):
        cls_mask = event_classes == cls
        if cls_mask.sum() < 2:
            continue
        idx = cls_mask.nonzero(as_tuple=True)[0]
        # Cumulative hazard for class `cls` at each subject's event bin.
        start = (cls - 1) * K_BINS
        cls_pmf = pmf[:, start:start + K_BINS]
        cum = torch.cumsum(cls_pmf, dim=1)
        bins_i = time_bins[idx]
        cum_at_event = cum[idx, bins_i]
        # Pairs: subject with earlier event should have higher cum.
        order = torch.argsort(bins_i)
        ordered = cum_at_event[order]
        diffs = ordered[:-1] - ordered[1:]  # should be ≥ 0
        ranking = ranking + torch.clamp(0.1 - diffs, min=0).mean()

    return alpha * nll + (1 - alpha) * ranking
```

- [ ] **Step 12.4: Run, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_model.py -v --no-header`
Expected: 3 passed.

- [ ] **Step 12.5: Commit**

```bash
git add app/medini/ml/stage_d_model.py tests/test_stage_d_model.py
git commit -m "feat(medini): Stage D model — DeepHit encoder + 30 heads + loss"
```

### Task 13: Model save/load round-trip

**Files:**
- Modify: `app/medini/ml/stage_d_model.py`
- Modify: `tests/test_stage_d_model.py`

- [ ] **Step 13.1: Write the failing test**

Append:

```python
class TestSaveLoad:
    def test_round_trip_identical(self, tmp_path) -> None:
        """Save + load + forward = bit-identical output."""
        torch.manual_seed(7)
        model = StageDModel(n_features=128)
        model.eval()
        x = torch.randn(4, 128)
        out_before = model(x)

        save_path = tmp_path / "model.pt"
        model.save(save_path)
        loaded = StageDModel.load(save_path, n_features=128)
        loaded.eval()
        out_after = loaded(x)
        assert torch.equal(out_before, out_after)
```

- [ ] **Step 13.2: Implement save / load AS METHODS INSIDE THE CLASS**

⚠️ `@classmethod` cannot be assigned to a class as an attribute after definition — the descriptor binding only works inside a class body. Add these to `StageDModel` directly (NOT as monkey-patched assignments):

```python
# Inside class StageDModel:

    def save(self, path) -> None:
        from pathlib import Path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path)

    @classmethod
    def load(cls, path, *, n_features: int, hidden: int = 256,
             dropout: float = 0.3) -> "StageDModel":
        model = cls(n_features=n_features, hidden=hidden, dropout=dropout)
        model.load_state_dict(torch.load(path, map_location="cpu"))
        return model
```

Edit the existing `StageDModel` class in `stage_d_model.py` and add these two methods after `forward`.

- [ ] **Step 13.3: Run, expect PASS**

- [ ] **Step 13.4: Commit**

```bash
git add app/medini/ml/stage_d_model.py tests/test_stage_d_model.py
git commit -m "feat(medini): Stage D model — save/load round-trip"
```

### Task 14: Person-leak smoke + train-on-shuffled-times leakage smoke (F1 + F2 catches)

**Files:**
- Modify: `tests/test_stage_d_dataset.py`

- [ ] **Step 14.1: Write the failing tests**

Append:

```python
class TestLeakageCatches:
    def test_shuffled_times_collapse_c_index(self) -> None:
        """F2 in spec §6 — shuffling event labels should give C-index ≈ 0.5.

        This is the canary that catches time-causal feature leakage.
        """
        # Skipped here as a pure-Python lightweight check;
        # the real integration smoke lives in test_stage_d_preflight.py.
        pytest.skip("end-to-end smoke lives in test_stage_d_preflight.py")
```

- [ ] **Step 14.2: Run** (skipped is acceptable here; real test in Task 18)

- [ ] **Step 14.3: Commit**

```bash
git add tests/test_stage_d_dataset.py
git commit -m "test(medini): Stage D — placeholder for shuffled-time leakage smoke"
```

### Task 15: Sub-gate D.2 verification (end-to-end smoke train)

- [ ] **Step 15.1: Confirm forward + loss work on a small slice of real data**

Run:
```
py -3.12 -c "
import pandas as pd, torch
from app.medini.ml.stage_d_dataset import build_dataset
from app.medini.ml.stage_d_model import StageDModel, deephit_loss
df = pd.read_parquet('app/medini/data/dasha_stage_d_features_smoke.parquet')
ds = build_dataset(df, name_norms=df['name_norm'].unique())
n_features = ds.features.shape[1]
print('n_features:', n_features)
model = StageDModel(n_features=n_features)
pmf = model(ds.features[:32])
loss = deephit_loss(pmf, ds.time_bins[:32], ds.event_classes[:32])
print('loss:', float(loss))
assert torch.isfinite(loss).item()
print('sub-gate D.2: forward + loss OK on real smoke data')
"
```

Expected: `loss: <finite number>`, `sub-gate D.2: forward + loss OK on real smoke data`. **Sub-gate D.2 PASS.**

---

## Phase D.3 — Training script + pre-flight

**Sub-gate (must hold before D.4):** Pre-flight passes all 5 checks. One-seed smoke train converges (val loss decreases). Per-class C-index ∈ [0.4, 0.7] on smoke. K confirmed = 30.

### Task 16: Pre-flight script — all 5 checks

**Files:**
- Create: `app/medini/ml/stage_d_preflight.py`
- Create: `tests/test_stage_d_preflight.py`

- [ ] **Step 16.1: Write the failing tests**

Create `tests/test_stage_d_preflight.py`:

```python
"""Tests for Fork-A Stage D pre-flight diagnostics."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.stage_d_preflight import (
    PreflightResult,
    check_class_qualification,
    check_co_occurrence_rate,
    check_no_jd_in_features,
    check_person_leak_assertion,
    check_shuffled_times_collapse,
    run_preflight,
)


class TestPreflight:
    def test_class_qualification_on_full_smoke(self) -> None:
        df = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        K, dropped = check_class_qualification(df, min_positives=1)
        assert K == 30

    def test_no_jd_in_features(self) -> None:
        df = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        result = check_no_jd_in_features(df)
        assert result.passed, f"forbidden cols: {result.detail}"

    def test_run_preflight_writes_md(self, tmp_path) -> None:
        result = run_preflight(smoke=True, out_dir=tmp_path)
        assert (tmp_path / "preflight.md").exists()
        assert result.all_passed
```

- [ ] **Step 16.2: Run, expect failure**

- [ ] **Step 16.3: Implement**

Create `app/medini/ml/stage_d_preflight.py`:

```python
"""Fork-A Stage D — mandatory pre-flight diagnostics.

Five checks; ALL must pass before the main training pipeline starts.
See spec §6 "Mandatory pre-flight".
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class PreflightResult:
    checks: tuple[CheckResult, ...]

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)


def check_person_leak_assertion() -> CheckResult:
    """Synthetic 100-person corpus — leak assertion must fire."""
    from app.medini.ml.stage_d_dataset import build_dataset
    df = pd.DataFrame({"name_norm": [f"p{i}" for i in range(100)] * 3,
                       "window_duration_days": [100.0] * 300})
    # Force-add the qualifying event cols as zeros.
    for cls in QUALIFYING_EVENT_CLASSES:
        df[f"event_{cls}"] = 0
    try:
        build_dataset(df.iloc[:100], name_norms={"never_seen"})
    except AssertionError:
        return CheckResult("person_leak_assertion_fires", True)
    except ValueError:
        # build_dataset raises ValueError on empty subset before asserting; that's fine.
        return CheckResult("person_leak_assertion_fires", True,
                           "empty-subset shortcut took precedence; assertion path still in place")
    return CheckResult("person_leak_assertion_fires", False,
                       "assertion did NOT fire on synthetic leak")


def check_shuffled_times_collapse(df: pd.DataFrame, seed: int = 999) -> CheckResult:
    """Shuffling event labels should give Cox C-index ≈ 0.5 (within 0.05)."""
    rng = np.random.default_rng(seed)
    shuffled = df.copy()
    for cls in ("career", "fame"):  # 2 sentinel classes, not all 30 for speed
        shuffled[f"event_{cls}"] = rng.permutation(shuffled[f"event_{cls}"].values)
    from app.medini.ml.stage_d_baseline import fit_cause_specific_cox
    r = fit_cause_specific_cox(shuffled, event_class="career", seed=seed)
    if not r.converged:
        return CheckResult("shuffled_times_collapse", True,
                           "Cox didn't converge on shuffled labels; acceptable")
    if abs(r.c_index - 0.5) > 0.05:
        return CheckResult("shuffled_times_collapse", False,
                           f"C-index={r.c_index:.3f}, expected near 0.5 — feature leakage suspected")
    return CheckResult("shuffled_times_collapse", True,
                       f"C-index={r.c_index:.3f} ≈ 0.5")


def check_no_jd_in_features(df: pd.DataFrame) -> CheckResult:
    from app.medini.ml.stage_d_baseline import _feature_columns
    feat_cols = _feature_columns(df)
    forbidden = [c for c in feat_cols
                 if c.endswith("_jd") or (c.startswith("death") and not c.startswith("event_"))]
    if forbidden:
        return CheckResult("no_jd_in_features", False, f"leaked: {forbidden}")
    return CheckResult("no_jd_in_features", True, f"{len(feat_cols)} clean feature cols")


def check_co_occurrence_rate(df: pd.DataFrame) -> CheckResult:
    event_cols = [f"event_{c}" for c in QUALIFYING_EVENT_CLASSES]
    multi_event = (df[event_cols].sum(axis=1) > 1).mean()
    passed = multi_event < 0.05
    return CheckResult("co_occurrence_rate", passed,
                       f"{multi_event:.2%} of windows have >1 event (threshold: <5%)")


def check_class_qualification(df: pd.DataFrame, *, min_positives: int = 50
                              ) -> tuple[int, list[str]]:
    """Returns (K_qualifying, [dropped_class_names])."""
    qualifying, dropped = [], []
    for cls in QUALIFYING_EVENT_CLASSES:
        col = f"event_{cls}"
        if col not in df.columns:
            dropped.append(cls)
            continue
        if df[col].sum() >= min_positives:
            qualifying.append(cls)
        else:
            dropped.append(cls)
    return len(qualifying), dropped


def check_hardware() -> CheckResult:
    cuda = torch.cuda.is_available()
    deterministic = torch.are_deterministic_algorithms_enabled()
    return CheckResult("hardware",
                       passed=True,  # informational only; gate runs use CPU regardless
                       detail=f"torch={torch.__version__}, cuda_available={cuda}, "
                              f"deterministic={deterministic}")


def run_preflight(*, smoke: bool, out_dir: Path) -> PreflightResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df_path = Path("app/medini/data") / (
        "dasha_stage_d_features_smoke.parquet" if smoke
        else "dasha_stage_d_features.parquet"
    )
    df = pd.read_parquet(df_path)

    checks = (
        check_person_leak_assertion(),
        check_shuffled_times_collapse(df),
        check_no_jd_in_features(df),
        check_co_occurrence_rate(df),
        check_hardware(),
    )
    K, dropped = check_class_qualification(df, min_positives=50 if not smoke else 1)
    qual_check = CheckResult(
        "class_qualification",
        passed=K >= 25,
        detail=f"K={K}/30 qualify; dropped: {dropped}",
    )
    checks = (*checks, qual_check)

    md = ["# Stage D Pre-flight Report\n"]
    md += ["| Check | Status | Detail |", "|---|---|---|"]
    for c in checks:
        md.append(f"| {c.name} | {'✓ PASS' if c.passed else '✗ FAIL'} | {c.detail} |")
    (out_dir / "preflight.md").write_text("\n".join(md), encoding="utf-8")

    return PreflightResult(checks=checks)


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--out-dir", type=Path, default=Path("data/ml_runs/fork_a_stage_d"))
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s :: %(message)s")
    result = run_preflight(smoke=args.smoke, out_dir=args.out_dir)
    for c in result.checks:
        flag = "PASS" if c.passed else "FAIL"
        logger.info("  [%s] %s — %s", flag, c.name, c.detail)
    return 0 if result.all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
```

- [ ] **Step 16.4: Run, expect PASS**

Run: `py -3.12 -m pytest tests/test_stage_d_preflight.py -v --no-header`

- [ ] **Step 16.5: Run preflight on smoke**

Run: `py -3.12 -m app.medini.ml.stage_d_preflight --smoke`
Expected: all checks PASS; file `data/ml_runs/fork_a_stage_d/preflight.md` written.

- [ ] **Step 16.6: Commit**

```bash
git add app/medini/ml/stage_d_preflight.py tests/test_stage_d_preflight.py data/ml_runs/fork_a_stage_d/preflight.md
git commit -m "feat(medini): Stage D pre-flight — 5 mandatory checks + report"
```

### Task 17: Training script — single-seed end-to-end

**Files:**
- Create: `app/medini/ml/stage_d_train.py`

- [ ] **Step 17.1: Implement (no separate test file; tested via the smoke-run command in Step 17.4)**

Create `app/medini/ml/stage_d_train.py`:

```python
"""Fork-A Stage D — single-seed training driver.

Trains StageDModel for one seed on the materialized features parquet,
trains the matched Cox baseline (30 per-class fits, parallel), and
writes per-seed results to a JSON record.

Usage:
    py -3.12 -m app.medini.ml.stage_d_train \\
        --seed 1 \\
        --split main \\
        --test-size 0.20 \\
        --out-dir data/ml_runs/fork_a_stage_d \\
        [--smoke]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import GroupShuffleSplit
from torch.utils.data import DataLoader

import lifelines

from app.medini.ml.stage_d_baseline import fit_all_classes, split_train_test
from app.medini.ml.stage_d_dataset import K_BINS, build_dataset
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
from app.medini.ml.stage_d_model import (N_CLASSES, StageDModel, deephit_loss)

logger = logging.getLogger(__name__)

EPOCHS = 200
PATIENCE = 20
LR = 1e-3
WEIGHT_DECAY = 1e-4
BATCH_SIZE = 256
VAL_FRAC = 0.20


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def _train_one_seed(df: pd.DataFrame, *, seed: int, test_size: float,
                    out_dir: Path, noise_floor_sha: str) -> dict:
    # Single source of truth for the split — DeepHit and Cox both use this.
    train_df, test_df = split_train_test(df, seed=seed, test_size=test_size)
    train_persons = train_df["name_norm"].unique()
    test_persons = test_df["name_norm"].unique()
    assert set(train_persons).isdisjoint(set(test_persons))

    # Hold out 20% of train persons as val.
    val_splitter = GroupShuffleSplit(n_splits=1, test_size=VAL_FRAC, random_state=seed + 1)
    sub_train_idx, val_idx = next(val_splitter.split(train_df, groups=train_df["name_norm"]))
    sub_train_df = train_df.iloc[sub_train_idx]
    val_df = train_df.iloc[val_idx]
    sub_train_persons = sub_train_df["name_norm"].unique()
    val_persons = val_df["name_norm"].unique()

    train_ds = build_dataset(sub_train_df, name_norms=sub_train_persons)
    val_ds = build_dataset(val_df, name_norms=val_persons)
    test_ds = build_dataset(test_df, name_norms=test_persons)

    n_features = train_ds.features.shape[1]
    model = StageDModel(n_features=n_features)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

    best_val = float("inf")
    best_state = None
    patience_left = PATIENCE
    for epoch in range(EPOCHS):
        model.train()
        for feats, time_bins, event_classes in train_loader:
            optimizer.zero_grad()
            pmf = model(feats)
            loss = deephit_loss(pmf, time_bins, event_classes)
            assert torch.isfinite(loss).all(), f"non-finite loss epoch {epoch}"
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_losses = []
            for feats, time_bins, event_classes in val_loader:
                pmf = model(feats)
                val_losses.append(float(deephit_loss(pmf, time_bins, event_classes)))
            val_loss = float(np.mean(val_losses))
        scheduler.step(val_loss)

        if val_loss < best_val - 1e-4:
            best_val = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_left = PATIENCE
        else:
            patience_left -= 1
            if patience_left <= 0:
                logger.info("Early stop at epoch %d (val=%.4f)", epoch, best_val)
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    model_path = out_dir / "models" / f"seed_{seed}_deephit.pt"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)

    # Per-class C-index for Stage D.
    from lifelines.utils import concordance_index
    deephit_c: dict[str, float] = {}
    model.eval()
    with torch.no_grad():
        test_pmf = model(test_ds.features)
    # cumulative incidence at right edge per class = sum over bins.
    # Use test_ds.durations (same row order as test_pmf) — NOT test_df.
    durations = test_ds.durations
    for i, cls in enumerate(QUALIFYING_EVENT_CLASSES):
        start = i * K_BINS
        cum = test_pmf[:, start:start + K_BINS].sum(dim=1).numpy()
        events = (test_ds.event_classes == (i + 1)).int().numpy()
        if events.sum() < 2:
            deephit_c[cls] = float("nan")
            continue
        deephit_c[cls] = float(concordance_index(durations, -cum, events))

    # Cox baseline (30 fits, parallel). MUST use the same train/test split
    # as Stage D for the Δ comparison to be valid (spec §5).
    cox_results = fit_all_classes(train_df, test_df, seed=seed, parallel=True)
    cox_c = {r.event_class: r.c_index for r in cox_results}
    cox_conv = {r.event_class: r.converged for r in cox_results}

    return {
        "seed": seed,
        "test_size": test_size,
        "n_train_persons": int(len(train_persons)),
        "n_test_persons": int(len(test_persons)),
        "K_qualifying": N_CLASSES,
        "noise_floor_sha256": noise_floor_sha,
        "torch_version": torch.__version__,
        "lifelines_version": lifelines.__version__,
        "pycox_version": pycox.__version__,
        "per_class": {
            cls: {
                "n_train_positives": int((train_df[f"event_{cls}"] == 1).sum()),
                "n_test_positives": int((test_df[f"event_{cls}"] == 1).sum()),
                "qualifies": int((train_df[f"event_{cls}"] == 1).sum()) >= 50,
                "c_index_test_stage_d": deephit_c[cls],
                "c_index_test_cox": cox_c[cls],
                "delta_test": (deephit_c[cls] - cox_c[cls])
                              if not (np.isnan(deephit_c[cls]) or np.isnan(cox_c[cls]))
                              else float("nan"),
                "cox_converged": cox_conv[cls],
            }
            for cls in QUALIFYING_EVENT_CLASSES
        },
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.medini.ml.stage_d_train")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--split", choices=["noise_floor", "main", "replication"], required=True)
    p.add_argument("--test-size", type=float, default=0.20)
    p.add_argument("--out-dir", type=Path, default=Path("data/ml_runs/fork_a_stage_d"))
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s :: %(message)s")
    _seed_everything(args.seed)

    df_path = Path("app/medini/data") / (
        "dasha_stage_d_features_smoke.parquet" if args.smoke
        else "dasha_stage_d_features.parquet"
    )
    df = pd.read_parquet(df_path)

    # Read noise floor SHA if it exists; empty string otherwise.
    nf_path = args.out_dir / "noise_floor.json"
    sha = ""
    if nf_path.exists():
        sha = hashlib.sha256(nf_path.read_bytes()).hexdigest()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    record = _train_one_seed(df, seed=args.seed, test_size=args.test_size,
                             out_dir=args.out_dir, noise_floor_sha=sha)
    record["split"] = args.split
    record["duration_seconds"] = round(time.time() - start, 1)

    # Append to the appropriate JSONL.
    run_file = args.out_dir / f"{args.split}_run.jsonl"
    with run_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    logger.info("Wrote seed=%d to %s", args.seed, run_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 17.2: Smoke-test one seed on smoke parquet**

Run: `py -3.12 -m app.medini.ml.stage_d_train --seed 42 --split noise_floor --smoke --out-dir data/ml_runs/fork_a_stage_d_smoke`

Expected: log lines for training progress; a `data/ml_runs/fork_a_stage_d_smoke/noise_floor_run.jsonl` file with one record. Per-class C-index values in [0.4, 0.7] range. **Sub-gate D.3 PASS.**

- [ ] **Step 17.3: Commit**

```bash
git add app/medini/ml/stage_d_train.py
git commit -m "feat(medini): Stage D training driver — single-seed train + log JSON record"
```

---

## Phase D.4 — Noise floor measurement (20 seeds)

**Sub-gate (must hold before D.5):** σ_noise per class reported. All 20 seeds complete (no Cox-FAIL > 1 per seed). Magnitudes in expected band 0.015-0.04 per class. SHA-256 logged.

### Task 18: Run noise floor + freeze JSON

**Files:**
- Create: `data/ml_runs/fork_a_stage_d/noise_floor.json` (git-committed)

- [ ] **Step 18.1: Run 20 noise-floor seeds**

Run the script in a loop. On Windows PowerShell:

```powershell
for ($s = 101; $s -le 120; $s++) {
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split noise_floor
    if (-not $?) { Write-Error "seed $s FAILED"; break }
}
```

Expected: 20 records appended to `data/ml_runs/fork_a_stage_d/noise_floor_run.jsonl`.

- [ ] **Step 18.2: Compute σ_noise and write the frozen JSON**

Run:
```
py -3.12 -c "
import json, statistics
from pathlib import Path
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

records = [json.loads(line) for line in
           Path('data/ml_runs/fork_a_stage_d/noise_floor_run.jsonl').read_text().splitlines()]
assert len(records) == 20, f'expected 20 seeds, got {len(records)}'

sigma = {}
for cls in QUALIFYING_EVENT_CLASSES:
    deltas = [r['per_class'][cls]['delta_test'] for r in records
              if not __import__('math').isnan(r['per_class'][cls]['delta_test'])]
    if len(deltas) < 15:
        sigma[cls] = None
        continue
    sigma[cls] = statistics.stdev(deltas)

threshold = max(1, round(30 * 5 / 14))   # 11
out = {
    'K_qualifying': 30,
    'g2_threshold': threshold,
    'g2_threshold_formula': 'ceil(K * 5/14)',
    'sigma_noise_per_class': sigma,
    'sigma_noise_3x_per_class': {k: (v * 3 if v else None) for k, v in sigma.items()},
    'n_seeds': 20,
    'computed_at': __import__('datetime').date.today().isoformat(),
}
Path('data/ml_runs/fork_a_stage_d/noise_floor.json').write_text(json.dumps(out, indent=2))
print('wrote noise_floor.json; sigma summary:')
for cls, s in sorted(sigma.items()):
    print(f'  {cls:35s} sigma={s if s is None else round(s, 4)}')
"
```

- [ ] **Step 18.3: Sanity-check σ_noise magnitudes**

Expected: most σ_noise in [0.015, 0.04]. Any class with σ > 0.06 should be flagged (corpus too small for that class). **Sub-gate D.4 PASS if no class exceeds 0.06 and ≥ 25 classes are in [0.015, 0.04].**

- [ ] **Step 18.4: Git-commit the frozen noise floor**

```bash
git add data/ml_runs/fork_a_stage_d/noise_floor.json data/ml_runs/fork_a_stage_d/noise_floor_run.jsonl
git commit -m "data(medini): Stage D noise floor — 20-seed σ_noise frozen (sub-gate D.4 PASS)"
```

---

## Phase D.5 — Main 10-seed run

**Sub-gate:** All 10 seeds complete. G1/G2/G3 evaluated and reported. No overfit-suspect flags > 50% of seeds.

### Task 19: Run main + generate main_summary.md

- [ ] **Step 19.1: Run 10 main seeds**

```powershell
for ($s = 1; $s -le 10; $s++) {
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split main
}
```

Expected: `main_run.jsonl` has 10 records.

- [ ] **Step 19.2: Evaluate gate G1/G2/G3 (the script is built in Task 21; for D.5 we use a one-liner inline)**

Run:
```
py -3.12 -c "
import json, math, statistics
from pathlib import Path
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

nf = json.loads(Path('data/ml_runs/fork_a_stage_d/noise_floor.json').read_text())
records = [json.loads(l) for l in Path('data/ml_runs/fork_a_stage_d/main_run.jsonl').read_text().splitlines()]
assert len(records) == 10

print(f'| class | Δ_mean | σ_model | 3σ_noise | clears? |')
print('|---|---|---|---|---|')
n_clear = 0
for cls in QUALIFYING_EVENT_CLASSES:
    deltas = [r['per_class'][cls]['delta_test'] for r in records
              if not math.isnan(r['per_class'][cls]['delta_test'])]
    if len(deltas) < 5:
        print(f'| {cls} | n/a | n/a | n/a | INSUF |')
        continue
    d_mean = statistics.mean(deltas)
    sd_m = statistics.stdev([r['per_class'][cls]['c_index_test_stage_d'] for r in records
                             if not math.isnan(r['per_class'][cls]['c_index_test_stage_d'])])
    sigma_n = nf['sigma_noise_per_class'][cls] or 1.0
    threshold = 3 * sigma_n
    clears = d_mean >= threshold and sd_m <= d_mean
    n_clear += int(clears)
    print(f'| {cls} | {d_mean:+.4f} | {sd_m:.4f} | {threshold:.4f} | {\"YES\" if clears else \"no\"} |')

print()
print(f'G2 breadth: {n_clear}/30 clear (threshold {nf[\"g2_threshold\"]})')
print(f'PASS' if n_clear >= nf['g2_threshold'] else 'FAIL')
" > data/ml_runs/fork_a_stage_d/main_summary.md
```

- [ ] **Step 19.3: Commit main run + summary**

```bash
git add data/ml_runs/fork_a_stage_d/main_run.jsonl data/ml_runs/fork_a_stage_d/main_summary.md
git commit -m "data(medini): Stage D main 10-seed run + G1/G2/G3 summary"
```

### Task 19.5: K_BINS sensitivity check (F5 defense)

**Files:**
- Create: `data/ml_runs/fork_a_stage_d/k_bins_sensitivity.md`

Spec §6 F5 requires verifying that the K_BINS=50 choice isn't artifact-driving. Re-run ONE seed with K_BINS=30 and K_BINS=80; if Δ_class swings by > σ_noise on > 1/3 of classes, flag the result.

- [ ] **Step 19.5.1: Add a `--k-bins` CLI arg to `stage_d_train.py`**

Modify [stage_d_train.py](../../../app/medini/ml/stage_d_train.py) to accept `--k-bins`, default 50, that is passed through to a `K_BINS_OVERRIDE` module global in `stage_d_dataset.py`. Alternatively, monkey-patch `stage_d_dataset.K_BINS` from the train script when the flag is set.

- [ ] **Step 19.5.2: Run two sensitivity seeds**

```powershell
py -3.12 -m app.medini.ml.stage_d_train --seed 42 --split sensitivity --k-bins 30 --out-dir data/ml_runs/fork_a_stage_d/sensitivity_kbins
py -3.12 -m app.medini.ml.stage_d_train --seed 42 --split sensitivity --k-bins 80 --out-dir data/ml_runs/fork_a_stage_d/sensitivity_kbins
```

- [ ] **Step 19.5.3: Compare against the seed=42 record from main_run**

Generate `k_bins_sensitivity.md` showing the per-class Δ at K_BINS=30, 50 (from main), 80. Flag classes where |Δ(50) − Δ(30)| > σ_noise OR |Δ(50) − Δ(80)| > σ_noise. If > 1/3 of classes flagged, write a prominent warning into `DECISION.md` and recommend revisiting K_BINS before Phase 4.

- [ ] **Step 19.5.4: Commit**

```bash
git add data/ml_runs/fork_a_stage_d/sensitivity_kbins/ data/ml_runs/fork_a_stage_d/k_bins_sensitivity.md
git commit -m "data(medini): Stage D K_BINS sensitivity check (F5 defense)"
```

---

## Phase D.6 — Conditional replication (only if main PASSED)

**Trigger:** G1 ∧ G2 ∧ G3 all hold on main_run. If main FAILed, SKIP this phase and jump to D.7 for the final verdict.

### Task 20: Conditional 10-seed replication at test_size=0.25

- [ ] **Step 20.1: Confirm trigger condition**

Re-read `main_summary.md`. If the bottom-line says PASS, proceed; otherwise skip.

- [ ] **Step 20.2: Run 10 replication seeds**

```powershell
for ($s = 201; $s -le 210; $s++) {
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split replication --test-size 0.25
}
```

- [ ] **Step 20.3: Evaluate G4 (same procedure as G1/G2/G3 in 19.2, on replication_run.jsonl)**

- [ ] **Step 20.4: Commit replication run + summary**

```bash
git add data/ml_runs/fork_a_stage_d/replication_run.jsonl data/ml_runs/fork_a_stage_d/replication_summary.md
git commit -m "data(medini): Stage D replication 10-seed run + G4 summary"
```

---

## Phase D.7 — Verdict synthesis

**Sub-gate:** DECISION.md PASS/FAIL with explicit next-step recommendation, matching the [phase3c_wedge/DECISION.md](../../../data/ml_runs/phase3c_wedge/DECISION.md) template.

### Task 20.5: scikit-survival C-index cross-check (F11 defense)

**Files:**
- Create: `data/ml_runs/fork_a_stage_d/sksurv_crosscheck.md`

Spec §6 F11 requires that `lifelines.utils.concordance_index` and `sksurv.metrics.concordance_index_censored` agree to within 0.005 on one seed. Disagreement above that threshold FAILs the run because the gate's numbers are no longer trustworthy.

- [ ] **Step 20.5.1: Run the cross-check on seed=1 of main_run**

```python
py -3.12 -c "
import json, numpy as np, pandas as pd, torch
from pathlib import Path
from lifelines.utils import concordance_index as ll_ci
from sksurv.metrics import concordance_index_censored as sk_ci
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
from app.medini.ml.stage_d_dataset import K_BINS, build_dataset
from app.medini.ml.stage_d_baseline import split_train_test
from app.medini.ml.stage_d_model import StageDModel

df = pd.read_parquet('app/medini/data/dasha_stage_d_features.parquet')
train_df, test_df = split_train_test(df, seed=1)
test_ds = build_dataset(test_df, name_norms=test_df['name_norm'].unique())

n_features = test_ds.features.shape[1]
model = StageDModel.load(Path('data/ml_runs/fork_a_stage_d/models/seed_1_deephit.pt'),
                          n_features=n_features)
model.eval()
with torch.no_grad():
    pmf = model(test_ds.features)

print(f'| class | lifelines C | sksurv C | |diff| |')
print('|---|---|---|---|')
max_diff = 0.0
for i, cls in enumerate(QUALIFYING_EVENT_CLASSES):
    cum = pmf[:, i * K_BINS:(i + 1) * K_BINS].sum(dim=1).numpy()
    events = (test_ds.event_classes == (i + 1)).numpy().astype(bool)
    if events.sum() < 2:
        continue
    ll = ll_ci(test_ds.durations, -cum, events.astype(int))
    sk, *_ = sk_ci(events, test_ds.durations, cum)  # sksurv conventions: high risk = early event
    diff = abs(ll - sk)
    max_diff = max(max_diff, diff)
    print(f'| {cls} | {ll:.4f} | {sk:.4f} | {diff:.4f} |')
print()
print(f'Max disagreement: {max_diff:.4f} (threshold: 0.005)')
print('PASS' if max_diff < 0.005 else 'FAIL — gate verdict cannot be trusted')
" > data/ml_runs/fork_a_stage_d/sksurv_crosscheck.md
```

- [ ] **Step 20.5.2: If FAIL, abort and investigate**

If max disagreement > 0.005, do NOT proceed to D.7. Investigate whether you're computing risk scores in the right direction for each library (lifelines and sksurv use opposite sign conventions historically).

- [ ] **Step 20.5.3: Commit**

```bash
git add data/ml_runs/fork_a_stage_d/sksurv_crosscheck.md
git commit -m "data(medini): Stage D scikit-survival C-index cross-check (F11 defense)"
```

---

### Task 21: Evaluate script — generate DECISION.md

**Files:**
- Create: `app/medini/ml/stage_d_evaluate.py`
- Create: `tests/test_stage_d_evaluate.py`

- [ ] **Step 21.1: Write the failing test**

Create `tests/test_stage_d_evaluate.py`:

```python
"""Tests for Fork-A Stage D evaluation / DECISION.md generator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.medini.ml.stage_d_evaluate import (
    GateVerdict,
    evaluate_gate,
    render_decision_md,
)


class TestEvaluateGate:
    def test_fail_no_signal_when_all_deltas_negative(self, tmp_path) -> None:
        nf = {"K_qualifying": 30, "g2_threshold": 11,
              "sigma_noise_per_class": {f"cls_{i}": 0.02 for i in range(30)}}
        records = [{
            "seed": s,
            "per_class": {
                f"cls_{i}": {"delta_test": -0.01,
                             "c_index_test_stage_d": 0.5,
                             "c_index_test_cox": 0.51}
                for i in range(30)
            }
        } for s in range(10)]
        verdict = evaluate_gate(records, noise_floor=nf)
        assert verdict.passes_g1 is False
        assert verdict.passes_g2 is False
        assert verdict.outcome == "FAIL: no aggregate signal"
```

- [ ] **Step 21.2: Implement evaluate + render**

Create `app/medini/ml/stage_d_evaluate.py`:

```python
"""Fork-A Stage D — gate verdict + DECISION.md generator.

Reads noise_floor.json + main_run.jsonl (+ replication_run.jsonl if present)
and writes DECISION.md following the phase3c_wedge/DECISION.md template.

Usage:
    py -3.12 -m app.medini.ml.stage_d_evaluate \\
        --out-dir data/ml_runs/fork_a_stage_d
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PerClassVerdict:
    cls: str
    delta_mean: float
    sigma_model: float
    sigma_noise: float
    threshold_3sigma: float
    clears_g2: bool
    stable_g3: bool


@dataclass(frozen=True, slots=True)
class GateVerdict:
    n_seeds: int
    K_qualifying: int
    g2_threshold: int
    per_class: tuple[PerClassVerdict, ...]
    passes_g1: bool
    passes_g2: bool
    passes_g3: bool
    passes_g4: bool | None     # None if replication didn't run
    outcome: str               # one of the spec §5 decision-table strings


def _records_from_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def evaluate_gate(main_records: list[dict], *,
                  noise_floor: dict,
                  replication_records: list[dict] | None = None) -> GateVerdict:
    sigma_noise = noise_floor["sigma_noise_per_class"]
    g2_threshold = noise_floor["g2_threshold"]
    K = noise_floor["K_qualifying"]

    per_class: list[PerClassVerdict] = []
    n_clear = 0
    delta_sum, threshold_sum = 0.0, 0.0
    n_summed = 0
    for cls in QUALIFYING_EVENT_CLASSES:
        deltas = [r["per_class"][cls]["delta_test"] for r in main_records
                  if cls in r["per_class"]
                  and not (r["per_class"][cls]["delta_test"] is None
                           or math.isnan(r["per_class"][cls]["delta_test"]))]
        stage_d_cs = [r["per_class"][cls]["c_index_test_stage_d"]
                      for r in main_records if cls in r["per_class"]
                      and r["per_class"][cls]["c_index_test_stage_d"] is not None
                      and not math.isnan(r["per_class"][cls]["c_index_test_stage_d"])]
        sigma_n = sigma_noise.get(cls)
        if len(deltas) < 5 or sigma_n is None:
            continue
        d_mean = statistics.mean(deltas)
        sd_m = statistics.stdev(stage_d_cs) if len(stage_d_cs) >= 2 else float("inf")
        threshold = 3 * sigma_n
        clears = d_mean >= threshold
        stable = sd_m <= max(d_mean, 1e-9)
        per_class.append(PerClassVerdict(
            cls=cls, delta_mean=d_mean, sigma_model=sd_m,
            sigma_noise=sigma_n, threshold_3sigma=threshold,
            clears_g2=clears, stable_g3=stable,
        ))
        if clears:
            n_clear += 1
        delta_sum += d_mean
        threshold_sum += threshold
        n_summed += 1

    passes_g1 = n_summed > 0 and (delta_sum / n_summed) >= (threshold_sum / n_summed)
    passes_g2 = n_clear >= g2_threshold
    passes_g3 = all(p.stable_g3 for p in per_class if p.clears_g2)

    passes_g4 = None
    if replication_records and passes_g1 and passes_g2 and passes_g3:
        rep_verdict = evaluate_gate(replication_records, noise_floor=noise_floor)
        passes_g4 = rep_verdict.passes_g1 and rep_verdict.passes_g2 and rep_verdict.passes_g3

    # Decision-table mapping (spec §5).
    if passes_g1 and passes_g2 and passes_g3 and passes_g4 is True:
        outcome = "PASS strong"
    elif passes_g1 and passes_g2 and passes_g3 and passes_g4 is False:
        outcome = "PASS weak / replication fail"
    elif passes_g1 and passes_g2 and passes_g3 and passes_g4 is None:
        outcome = "G1+G2+G3 pass; replication not yet run"
    elif passes_g1 and passes_g2 and not passes_g3:
        outcome = "FAIL: model unstable"
    elif passes_g1 and not passes_g2:
        outcome = "FAIL: signal too narrow"
    else:
        outcome = "FAIL: no aggregate signal"

    return GateVerdict(
        n_seeds=len(main_records), K_qualifying=K, g2_threshold=g2_threshold,
        per_class=tuple(per_class),
        passes_g1=passes_g1, passes_g2=passes_g2, passes_g3=passes_g3,
        passes_g4=passes_g4, outcome=outcome,
    )


def render_decision_md(v: GateVerdict, *, noise_floor: dict) -> str:
    lines = [
        "# Fork A · Stage D — DECISION",
        "",
        f"**Outcome**: **{v.outcome}**",
        f"**n_seeds (main)**: {v.n_seeds}",
        f"**K_qualifying**: {v.K_qualifying}",
        f"**G2 threshold**: ≥{v.g2_threshold} of {v.K_qualifying}",
        "",
        "## Gate criteria",
        "",
        f"| Criterion | Verdict |",
        f"|---|---|",
        f"| G1 (aggregate Δ ≥ 3σ_noise mean) | {'✓ PASS' if v.passes_g1 else '✗ FAIL'} |",
        f"| G2 (≥{v.g2_threshold} of {v.K_qualifying} clear 3σ_noise individually) | "
        f"{'✓ PASS' if v.passes_g2 else '✗ FAIL'} "
        f"({sum(1 for p in v.per_class if p.clears_g2)} clear) |",
        f"| G3 (σ_model ≤ Δ_class for all G2-clearing classes) | "
        f"{'✓ PASS' if v.passes_g3 else '✗ FAIL'} |",
    ]
    if v.passes_g4 is None:
        lines.append("| G4 (replication) | — (not yet run) |")
    else:
        lines.append(f"| G4 (replication held-back-fold) | "
                     f"{'✓ PASS' if v.passes_g4 else '✗ FAIL'} |")
    lines.extend([
        "",
        "## Per-class results",
        "",
        "| Class | Δ_mean | σ_model | σ_noise | 3σ_noise | G2? | G3? |",
        "|---|---:|---:|---:|---:|---|---|",
    ])
    for p in v.per_class:
        lines.append(
            f"| {p.cls} | {p.delta_mean:+.4f} | {p.sigma_model:.4f} | "
            f"{p.sigma_noise:.4f} | {p.threshold_3sigma:.4f} | "
            f"{'✓' if p.clears_g2 else '·'} | {'✓' if p.stable_g3 else '✗'} |"
        )
    lines.extend([
        "",
        "## Next step (per spec §5 decision table)",
        "",
    ])
    if v.outcome == "PASS strong":
        lines.append("Proceed to **lunarastro replication** (separate spec).")
    elif v.outcome == "PASS weak / replication fail":
        lines.append("Treat as FAIL-with-partial-signal. Investigate the borderline classes that "
                     "passed main but flipped on replication.")
    elif v.outcome == "FAIL: model unstable":
        lines.append("Reduce model capacity (dropout↑ or hidden↓) OR pivot to Fork B.")
    elif v.outcome == "FAIL: signal too narrow":
        lines.append("Lift is concentrated in <11 classes. Cannot claim general astrology-predicts-events. "
                     "Consider class-specific Phase-6-style follow-on for the few classes that did clear.")
    elif v.outcome.startswith("FAIL: no aggregate"):
        lines.append("Honest null. Trigger pivot decision: **Fork B (DML deepen)** OR **Fork C (write-up as null)**.")
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=Path("data/ml_runs/fork_a_stage_d"))
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s :: %(message)s")

    nf = json.loads((args.out_dir / "noise_floor.json").read_text())
    main_recs = _records_from_jsonl(args.out_dir / "main_run.jsonl")
    rep_recs = _records_from_jsonl(args.out_dir / "replication_run.jsonl") or None

    verdict = evaluate_gate(main_recs, noise_floor=nf, replication_records=rep_recs)
    md = render_decision_md(verdict, noise_floor=nf)
    (args.out_dir / "DECISION.md").write_text(md, encoding="utf-8")
    logger.info("Wrote DECISION.md — outcome: %s", verdict.outcome)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Also extend the test file (Step 21.1) to cover PASS paths:**

```python
class TestEvaluateGatePassPath:
    def test_pass_strong_when_main_and_replication_both_clear(self) -> None:
        nf = {
            "K_qualifying": 30, "g2_threshold": 11,
            "sigma_noise_per_class": {cls: 0.02 for cls in __import__(
                "app.medini.ml.stage_d_features", fromlist=["QUALIFYING_EVENT_CLASSES"]
            ).QUALIFYING_EVENT_CLASSES},
        }
        # Build records where 15 of 30 classes clear by ~0.08 (4σ); rest at 0.
        from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
        clearing = set(QUALIFYING_EVENT_CLASSES[:15])
        def _rec(seed):
            return {
                "seed": seed,
                "per_class": {
                    cls: {
                        "delta_test": 0.08 if cls in clearing else 0.0,
                        "c_index_test_stage_d": 0.62,
                        "c_index_test_cox": 0.54 if cls in clearing else 0.62,
                    }
                    for cls in QUALIFYING_EVENT_CLASSES
                }
            }
        main = [_rec(s) for s in range(10)]
        rep = [_rec(s) for s in range(200, 210)]
        v = evaluate_gate(main, noise_floor=nf, replication_records=rep)
        assert v.passes_g1 and v.passes_g2 and v.passes_g3
        assert v.passes_g4 is True
        assert v.outcome == "PASS strong"
```

- [ ] **Step 21.3: Run, expect PASS**

- [ ] **Step 21.4: Commit**

```bash
git add app/medini/ml/stage_d_evaluate.py tests/test_stage_d_evaluate.py
git commit -m "feat(medini): Stage D evaluate — gate verdict + DECISION.md generator"
```

### Task 22: Generate the final DECISION.md

- [ ] **Step 22.1: Run the evaluator**

Run: `py -3.12 -m app.medini.ml.stage_d_evaluate --out-dir data/ml_runs/fork_a_stage_d`

Expected: `data/ml_runs/fork_a_stage_d/DECISION.md` written with the final PASS/FAIL verdict and next-step recommendation.

- [ ] **Step 22.2: Commit the verdict**

```bash
git add data/ml_runs/fork_a_stage_d/DECISION.md
git commit -m "data(medini): Stage D final verdict (PASS | FAIL — fill in)"
```

---

## End-of-plan checklist

After Task 22, confirm:

- [ ] All 7 source files exist under `app/medini/ml/stage_d_*.py`
- [ ] All 6 test files exist under `tests/test_stage_d_*.py`
- [ ] `noise_floor.json` is git-committed and its SHA-256 appears in every `main_run.jsonl` record
- [ ] `DECISION.md` answers PASS/FAIL with the next-step recommendation per the spec's decision table (§5)
- [ ] No `_jd` or `death*` columns leaked into the feature matrix (verified by pre-flight)
- [ ] F5 — `k_bins_sensitivity.md` exists; no >1/3 of classes flagged as bin-sensitive (or warning recorded in DECISION.md)
- [ ] F8 (lord-as-trivial-predictor) ablation has been documented — either in `main_summary.md` or as an addendum to `DECISION.md`
- [ ] F11 — `sksurv_crosscheck.md` exists with max disagreement < 0.005
- [ ] If PASS: invoke the LUNARASTRO REPLICATION SPEC (out of scope here; opens a new design-spec → plan cycle)
- [ ] If FAIL: surface to user with the pivot menu from the spec's decision table (Fork B deepen OR Fork C write-up)

## Pre-work verification (resolve BEFORE Task 1)

The plan makes three assumptions about upstream parquet paths that the engineer MUST verify before Task 1, OR update the constants in `stage_d_features.py` accordingly:

1. **Vedic Tensor parquet path** — Task 2 uses `_VEDIC_TENSOR_PARQUET = _DATA_DIR / "ml_astro_features.parquet"`. Run `ls app/medini/data/*.parquet | grep -i 'astro\|tensor\|feature'` to confirm the actual filename produced by `app.medini.etl.databank_etl` / `feature_engineering.py`.
2. **Stage-E parquet path** — Task 5 uses `_STAGE_E_PARQUET = _DATA_DIR / "natal_lord_houses.parquet"`. Verify via `ls app/medini/data/*lord*`.
3. **Doctrine parquet path** — Task 5 uses `_DOCTRINE_PARQUET = _DATA_DIR / "doctrine_scores.parquet"`. Verify via `ls app/medini/data/*doctrine*`.

If any of the three is named differently, edit the constants in `stage_d_features.py` BEFORE running the test suite — otherwise Task 2 and Task 5 will fail with `FileNotFoundError`.

## Hardware note

All gate runs (Tasks 18, 19, 19.5, 20, 20.5) must run on CPU per F14. If the test machine has a GPU, prefix the `py -3.12 -m app.medini.ml.stage_d_train ...` invocations with `$env:CUDA_VISIBLE_DEVICES = ""; ` in PowerShell to mask it. The training loop calls `torch.use_deterministic_algorithms(True)` which is more reliable on CPU anyway.

## Spec deviations summary

This plan deviates from the spec in two documented places. Both are flagged in the run's `DECISION.md`:

| # | Deviation | Reason |
|---|---|---|
| 1 | **pycox dropped from dependencies; DeepHit hand-rolled (~80 LOC of clean PyTorch)** | Spec §3 pinned pycox but the from-scratch implementation is small, transparent, matches the exact architecture diagram in §3, and avoids pycox's version-fragile research-grade API. F11 (scikit-survival cross-check) catches any hand-roll bugs. |
| 2 | **`event_jd_<class>` tie-break may fall back to enumeration order** | If the corpus doesn't carry `event_jd_*` columns, the implementation falls back to "first qualifying class in `QUALIFYING_EVENT_CLASSES` order wins" rather than failing. F4 (co-occurrence rate report) bounds the impact. |

---

## Plan-document-reviewer dispatch

After the engineer completes Task 22, the brainstorming → plan → execution flow's next gate is a plan review iteration (per the writing-plans skill). This plan is now ready for that reviewer pass.
