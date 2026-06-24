"""Phase-3C-take-2 ETL step 2: lunarastro natal parquet → per-class screening cohorts.

Reads ``lunarastro_natal.parquet`` (output of step 1) and emits one
screening cohort per event class:

* ``lunarastro_career.parquet``
* ``lunarastro_fame.parquet``
* ``lunarastro_marriage.parquet``
* ``lunarastro_health.parquet``
* (more on demand)

Each cohort is binary-labelled (``is_event_X``) with era-stratified
negatives sampled (without replacement) from rows whose ``tags`` field
does NOT match any of the class's tag patterns.

Why this is needed:
    The downstream eval (``add_yoga_features.py`` + ``wedge_eval_v2.py``)
    expects an ``is_event_X`` (or ``is_event``) target column and
    grouping by ``name_norm``. Lunarastro ships each person as a single
    row with a free-form ``tags`` field; the binary screening view is
    derived from that field.

Two design choices documented in the file:
    1. **Granular tag mapping**: we use specific tags
       (``Career`` / ``Job`` / ``Profession``) rather than the broad
       ``Vocation`` (which is on 60% of all rows and would make the
       task trivially easy). This keeps positive rates in the
       10-30% range matching the Astro-Databank screening cohorts.
    2. **Era-stratified negative sampling**: for each positive
       birth-decade, sample ``neg_ratio`` negatives from the same
       decade if available. Prevents trivial era-decoding.

Usage:
    python -m app.medini.etl.lunarastro_to_screening \\
        --input  app/medini/data/lunarastro_natal.parquet \\
        --output-dir app/medini/data/ \\
        --class career fame \\
        [--neg-ratio 2] [--min-birth-time-confidence 0.5] [--seed 42]
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Tag → event-class mapping (granular by default)                              #
# --------------------------------------------------------------------------- #

# Each class names the tag patterns that mark a row as a positive. Matching
# is case-insensitive substring against each semicolon-split tag.
# Choose tags that map cleanly to the classical event class; deliberately
# avoid the catch-all ``Vocation`` (21k rows) so positive rate stays in
# the same 10-30% range as the Astro-Databank screening cohorts.

@dataclass(frozen=True, slots=True)
class _ClassDef:
    name: str
    positive_patterns: tuple[str, ...]
    # Broad tags that should NOT contribute to negatives either —
    # treat them as "ambiguously related" rather than confirmed negative.
    abstain_patterns: tuple[str, ...] = ()


_CLASS_DEFS: dict[str, _ClassDef] = {
    "career": _ClassDef(
        name="career",
        positive_patterns=(
            r"\bcareer\b", r"\bjob\b", r"\bprofession\b",
            r"\bcareerpath\b", r"\bbusiness\b", r"\bfinancial\b",
        ),
        # Vocation/Work are too broad — used by the corpus as "this person
        # does some job" rather than a career event. Abstain from sampling
        # those as either positive or negative.
        abstain_patterns=(r"\bvocation\b", r"\bwork\b"),
    ),
    "fame": _ClassDef(
        name="fame",
        positive_patterns=(
            r"\bawards?\b", r"\bfamous\b", r"\bnotable\b",
            r"\bprize\b", r"\bmedal\b", r"\bhonou?r\b",
        ),
    ),
    "marriage": _ClassDef(
        name="marriage",
        positive_patterns=(r"\bmarriage\b", r"\bmarriages?\b", r"\bwedding\b"),
        abstain_patterns=(r"\brelationship\b",),
    ),
    "death": _ClassDef(
        name="death",
        positive_patterns=(r"\bdeath\b", r"\bdied\b", r"\bdemise\b", r"\bdeceased\b"),
        abstain_patterns=(),
    ),
    "health": _ClassDef(
        name="health",
        positive_patterns=(
            r"\bhealth\b", r"\bdiagnoses\b", r"\bmajor diseases\b",
            r"\bbody part problems\b", r"\billness\b",
        ),
    ),
    "spiritual": _ClassDef(
        name="spiritual",
        positive_patterns=(
            r"\breligion/spirituality\b", r"\bspiritual\b", r"\boccult fields\b",
        ),
    ),
    "politics": _ClassDef(
        name="politics",
        positive_patterns=(
            r"\bpolitics?\b", r"\bmilitary\b",
        ),
    ),
}


def _row_matches(tags: str, patterns: tuple[str, ...]) -> bool:
    """True iff any pattern matches any semicolon-split tag (case-insensitive)."""
    if not tags or not patterns:
        return False
    for raw in str(tags).split(";"):
        token = raw.strip().lower()
        if not token:
            continue
        for pat in patterns:
            if re.search(pat, token):
                return True
    return False


# --------------------------------------------------------------------------- #
# Cohort builder                                                               #
# --------------------------------------------------------------------------- #

def _label_rows(df: pd.DataFrame, class_def: _ClassDef) -> pd.DataFrame:
    """Add columns ``is_positive`` and ``abstain`` (boolean) for a class."""
    out = df.copy()
    tags_series = out["tags"].fillna("").astype(str)
    out["is_positive"] = tags_series.apply(
        lambda t: _row_matches(t, class_def.positive_patterns)
    )
    out["abstain"] = tags_series.apply(
        lambda t: _row_matches(t, class_def.abstain_patterns)
    )
    # Positives override abstain — if a row matches both, it's a clean positive.
    out.loc[out["is_positive"], "abstain"] = False
    return out


def _stratified_negative_sample(
    positives: pd.DataFrame,
    negative_pool: pd.DataFrame,
    *,
    neg_ratio: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Sample negatives from ``negative_pool`` matching positive birth-decade dist."""
    if len(positives) == 0:
        return negative_pool.iloc[:0]

    target = int(round(neg_ratio * len(positives)))
    if target <= 0:
        return negative_pool.iloc[:0]

    pos_dec_counts = positives["birth_decade"].value_counts()
    # Per-decade target = round(neg_ratio * pos_count_for_that_decade).
    neg_pool_by_dec = negative_pool.groupby("birth_decade")

    chosen_indices: list[int] = []
    for decade, pos_n in pos_dec_counts.items():
        n_want = int(round(neg_ratio * pos_n))
        if n_want <= 0:
            continue
        try:
            dec_pool = neg_pool_by_dec.get_group(decade)
        except KeyError:
            continue
        n_avail = len(dec_pool)
        n_take = min(n_want, n_avail)
        if n_take == 0:
            continue
        # Sample without replacement.
        picked = rng.choice(dec_pool.index.to_numpy(), size=n_take, replace=False)
        chosen_indices.extend(int(i) for i in picked)

    return negative_pool.loc[chosen_indices]


def build_one_class(
    natal_df: pd.DataFrame,
    class_def: _ClassDef,
    *,
    neg_ratio: float,
    min_birth_time_confidence: float,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Construct the screening parquet body for one class."""
    df = natal_df.copy()
    pre_conf = len(df)
    df = df[df["birth_time_confidence"] >= min_birth_time_confidence].copy()
    after_conf = len(df)

    labelled = _label_rows(df, class_def)
    positives = labelled[labelled["is_positive"]]
    negative_pool = labelled[~labelled["is_positive"] & ~labelled["abstain"]]

    rng = np.random.default_rng(seed)
    sampled_negatives = _stratified_negative_sample(
        positives, negative_pool, neg_ratio=neg_ratio, rng=rng,
    )

    cohort = pd.concat([positives, sampled_negatives], axis=0, ignore_index=False)
    cohort["is_event_X"] = cohort["is_positive"].astype(int)
    cohort = cohort.drop(columns=["is_positive", "abstain"], errors="ignore")

    # Drop name duplicates (keep first) so GroupShuffleSplit-by-name doesn't
    # leak. Lunarastro has ~3200 dupes (e.g. Einstein × 2).
    cohort = cohort.drop_duplicates(subset=["name_norm"], keep="first")

    summary = {
        "input_rows": int(pre_conf),
        "after_confidence_filter": int(after_conf),
        "n_positives": int(positives["name_norm"].nunique()),
        "n_negatives_pool": int(negative_pool["name_norm"].nunique()),
        "n_negatives_sampled": int(sampled_negatives["name_norm"].nunique()),
        "cohort_rows": int(len(cohort)),
        "cohort_unique_people": int(cohort["name_norm"].nunique()),
        "base_rate_pct": round(100.0 * cohort["is_event_X"].mean(), 2),
    }
    return cohort, summary


def run(
    natal_parquet: Path,
    output_dir: Path,
    classes: list[str],
    *,
    neg_ratio: float,
    min_birth_time_confidence: float,
    seed: int,
) -> dict[str, dict[str, int]]:
    natal_df = pd.read_parquet(natal_parquet)
    logger.info("loaded %s shape=%s", natal_parquet, natal_df.shape)

    output_dir.mkdir(parents=True, exist_ok=True)
    all_stats: dict[str, dict[str, int]] = {}
    for cls in classes:
        if cls not in _CLASS_DEFS:
            logger.warning("skipping unknown class %r (known: %s)",
                           cls, sorted(_CLASS_DEFS))
            continue
        class_def = _CLASS_DEFS[cls]
        cohort, summary = build_one_class(
            natal_df, class_def,
            neg_ratio=neg_ratio,
            min_birth_time_confidence=min_birth_time_confidence,
            seed=seed,
        )
        out_path = output_dir / f"lunarastro_{cls}.parquet"
        cohort.to_parquet(out_path, index=False)
        summary["output_path"] = str(out_path)
        all_stats[cls] = summary
        logger.info(
            "wrote %s rows=%d unique=%d base_rate=%.1f%%",
            out_path, summary["cohort_rows"],
            summary["cohort_unique_people"], summary["base_rate_pct"],
        )
    return all_stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.lunarastro_to_screening",
        description="Build per-class screening cohorts from the lunarastro natal parquet.",
    )
    parser.add_argument(
        "--input", type=Path,
        default=Path("app/medini/data/lunarastro_natal.parquet"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("app/medini/data/"),
    )
    parser.add_argument(
        "--class", dest="classes", nargs="+",
        default=["career", "fame"],
        help=f"Event classes to build. Known: {sorted(_CLASS_DEFS)}",
    )
    parser.add_argument("--neg-ratio", type=float, default=2.0)
    parser.add_argument("--min-birth-time-confidence", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not args.input.exists():
        print(f"ERROR input not found: {args.input}", file=sys.stderr)
        return 2

    stats = run(
        args.input, args.output_dir, args.classes,
        neg_ratio=args.neg_ratio,
        min_birth_time_confidence=args.min_birth_time_confidence,
        seed=args.seed,
    )
    print()
    print(f"=== Screening cohort build complete ===")
    for cls, s in stats.items():
        print(f"  [{cls}] rows={s['cohort_rows']} unique_people={s['cohort_unique_people']} "
              f"positives={s['n_positives']} base_rate={s['base_rate_pct']}% "
              f"-> {s['output_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
