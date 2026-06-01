"""Stage D follow-up: within-person concordance test using GPU DeepHit checkpoints.

The 4 prior null verdicts were all between-person tests. None asked: within a
SINGLE person whose chart is fixed, do the dasha windows the trained DeepHit
model rates as high-cumulative-incidence actually contain more events than the
windows rated low?

Within-person factors out every person-level confound (birth year, ascendant,
documentation density, selection bias). Within a person, chart features are
constant; only dasha-time features vary. If real structural signal exists, this
is where it survives.

**Implementation uses the trained DeepHit checkpoints** (`seed_*_deephit.pt`)
from the Stage D 5-seed gate, NOT a re-fit of Cox. The DeepHit model already
encodes the same train/test split (via deterministic split_train_test(seed=k)),
so a single GPU forward pass on the test features gives per-window cumulative
incidence per class. Total runtime: seconds per seed, not 20+ minutes.

Usage:
    py -3.12 -m app.medini.ml.stage_d_within_person \\
        --seeds 1 2 3 4 5 \\
        --classes fame career business finance marriage \\
        --device dml \\
        --out data/ml_runs/fork_a_stage_d_subsample/within_person_dml.md
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from app.medini.ml.stage_d_baseline import split_train_test
from app.medini.ml.stage_d_dataset import K_BINS, build_dataset
from app.medini.ml.stage_d_device import device_label, resolve_device
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
from app.medini.ml.stage_d_model import StageDModel

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WithinPersonResult:
    event_class: str
    seed: int
    n_test_positives: int
    n_concordant: int
    n_discordant: int
    n_ties: int
    n_pairs: int
    n_persons_with_pairs: int
    concordance: float
    p_value_perm: float


def _within_person_concordance(
    person_ids: np.ndarray, events: np.ndarray, risks: np.ndarray,
) -> tuple[int, int, int, int]:
    """Pairwise concordance restricted to within-person (event, non-event) pairs.

    All arrays MUST be in the same row order. Vectorized per-person via numpy
    broadcasting. Returns (n_concordant, n_discordant, n_ties, n_persons).
    """
    # Group rows by person via a sort. argsort is O(n log n); subsequent
    # iteration over unique persons is O(n).
    order = np.argsort(person_ids, kind="stable")
    p_sorted = person_ids[order]
    e_sorted = events[order]
    r_sorted = risks[order]
    # Find run boundaries (each person is a contiguous slice in the sort).
    # Boundaries = positions where person ID changes. np.diff fails on strings,
    # so compare adjacent elements directly (works for any dtype).
    boundaries = np.flatnonzero(p_sorted[1:] != p_sorted[:-1]) + 1
    starts = np.concatenate(([0], boundaries))
    ends = np.concatenate((boundaries, [len(p_sorted)]))

    nc = nd = nt = 0
    persons = 0
    for s, e in zip(starts, ends):
        ev = e_sorted[s:e]
        if not ev.any():       # this person has no events for the class
            continue
        if ev.all():           # this person has no non-events
            continue
        persons += 1
        rs = r_sorted[s:e]
        ev_h = rs[ev == 1]
        ne_h = rs[ev == 0]
        diff = ev_h[:, None] - ne_h[None, :]
        nc += int((diff > 0).sum())
        nd += int((diff < 0).sum())
        nt += int((diff == 0).sum())
    return nc, nd, nt, persons


def _permutation_p(
    person_ids: np.ndarray, events: np.ndarray, risks: np.ndarray,
    *, observed_c: float, n_perm: int, seed: int,
) -> float:
    """One-sided permutation p-value. Shuffle event labels WITHIN each person."""
    rng = np.random.default_rng(seed)
    order = np.argsort(person_ids, kind="stable")
    p_sorted = person_ids[order]
    e_sorted = events[order].copy()
    r_sorted = risks[order]
    # Boundaries = positions where person ID changes. np.diff fails on strings,
    # so compare adjacent elements directly (works for any dtype).
    boundaries = np.flatnonzero(p_sorted[1:] != p_sorted[:-1]) + 1
    starts = np.concatenate(([0], boundaries))
    ends = np.concatenate((boundaries, [len(p_sorted)]))

    n_geq = 0
    for _ in range(n_perm):
        # Shuffle within each person's slice.
        for s, e in zip(starts, ends):
            if e - s >= 2:
                rng.shuffle(e_sorted[s:e])
        # Inline concordance count (skip extra arg-sort since we're already sorted).
        nc = nd = nt = 0
        for s, e in zip(starts, ends):
            ev = e_sorted[s:e]
            if not ev.any() or ev.all():
                continue
            rs = r_sorted[s:e]
            ev_h = rs[ev == 1]
            ne_h = rs[ev == 0]
            diff = ev_h[:, None] - ne_h[None, :]
            nc += int((diff > 0).sum())
            nd += int((diff < 0).sum())
            nt += int((diff == 0).sum())
        total = nc + nd + nt
        if total == 0:
            continue
        c_perm = (nc + 0.5 * nt) / total
        if c_perm >= observed_c:
            n_geq += 1
    return (n_geq + 1) / (n_perm + 1)


def _evaluate_seed(
    df: pd.DataFrame, *, seed: int, classes: list[str], device: torch.device,
    n_perm: int, models_dir: Path,
) -> list[WithinPersonResult]:
    """Run one seed: rebuild split, load checkpoint, forward pass, per-class concordance."""
    t0 = time.time()
    train_df, test_df = split_train_test(df, seed=seed)
    test_persons = test_df["name_norm"].unique()
    test_ds = build_dataset(test_df, name_norms=test_persons)
    # build_dataset filters via isin + reset_index. Since name_norms covers all
    # test persons (no filtering), the row order of test_ds matches
    # test_df.reset_index(drop=True). Confirm the length matches as a guard.
    test_meta = test_df.reset_index(drop=True)
    assert len(test_meta) == len(test_ds.features), (
        f"row alignment mismatch: meta={len(test_meta)} ds={len(test_ds.features)}"
    )
    n_features = test_ds.features.shape[1]

    ckpt = models_dir / f"seed_{seed}_deephit.pt"
    model = StageDModel.load(ckpt, n_features=n_features).to(device)
    model.eval()
    with torch.no_grad():
        pmf = model(test_ds.features.to(device)).detach().cpu().numpy()
    logger.info("seed=%d forward pass done in %.1fs (pmf shape %s)",
                seed, time.time() - t0, pmf.shape)

    person_ids = test_meta["name_norm"].to_numpy()
    results: list[WithinPersonResult] = []
    for cls in classes:
        if cls not in QUALIFYING_EVENT_CLASSES:
            logger.warning("class %s not in QUALIFYING_EVENT_CLASSES; skip", cls)
            continue
        cls_idx = QUALIFYING_EVENT_CLASSES.index(cls)
        start = cls_idx * model.k_bins
        # Cumulative incidence for the class = sum over its K bins (excludes the
        # censored bucket). Higher = model thinks this window more likely to
        # produce this event class.
        cum = pmf[:, start:start + model.k_bins].sum(axis=1)
        event_col = f"event_{cls}"
        if event_col not in test_meta.columns:
            logger.warning("missing %s in test_meta; skip", event_col)
            continue
        events = test_meta[event_col].to_numpy().astype(np.int8)
        n_pos = int(events.sum())
        nc, nd, nt, n_persons = _within_person_concordance(person_ids, events, cum)
        n_pairs = nc + nd + nt
        if n_pairs == 0:
            results.append(WithinPersonResult(
                event_class=cls, seed=seed, n_test_positives=n_pos,
                n_concordant=0, n_discordant=0, n_ties=0, n_pairs=0,
                n_persons_with_pairs=0, concordance=float("nan"),
                p_value_perm=float("nan"),
            ))
            continue
        concordance = (nc + 0.5 * nt) / n_pairs
        p_perm = (_permutation_p(person_ids, events, cum,
                                 observed_c=concordance, n_perm=n_perm, seed=seed)
                  if n_perm > 0 else float("nan"))
        results.append(WithinPersonResult(
            event_class=cls, seed=seed, n_test_positives=n_pos,
            n_concordant=nc, n_discordant=nd, n_ties=nt, n_pairs=n_pairs,
            n_persons_with_pairs=n_persons,
            concordance=concordance, p_value_perm=p_perm,
        ))
        logger.info(
            "  cls=%-20s n_pos=%3d  c_within=%.4f  n_pairs=%5d  persons=%3d  p_perm=%.4f",
            cls, n_pos, concordance, n_pairs, n_persons, p_perm,
        )

    # Free memory before next seed.
    del model, pmf, test_ds
    if device.type == "privateuseone":
        try:
            import torch_directml
            torch_directml.empty_cache()
        except (ImportError, AttributeError):
            pass
    elif device.type == "cuda":
        torch.cuda.empty_cache()
    return results


def _render_report(all_results: list[WithinPersonResult], *,
                   seeds: list[int], device: str) -> str:
    lines = [
        "# Stage D follow-up · Within-person concordance (DeepHit, GPU)",
        "",
        f"**Seeds**: {seeds}",
        f"**Device**: {device}",
        f"**Substrate**: subsample_2000p (1.2M rows / 2000 persons)",
        "**Risk source**: per-class cumulative incidence from the trained DeepHit",
        "checkpoints in `data/ml_runs/fork_a_stage_d_subsample/models/seed_*_deephit.pt`.",
        "",
        "## Background",
        "",
        "Within a single person, chart features are constant. Only dasha-time",
        "features vary. This test asks: does the trained DeepHit model rank a",
        "person's actual event-windows higher than their non-event-windows?",
        "",
        "If yes (concordance > 0.55, p < 0.05), there is recoverable within-person",
        "dasha-time signal even though between-person prediction failed (Δ=-0.16).",
        "",
        "## Per-(seed, class) results",
        "",
        "| Seed | Class | n_pos | n_pairs | n_persons | C_within | p_perm |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for r in all_results:
        lines.append(
            f"| {r.seed} | {r.event_class} | {r.n_test_positives} | {r.n_pairs} | "
            f"{r.n_persons_with_pairs} | {r.concordance:.4f} | {r.p_value_perm:.4f} |"
        )
    # Per-class aggregate over seeds.
    lines.extend(["", "## Per-class aggregate (mean over seeds)", "",
                  "| Class | n_seeds | mean C_within | min | max | min p_perm |",
                  "|---|---:|---:|---:|---:|---:|"])
    by_class: dict[str, list[WithinPersonResult]] = {}
    for r in all_results:
        by_class.setdefault(r.event_class, []).append(r)
    for cls, rs in by_class.items():
        finite = [r for r in rs if r.n_pairs > 0]
        if not finite:
            continue
        cs = [r.concordance for r in finite]
        ps = [r.p_value_perm for r in finite if r.p_value_perm == r.p_value_perm]
        lines.append(
            f"| {cls} | {len(finite)} | {sum(cs)/len(cs):.4f} | "
            f"{min(cs):.4f} | {max(cs):.4f} | "
            f"{min(ps) if ps else float('nan'):.4f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- **C_within** = pairwise concordance over within-person (event, non_event) pairs.",
        "  0.5 = chance.",
        "- **p_perm** = one-sided permutation test, shuffling event labels within each",
        "  person (preserves per-person event counts).",
        "",
        "If most per-class mean C_within values cluster around 0.50 with p > 0.05,",
        "the within-person signal is also null and the prediction question is closed",
        "across all 5 of: 3-corpus doctrine, XGBoost date-controlled, LLM real-vs-shuffled,",
        "Stage D DeepHit between-person, and Stage D DeepHit within-person.",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.medini.ml.stage_d_within_person")
    p.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    p.add_argument("--classes", nargs="+", default=None,
                   help="Default: top-5 by test-positive count on seed=1.")
    p.add_argument("--device", type=str, default="auto",
                   choices=("auto", "dml", "cuda", "cpu"))
    p.add_argument("--n-perm", type=int, default=1000)
    p.add_argument("--features", type=Path,
                   default=Path("app/medini/data/dasha_stage_d_features_subsample.parquet"))
    p.add_argument("--models-dir", type=Path,
                   default=Path("data/ml_runs/fork_a_stage_d_subsample/models"))
    p.add_argument("--out", type=Path,
                   default=Path("data/ml_runs/fork_a_stage_d_subsample/within_person_dml.md"))
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s :: %(message)s")
    device = resolve_device(args.device)
    logger.info("Using device: %s", device_label(device))

    logger.info("Loading %s", args.features)
    df = pd.read_parquet(args.features)

    if args.classes is None:
        # Auto-pick top-5 by test positives on the first seed.
        _, test0 = split_train_test(df, seed=args.seeds[0])
        positives = {
            c: int(test0[f"event_{c}"].sum())
            for c in QUALIFYING_EVENT_CLASSES if f"event_{c}" in test0.columns
        }
        top = sorted(positives.items(), key=lambda kv: -kv[1])[:5]
        args.classes = [c for c, _ in top]
        logger.info("Auto-picked top-5 classes (by seed=%d positives): %s",
                    args.seeds[0], top)

    all_results: list[WithinPersonResult] = []
    for s in args.seeds:
        try:
            all_results.extend(_evaluate_seed(
                df, seed=s, classes=args.classes, device=device,
                n_perm=args.n_perm, models_dir=args.models_dir,
            ))
        except Exception as e:
            logger.exception("seed %d failed: %s", s, e)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        _render_report(all_results, seeds=args.seeds, device=device_label(device)),
        encoding="utf-8",
    )
    jpath = args.out.with_suffix(".json")
    jpath.write_text(json.dumps([asdict(r) for r in all_results], indent=2))
    logger.info("Wrote %s + %s", args.out, jpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
