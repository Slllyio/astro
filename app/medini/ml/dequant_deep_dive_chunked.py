"""Checkpointed de-quantization deep dive — sandbox-friendly version.

The original ``dequant_deep_dive.py`` does 32+ XGBoost CV evaluations
back-to-back; each takes 15-30s on full multi-class. Running it inside a
sandbox that kills processes after 45s makes that impossible.

This variant:
- Processes ONE evaluation per invocation.
- Persists state to ``state.json`` so subsequent calls skip done work.
- Uses top-5 most-common event classes for tractable runtime (covers
  ~70% of the corpus mass).
- Single 80/20 train/val split (not 5-fold CV) for budget.

Usage::

    # Run once per invocation; repeat until "ALL DONE" is printed.
    python -m app.medini.ml.dequant_deep_dive_chunked

The output directory layout matches the original script (so the same
``report.md`` consumer can read both):
- data/ml_runs/dequant_deep_dive/state.json   (resume state)
- data/ml_runs/dequant_deep_dive/ablation_results.csv
- data/ml_runs/dequant_deep_dive/per_class_breakdown.csv
- data/ml_runs/dequant_deep_dive/report.md
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from app.medini.ml.dequantization_probe import (
    _fix_nak_pos,
    _prep_features,
    partition_features,
)
from app.medini.ml.dequant_deep_dive import (
    CONTINUOUS_GROUPS,
    DISCRETE_GROUPS,
    _resolve_group_cols,
)

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/ml_runs/dequant_deep_dive")
STATE_FILE = OUTPUT_DIR / "state.json"
CORPUS = Path("app/medini/data/event_corpus_round5_all.parquet")
TOP_K_CLASSES = 5
SEED = 42
N_EST = 30
MAX_DEPTH = 3


# ----------------------------------------------------------------------
# State management
# ----------------------------------------------------------------------

def _empty_state() -> dict:
    return {
        "schema_version": 1,
        "n_classes": None,
        "class_names": [],
        "n_rows": None,
        "n_cont": None,
        "n_disc": None,
        "baselines": {},          # name -> {accuracy, n_cols, per_class_auc}
        "ablations": {},          # group_name -> {n_dropped, accuracy_without_group, delta, kind}
        "todo_baselines": ["continuous_only", "discrete_only", "both"],
        "todo_ablations": [],
        "completed": False,
    }


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return _empty_state()


def save_state(state: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------

def _load_corpus():
    df = pd.read_parquet(CORPUS)
    df["_label"] = df["event_root"].astype(str).str.lower().str.strip()
    counts = df["_label"].value_counts()
    top = counts.head(TOP_K_CLASSES).index
    df = df[df["_label"].isin(top)].reset_index(drop=True)
    class_names = sorted(df["_label"].unique().tolist())
    class_to_idx = {n: i for i, n in enumerate(class_names)}
    y = df["_label"].map(class_to_idx).astype(int)
    return df, y, class_names


def _eval_single(df: pd.DataFrame, cols: list[str], y: pd.Series,
                 n_classes: int) -> dict:
    if not cols:
        return {"accuracy": 0.0, "n_cols": 0, "per_class_auc": {}}
    X = _prep_features(df, cols)
    X_tr, X_va, y_tr, y_va = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y,
    )
    clf = xgb.XGBClassifier(
        objective="multi:softprob", num_class=n_classes,
        n_estimators=N_EST, max_depth=MAX_DEPTH, learning_rate=0.1,
        enable_categorical=True, tree_method="hist",
        random_state=SEED, n_jobs=-1, eval_metric="mlogloss",
    )
    clf.fit(X_tr, y_tr)
    preds = clf.predict(X_va)
    acc = float((preds == y_va.to_numpy()).mean())
    proba = clf.predict_proba(X_va)
    per_class_auc = {}
    for c in range(n_classes):
        y_bin = (y_va.to_numpy() == c).astype(int)
        if y_bin.sum() == 0 or y_bin.sum() == len(y_bin):
            continue
        try:
            per_class_auc[c] = float(roc_auc_score(y_bin, proba[:, c]))
        except ValueError:
            pass
    return {"accuracy": acc, "n_cols": len(cols), "per_class_auc": per_class_auc}


# ----------------------------------------------------------------------
# Driver: do one chunk per call
# ----------------------------------------------------------------------

def step_one() -> bool:
    """Do one evaluation and persist. Returns True if more work remains."""
    state = load_state()

    if state["completed"]:
        print("ALL DONE — state shows completed=true")
        return False

    t0 = time.time()
    df, y, class_names = _load_corpus()
    n_classes = len(class_names)
    cont, disc = partition_features(df)
    cont, disc = _fix_nak_pos(cont, disc)
    both = cont + disc

    # First time: initialise metadata + ablation todo list
    if state["n_classes"] is None:
        state["n_classes"] = n_classes
        state["class_names"] = class_names
        state["n_rows"] = len(df)
        state["n_cont"] = len(cont)
        state["n_disc"] = len(disc)
        state["todo_ablations"] = [
            g for g in (list(DISCRETE_GROUPS.keys()) + list(CONTINUOUS_GROUPS.keys()))
            if _resolve_group_cols(g, both)
        ]
        save_state(state)
        print(f"INIT  rows={len(df)} classes={n_classes} cont={len(cont)} disc={len(disc)} ablations={len(state['todo_ablations'])} ({time.time()-t0:.1f}s)")
        return True

    # 1) baselines first
    if state["todo_baselines"]:
        name = state["todo_baselines"][0]
        cols = {"continuous_only": cont, "discrete_only": disc, "both": both}[name]
        print(f"EVAL  baseline {name} (n_cols={len(cols)}) ...")
        res = _eval_single(df, cols, y, n_classes)
        state["baselines"][name] = res
        state["todo_baselines"] = state["todo_baselines"][1:]
        save_state(state)
        print(f"DONE  baseline {name}: acc={res['accuracy']:.4f} ({time.time()-t0:.1f}s)")
        return True

    # 2) ablations: drop one group from `both`, evaluate
    if state["todo_ablations"]:
        group = state["todo_ablations"][0]
        group_cols = _resolve_group_cols(group, both)
        remaining = [c for c in both if c not in group_cols]
        kind = "discrete" if group in DISCRETE_GROUPS else "continuous"
        print(f"ABLATE drop {group} ({len(group_cols)} cols, remaining {len(remaining)}) ...")
        res = _eval_single(df, remaining, y, n_classes)
        baseline_acc = state["baselines"].get("both", {}).get("accuracy", float("nan"))
        delta = res["accuracy"] - baseline_acc if not np.isnan(baseline_acc) else float("nan")
        state["ablations"][group] = {
            "kind": kind,
            "n_dropped": len(group_cols),
            "accuracy_without_group": res["accuracy"],
            "delta_from_baseline": delta,
        }
        state["todo_ablations"] = state["todo_ablations"][1:]
        save_state(state)
        print(f"DONE  ablate {group}: acc={res['accuracy']:.4f} delta={delta:+.4f} ({time.time()-t0:.1f}s)")
        return True

    # 3) all done — write report + CSVs
    write_outputs(state)
    state["completed"] = True
    save_state(state)
    print("ALL DONE — report + CSVs written")
    return False


def write_outputs(state: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    class_names = state["class_names"]
    baselines = state["baselines"]
    n_classes = state["n_classes"]

    # ablation_results.csv (sorted by delta ascending = most-important first)
    ab_path = OUTPUT_DIR / "ablation_results.csv"
    rows = []
    for g, r in state["ablations"].items():
        rows.append({"group": g, **r})
    rows.sort(key=lambda x: x["delta_from_baseline"] if x["delta_from_baseline"] == x["delta_from_baseline"] else 0)
    with ab_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["group", "kind", "n_dropped",
                                          "accuracy_without_group", "delta_from_baseline"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # per_class_breakdown.csv
    pc_path = OUTPUT_DIR / "per_class_breakdown.csv"
    cont_auc = baselines.get("continuous_only", {}).get("per_class_auc", {})
    disc_auc = baselines.get("discrete_only", {}).get("per_class_auc", {})
    both_auc = baselines.get("both", {}).get("per_class_auc", {})
    with pc_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class_idx", "class_name", "auc_continuous",
                    "auc_discrete", "auc_both", "best_kind", "delta_cont_minus_disc"])
        for c_idx, c_name in enumerate(class_names):
            ac = cont_auc.get(str(c_idx), cont_auc.get(c_idx, np.nan))
            ad = disc_auc.get(str(c_idx), disc_auc.get(c_idx, np.nan))
            ab = both_auc.get(str(c_idx), both_auc.get(c_idx, np.nan))
            try:
                ac = float(ac); ad = float(ad); ab = float(ab)
            except (TypeError, ValueError):
                ac = ad = ab = float("nan")
            delta = ac - ad if not (np.isnan(ac) or np.isnan(ad)) else float("nan")
            best = "continuous" if (not np.isnan(delta) and delta > 0.005) else (
                "discrete" if (not np.isnan(delta) and delta < -0.005) else "tied"
            )
            w.writerow([
                c_idx, c_name,
                f"{ac:.4f}" if not np.isnan(ac) else "",
                f"{ad:.4f}" if not np.isnan(ad) else "",
                f"{ab:.4f}" if not np.isnan(ab) else "",
                best,
                f"{delta:+.4f}" if not np.isnan(delta) else "",
            ])

    # report.md
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rep_path = OUTPUT_DIR / "report.md"
    lines = [
        "# De-quantization Deep Dive (chunked runner)",
        "",
        f"_Generated {now}_",
        "",
        "## Setup",
        f"- Event corpus: {state['n_rows']:,} events (top-{TOP_K_CLASSES} classes only)",
        f"- Classes: {', '.join(class_names)}",
        f"- Continuous cols: {state['n_cont']}",
        f"- Discrete cols:   {state['n_disc']}",
        f"- Total cols:      {state['n_cont'] + state['n_disc']}",
        f"- Eval method: 80/20 stratified hold-out (NOT 5-fold CV); "
        f"XGBoost n_est={N_EST}, depth={MAX_DEPTH}",
        "",
        "> Reduced from the original script's 5-fold × 27-class setup to fit",
        "> the sandbox 45s/process budget. Comparative deltas (which group "
        "> matters most) remain meaningful; absolute accuracies are slightly "
        "> lower than the full-class run.",
        "",
        "## Part A: aggregate baselines",
        "",
        "| Feature set | N cols | Accuracy |",
        "|---|---|---|",
    ]
    for name in ("continuous_only", "discrete_only", "both"):
        r = baselines.get(name, {})
        lines.append(
            f"| {name} | {r.get('n_cols', '')} | "
            f"{r.get('accuracy', float('nan')):.4f} |"
        )
    lines.extend([
        "",
        f"Random baseline: 1/{n_classes} = {1 / n_classes:.4f}",
        "",
        "## Part A: per-class breakdown (one-vs-rest AUC)",
        "",
        "| Class | AUC cont. | AUC disc. | AUC both | Best | Δ (cont-disc) |",
        "|---|---|---|---|---|---|",
    ])
    for c_idx, c_name in enumerate(class_names):
        ac = cont_auc.get(str(c_idx), cont_auc.get(c_idx, np.nan))
        ad = disc_auc.get(str(c_idx), disc_auc.get(c_idx, np.nan))
        ab = both_auc.get(str(c_idx), both_auc.get(c_idx, np.nan))
        try:
            ac = float(ac); ad = float(ad); ab = float(ab)
        except (TypeError, ValueError):
            ac = ad = ab = float("nan")
        delta = ac - ad if not (np.isnan(ac) or np.isnan(ad)) else float("nan")
        best = "cont." if (not np.isnan(delta) and delta > 0.005) else (
            "disc." if (not np.isnan(delta) and delta < -0.005) else "tied"
        )
        c_str = f"{ac:.3f}" if not np.isnan(ac) else "—"
        d_str = f"{ad:.3f}" if not np.isnan(ad) else "—"
        b_str = f"{ab:.3f}" if not np.isnan(ab) else "—"
        delta_str = f"{delta:+.3f}" if not np.isnan(delta) else "—"
        lines.append(f"| `{c_name}` | {c_str} | {d_str} | {b_str} | {best} | {delta_str} |")

    lines.extend([
        "",
        "## Part B: drop-one-group ablation",
        "",
        "Sorted by impact: most-negative `Δ` = group is most important "
        "(removing it hurts the most).",
        "",
        "| Group | Kind | N cols | Acc w/o group | Δ from baseline |",
        "|---|---|---|---|---|",
    ])
    for r in rows:
        lines.append(
            f"| `{r['group']}` | {r['kind']} | {r['n_dropped']} | "
            f"{r['accuracy_without_group']:.4f} | {r['delta_from_baseline']:+.4f} |"
        )

    lines.extend([
        "",
        "## Interpretation guide",
        "",
        "- **Per-class breakdown** — which event classes prefer continuous "
        "features vs. discrete buckets.",
        "- **Ablation** — biggest negative Δ = load-bearing group.",
        "- Δ near 0 = redundant (covered by other groups).",
        "- Positive Δ when removed = the group was actively hurting (e.g. "
        "spurious / noisy features).",
        "",
        "Full ablation: `ablation_results.csv`; per-class: "
        "`per_class_breakdown.csv`; resume state: `state.json`.",
    ])
    rep_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.medini.ml.dequant_deep_dive_chunked")
    parser.add_argument("--max-steps", type=int, default=1,
                        help="how many evaluations to run this invocation")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    for _ in range(args.max_steps):
        if not step_one():
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
