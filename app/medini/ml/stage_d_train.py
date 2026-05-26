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
from app.medini.ml.stage_d_device import device_label, resolve_device
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
from app.medini.ml.stage_d_model import (N_CLASSES, StageDModel, deephit_loss)

logger = logging.getLogger(__name__)

EPOCHS = 200
PATIENCE = 20
LR = 1e-3
WEIGHT_DECAY = 1e-4
# BATCH_SIZE bumped 256 -> 1024 to exploit DML throughput. At 2000p
# (1.2M rows), 256 made DeepHit ~3.3h/seed. The bigger batch reduces
# fwd/bwd calls per epoch ~4x. AMD 9060 XT (16 GB VRAM) easily holds
# the activations (~12 MB / batch at K_BINS=50, n_classes=30, hidden=256).
# Note: gradient noise scales ~1/sqrt(batch), so val_loss convergence
# behaviour may shift slightly; spec's hand-rolled DeepHit doesn't have
# a published hyperparam scan, so this is a defensible tuning choice.
BATCH_SIZE = 1024
VAL_FRAC = 0.20


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    # DirectML has its own RNG state. Seed it too when available — otherwise
    # the same code path produces different DML weight init across seeds.
    try:
        import torch_directml
        torch_directml.manual_seed_all(seed)
    except (ImportError, AttributeError):
        pass
    torch.use_deterministic_algorithms(True, warn_only=True)


def _train_one_seed(df: pd.DataFrame, *, seed: int, test_size: float,
                    out_dir: Path, noise_floor_sha: str,
                    k_bins: int | None = None,
                    device: torch.device | None = None) -> dict:
    # `device` lets the trainer push DeepHit to DirectML/CUDA while Cox
    # stays on CPU (lifelines is CPU-only). Default None → CPU.
    if device is None:
        device = torch.device("cpu")
    # Resolve k_bins FIRST so the dataset and model agree.
    # Default is the imported K_BINS=50; F5 sensitivity overrides via the
    # explicit kwarg (preferred) or via _train_one_seed._k_bins_override
    # (legacy attribute hook). Either path resolves before any build_dataset call.
    if k_bins is None:
        k_bins = getattr(_train_one_seed, "_k_bins_override", None) or K_BINS

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

    # Pass k_bins to build_dataset so the dataset's time_bin assignments
    # use the same bin grid as the model. Without this, --k-bins 30 would
    # crash with an OOB index in deephit_loss because the dataset would
    # still emit time_bins in [0, 49] while the PMF has only 30 cells/class.
    train_ds = build_dataset(sub_train_df, name_norms=sub_train_persons, k_bins=k_bins)
    val_ds = build_dataset(val_df, name_norms=val_persons, k_bins=k_bins)
    test_ds = build_dataset(test_df, name_norms=test_persons, k_bins=k_bins)

    n_features = train_ds.features.shape[1]
    model = StageDModel(n_features=n_features, k_bins=k_bins).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

    best_val = float("inf")
    best_state = None  # always lives on CPU for save() portability
    patience_left = PATIENCE
    for epoch in range(EPOCHS):
        model.train()
        for feats, time_bins, event_classes in train_loader:
            feats = feats.to(device, non_blocking=True)
            time_bins = time_bins.to(device, non_blocking=True)
            event_classes = event_classes.to(device, non_blocking=True)
            optimizer.zero_grad()
            pmf = model(feats)
            loss = deephit_loss(pmf, time_bins, event_classes, k_bins=model.k_bins)
            assert torch.isfinite(loss).all(), f"non-finite loss epoch {epoch}"
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_losses = []
            for feats, time_bins, event_classes in val_loader:
                feats = feats.to(device, non_blocking=True)
                time_bins = time_bins.to(device, non_blocking=True)
                event_classes = event_classes.to(device, non_blocking=True)
                pmf = model(feats)
                val_losses.append(float(
                    deephit_loss(pmf, time_bins, event_classes, k_bins=model.k_bins)
                ))
            val_loss = float(np.mean(val_losses))
        scheduler.step(val_loss)

        if val_loss < best_val - 1e-4:
            best_val = val_loss
            # Snapshot to CPU so save() works without device-specific tensors
            # in the checkpoint (and so load() with map_location='cpu' works).
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_left = PATIENCE
        else:
            patience_left -= 1
            if patience_left <= 0:
                logger.info("Early stop at epoch %d (val=%.4f)", epoch, best_val)
                break

    if best_state is not None:
        model.load_state_dict(best_state)  # back onto the GPU
    model_path = out_dir / "models" / f"seed_{seed}_deephit.pt"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)

    # Per-class C-index for Stage D.
    from lifelines.utils import concordance_index
    deephit_c: dict[str, float] = {}
    model.eval()
    with torch.no_grad():
        # Move test features to device; the resulting pmf comes back to CPU
        # because concordance_index runs on numpy arrays.
        test_pmf = model(test_ds.features.to(device)).detach().cpu()
    durations = test_ds.durations
    for i, cls in enumerate(QUALIFYING_EVENT_CLASSES):
        start = i * model.k_bins
        cum = test_pmf[:, start:start + model.k_bins].sum(dim=1).numpy()
        events = (test_ds.event_classes == (i + 1)).int().numpy()
        if events.sum() < 2:
            deephit_c[cls] = float("nan")
            continue
        deephit_c[cls] = float(concordance_index(durations, -cum, events))

    # Free DeepHit memory before launching Cox workers — the DML model +
    # train/val/test datasets + best_state hold ~10 GB of GPU/host RAM, and
    # each Cox worker malloc's ~1 GB for pyarrow's parquet read at subsample
    # scale. Without this cleanup, ~7 concurrent worker initializers OOM
    # with ArrowMemoryError. Order matters: clear references, then gc, then
    # try to drop the DML allocator's cached blocks.
    import gc
    del model, optimizer, scheduler, train_loader, val_loader
    del train_ds, val_ds, test_ds, best_state, test_pmf
    gc.collect()
    if device.type == "privateuseone":  # DirectML
        try:
            import torch_directml
            torch_directml.empty_cache()
        except (ImportError, AttributeError):
            pass
    elif device.type == "cuda":
        torch.cuda.empty_cache()

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
        "deephit_implementation": "hand-rolled (see spec-deviation note in plan)",
        "device": device_label(device),
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
    # Loose --split accept: noise_floor/main/replication are the spec set;
    # `sensitivity_kbins{30,80}` etc. are used by Task 19.5 F5 defense.
    p.add_argument("--split", type=str, required=True,
                   help="Output JSONL bucket name (noise_floor/main/replication/sensitivity_kbins30/...)")
    p.add_argument("--test-size", type=float, default=0.20)
    p.add_argument("--out-dir", type=Path, default=Path("data/ml_runs/fork_a_stage_d"))
    # --smoke / --subsample / (default = full corpus) are mutually exclusive.
    # Subsample = 2000 randomly-sampled persons (~1.2M rows). Same shape as
    # full but fits Cox in ~2 GB; verdict carries an "n=2000 subsample" footnote.
    corpus = p.add_mutually_exclusive_group()
    corpus.add_argument("--smoke", action="store_true",
                        help="Use 100-person smoke parquet (~60K rows).")
    corpus.add_argument("--subsample", action="store_true",
                        help="Use 2000-person subsample parquet (~1.2M rows). "
                             "Built by scratch_materialize_subsample.py; the "
                             "person list lives in dasha_subsample_2000_persons.parquet.")
    p.add_argument("--k-bins", type=int, default=None,
                   help="Override the model's k_bins (default: stage_d_dataset.K_BINS=50). "
                        "Used by Task 19.5 sensitivity sweep (F5 defense). "
                        "Must match between the dataset's bin assignments and the model's heads — "
                        "_train_one_seed threads this through to both build_dataset and StageDModel.")
    p.add_argument("--device", type=str, default="auto",
                   choices=("auto", "dml", "cuda", "cpu"),
                   help="DeepHit training device. 'auto' prefers DirectML, "
                        "then CUDA, then CPU. F14 spec deviation: original "
                        "design was CPU-only; GPU choice is recorded in each "
                        "run record's `device` field for honest replication.")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s :: %(message)s")
    _seed_everything(args.seed)

    if args.smoke:
        df_name = "dasha_stage_d_features_smoke.parquet"
    elif args.subsample:
        df_name = "dasha_stage_d_features_subsample.parquet"
    else:
        df_name = "dasha_stage_d_features.parquet"
    df_path = Path("app/medini/data") / df_name
    df = pd.read_parquet(df_path)

    # Read noise floor SHA if it exists; empty string otherwise.
    nf_path = args.out_dir / "noise_floor.json"
    sha = ""
    if nf_path.exists():
        sha = hashlib.sha256(nf_path.read_bytes()).hexdigest()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    device = resolve_device(args.device)
    logger.info("Using device: %s", device_label(device))
    start = time.time()
    record = _train_one_seed(df, seed=args.seed, test_size=args.test_size,
                             out_dir=args.out_dir, noise_floor_sha=sha,
                             k_bins=args.k_bins, device=device)
    record["split"] = args.split
    record["k_bins"] = args.k_bins or K_BINS
    # Tag corpus so DECISION.md can footnote "n=2000 subsample" verdicts.
    if args.smoke:
        record["corpus"] = "smoke_100p"
    elif args.subsample:
        record["corpus"] = "subsample_2000p"
    else:
        record["corpus"] = "full_10239p"
    record["duration_seconds"] = round(time.time() - start, 1)

    # Append to the appropriate JSONL.
    run_file = args.out_dir / f"{args.split}_run.jsonl"
    with run_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    logger.info("Wrote seed=%d to %s", args.seed, run_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
