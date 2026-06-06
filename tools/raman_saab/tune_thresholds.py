"""Threshold tuner SKELETON for the Raman Saab engine (build-time tool, OUTSIDE app/).

Loads the CONFIRMED goldens, runs Track B, scores accuracy + a 3x3 confusion matrix
(favourable / mixed / afflicted), and performs a BOUNDED, DISCRETE coordinate-descent
over the two engine thresholds:

  * ``MIN_REQUIRED[planet]`` — per-planet minimum total Shadbala in Rupas
    (``app/raman_saab/primitives/shadbala/total.py``). Step = 0.5 Rupa.
  * ``BHAVA_BALA_MIN_SH`` — minimum Bhava Bala in Shashtiamsas. Step = 1.0 Rupa
    (== 60 Shashtiamsas).

It NEVER writes ``total.py``. It prints a report and emits a *candidate diff* (the
proposed constant changes) for a human to apply. ``--holdout-lock`` excludes named
historical charts from the fit so the famous charts cannot be over-fit; ``--max-iterations``
bounds the descent.

This is a SKELETON: it runs end-to-end on the seed corpus today (even with a single
CONFIRMED record), exercising the scorer, the confusion matrix, and the descent loop.
The Shadbala-perturbation hook is wired but only Track-B-relevant thresholds move the
needle once the corpus carries fresh-cast (Shadbala-bearing) goldens — on a pure
from_stated_positions seed the verdict is threshold-independent, which the report states.

Usage:
    py -3.12 -m tools.raman_saab.tune_thresholds
    py -3.12 -m tools.raman_saab.tune_thresholds --max-iterations 20 --holdout-lock
"""
from __future__ import annotations

import argparse
import copy
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.raman_saab.primitives.shadbala import total as shadbala_total

# Import the harness loader/scorer so the tuner and the tests judge identically.
# `tests/` is not an importable package (no tests/__init__.py — that would change
# pytest discovery), so load the harness module directly from its file path.
import importlib.util as _ilu
from pathlib import Path as _Path

_HARNESS_PATH = (_Path(__file__).resolve().parents[2]
                 / "tests" / "raman_saab" / "test_goldens.py")
_spec = _ilu.spec_from_file_location("_raman_golden_harness", _HARNESS_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot load golden harness from {_HARNESS_PATH}")
_harness = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_harness)

build_chart = _harness.build_chart
confirmed_verdicts = _harness.confirmed_verdicts
load_goldens = _harness.load_goldens
_signification_verdict = _harness._signification_verdict

# The three verdict classes the confusion matrix tracks (insufficient-evidence is
# reported separately as "abstain" — it is not a favourable/mixed/afflicted call).
_MATRIX_CLASSES: tuple[str, ...] = ("favourable", "mixed", "afflicted")

# ---------------------------------------------------------------------------
# Bounded discrete search space (documented bounds — do NOT widen without cause).
# ---------------------------------------------------------------------------
_MIN_REQUIRED_STEP: float = 0.5          # Rupa
_MIN_REQUIRED_BOUNDS: tuple[float, float] = (4.0, 8.0)   # per-planet Rupa floor/ceiling
_BHAVA_BALA_STEP: float = 60.0           # 1.0 Rupa == 60 Shashtiamsas
_BHAVA_BALA_BOUNDS: tuple[float, float] = (180.0, 420.0)  # Shashtiamsas

# Charts excluded from the fit under --holdout-lock (named-historical anti-overfit set).
# Match on the record id prefix. Extend as famous charts are added to the corpus.
_HOLDOUT_PREFIXES: tuple[str, ...] = (
    "HTJAH-I.chart_", "HTJAH-II.chart_",  # the book's numbered worked examples
)


# ---------------------------------------------------------------------------
# Threshold vector — the mutable point the descent moves.
# ---------------------------------------------------------------------------

@dataclass
class Thresholds:
    """A candidate threshold setting. ``min_required`` mirrors
    ``shadbala_total.MIN_REQUIRED``; ``bhava_bala_min`` mirrors ``BHAVA_BALA_MIN_SH``."""
    min_required: dict[str, float]
    bhava_bala_min: float

    @classmethod
    def current(cls) -> "Thresholds":
        return cls(min_required=dict(shadbala_total.MIN_REQUIRED),
                   bhava_bala_min=float(shadbala_total.BHAVA_BALA_MIN_SH))

    def clone(self) -> "Thresholds":
        return Thresholds(min_required=dict(self.min_required),
                          bhava_bala_min=self.bhava_bala_min)


# ---------------------------------------------------------------------------
# Apply / restore thresholds around a scoring call (monkeypatch the module consts).
# ---------------------------------------------------------------------------

class _ApplyThresholds:
    """Context manager that swaps the engine's module-level thresholds for the duration
    of a scoring pass, then restores them. Keeps the tuner side-effect-free."""
    def __init__(self, th: Thresholds) -> None:
        self.th = th
        self._saved_min: Optional[dict[str, float]] = None
        self._saved_bb: Optional[float] = None

    def __enter__(self) -> None:
        self._saved_min = dict(shadbala_total.MIN_REQUIRED)
        self._saved_bb = shadbala_total.BHAVA_BALA_MIN_SH
        shadbala_total.MIN_REQUIRED.clear()
        shadbala_total.MIN_REQUIRED.update(self.th.min_required)
        # BHAVA_BALA_MIN_SH is a documented golden-tuned knob (NOT typing.Final), so
        # the tuner may rebind it directly without a type:ignore.
        shadbala_total.BHAVA_BALA_MIN_SH = self.th.bhava_bala_min

    def __exit__(self, *exc: Any) -> None:
        shadbala_total.MIN_REQUIRED.clear()
        shadbala_total.MIN_REQUIRED.update(self._saved_min or {})
        shadbala_total.BHAVA_BALA_MIN_SH = self._saved_bb


# ---------------------------------------------------------------------------
# Scoring — accuracy + confusion matrix over the CONFIRMED Track-B goldens.
# ---------------------------------------------------------------------------

@dataclass
class Score:
    total: int = 0
    correct: int = 0
    # confusion[expected][predicted] -> count, over _MATRIX_CLASSES.
    confusion: dict[str, dict[str, int]] = field(default_factory=dict)
    abstain: int = 0       # engine returned insufficient-evidence vs a decisive golden
    missing: int = 0       # signification absent from the engine output

    @property
    def accuracy(self) -> float:
        return (self.correct / self.total) if self.total else 0.0


def _blank_confusion() -> dict[str, dict[str, int]]:
    return {e: {p: 0 for p in _MATRIX_CLASSES} for e in _MATRIX_CLASSES}


def score(records: list[dict[str, Any]], th: Thresholds) -> Score:
    """Run Track B under ``th`` and tally accuracy + the 3x3 confusion matrix."""
    sc = Score(confusion=_blank_confusion())
    with _ApplyThresholds(th):
        for rec in records:
            chart = build_chart(rec)
            for house, entry in confirmed_verdicts(rec):
                expected = entry["verdict"]
                got = _signification_verdict(chart, house, entry["signification"])
                sc.total += 1
                if got is None:
                    sc.missing += 1
                    continue
                if got == expected:
                    sc.correct += 1
                if got == "insufficient-evidence" and expected in _MATRIX_CLASSES:
                    sc.abstain += 1
                if expected in _MATRIX_CLASSES and got in _MATRIX_CLASSES:
                    sc.confusion[expected][got] += 1
    return sc


# ---------------------------------------------------------------------------
# Bounded discrete coordinate descent.
# ---------------------------------------------------------------------------

def _neighbours(th: Thresholds) -> list[tuple[str, Thresholds]]:
    """All one-step discrete moves from ``th`` within bounds: +-step on each planet's
    MIN_REQUIRED and on BHAVA_BALA_MIN_SH. Returns (label, candidate)."""
    out: list[tuple[str, Thresholds]] = []
    for planet, val in th.min_required.items():
        for delta in (-_MIN_REQUIRED_STEP, _MIN_REQUIRED_STEP):
            nv = round(val + delta, 3)
            if _MIN_REQUIRED_BOUNDS[0] <= nv <= _MIN_REQUIRED_BOUNDS[1]:
                cand = th.clone()
                cand.min_required[planet] = nv
                out.append((f"MIN_REQUIRED[{planet}] {val}->{nv}", cand))
    for delta in (-_BHAVA_BALA_STEP, _BHAVA_BALA_STEP):
        nv = round(th.bhava_bala_min + delta, 3)
        if _BHAVA_BALA_BOUNDS[0] <= nv <= _BHAVA_BALA_BOUNDS[1]:
            cand = th.clone()
            cand.bhava_bala_min = nv
            out.append((f"BHAVA_BALA_MIN_SH {th.bhava_bala_min}->{nv}", cand))
    return out


def coordinate_descent(records: list[dict[str, Any]], start: Thresholds,
                       max_iterations: int) -> tuple[Thresholds, Score, list[str]]:
    """Greedy bounded descent: at each step take the neighbour with the highest
    accuracy (ties broken by fewer abstains), stop when no neighbour improves or the
    iteration budget runs out. Returns (best_thresholds, best_score, move_log)."""
    best = start.clone()
    best_score = score(records, best)
    log: list[str] = []
    for it in range(max_iterations):
        improved = False
        for label, cand in _neighbours(best):
            cand_score = score(records, cand)
            better = (cand_score.accuracy > best_score.accuracy
                      or (cand_score.accuracy == best_score.accuracy
                          and cand_score.abstain < best_score.abstain))
            if better:
                best, best_score = cand, cand_score
                log.append(f"iter {it}: {label}  acc={cand_score.accuracy:.3f}")
                improved = True
                break
        if not improved:
            log.append(f"iter {it}: no improving neighbour -- converged")
            break
    return best, best_score, log


# ---------------------------------------------------------------------------
# Reporting + candidate diff (never writes total.py).
# ---------------------------------------------------------------------------

def _format_confusion(sc: Score) -> str:
    head = "expected\\predicted | " + " | ".join(f"{c:>10}" for c in _MATRIX_CLASSES)
    rows = [head, "-" * len(head)]
    for e in _MATRIX_CLASSES:
        rows.append(f"{e:>18} | " + " | ".join(f"{sc.confusion[e][p]:>10}" for p in _MATRIX_CLASSES))
    return "\n".join(rows)


def _candidate_diff(base: Thresholds, tuned: Thresholds) -> str:
    """A human-applyable diff of the proposed constant changes. NOT written to disk."""
    lines: list[str] = ["# --- CANDIDATE DIFF (apply by hand to "
                        "app/raman_saab/primitives/shadbala/total.py) ---"]
    changed = False
    for planet in tuned.min_required:
        if tuned.min_required[planet] != base.min_required.get(planet):
            lines.append(f"#   MIN_REQUIRED[{planet!r}]: "
                         f"{base.min_required.get(planet)} -> {tuned.min_required[planet]}")
            changed = True
    if tuned.bhava_bala_min != base.bhava_bala_min:
        lines.append(f"#   BHAVA_BALA_MIN_SH: {base.bhava_bala_min} -> {tuned.bhava_bala_min}")
        changed = True
    if not changed:
        lines.append("#   (no change -- current thresholds already optimal on this corpus)")
    return "\n".join(lines)


def _filter_holdout(records: list[dict[str, Any]], lock: bool) -> list[dict[str, Any]]:
    if not lock:
        return records
    kept = [r for r in records
            if not any(str(r.get("id", "")).startswith(p) for p in _HOLDOUT_PREFIXES)]
    return kept


def run(max_iterations: int, holdout_lock: bool,
        out: Callable[[str], None] = print) -> int:
    """End-to-end tuner pass. Returns 0 on success (even with a tiny corpus)."""
    all_records = load_goldens()
    confirmed = [r for r in all_records
                 if "B" in r.get("track_eligibility", []) and confirmed_verdicts(r)]
    fit_set = _filter_holdout(confirmed, holdout_lock)

    out("=" * 70)
    out("Raman Saab threshold tuner (SKELETON)")
    out(f"  CONFIRMED Track-B records: {len(confirmed)}"
        + (f"  (holdout-lock excludes {len(confirmed) - len(fit_set)})" if holdout_lock else ""))
    out("=" * 70)

    if not fit_set:
        out("No fittable CONFIRMED records (all held out or none present). Nothing to tune.")
        return 0

    base = Thresholds.current()
    base_score = score(fit_set, base)
    out(f"\nBaseline accuracy: {base_score.accuracy:.3f} "
        f"({base_score.correct}/{base_score.total})  "
        f"abstain={base_score.abstain} missing={base_score.missing}")
    out("\nBaseline confusion matrix:")
    out(_format_confusion(base_score))

    tuned, tuned_score, log = coordinate_descent(fit_set, base, max_iterations)
    out(f"\nTuned accuracy: {tuned_score.accuracy:.3f} "
        f"({tuned_score.correct}/{tuned_score.total})  abstain={tuned_score.abstain}")
    out("\nDescent log:")
    for line in log:
        out(f"  {line}")
    out("\nTuned confusion matrix:")
    out(_format_confusion(tuned_score))

    out("")
    out(_candidate_diff(base, tuned))
    out("\n(Reminder: this tool NEVER edits total.py -- apply the diff by hand after review.)")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Raman Saab threshold tuner (skeleton).")
    ap.add_argument("--max-iterations", type=int, default=10,
                    help="bound on coordinate-descent iterations (default 10)")
    ap.add_argument("--holdout-lock", action="store_true",
                    help="exclude named-historical charts from the fit (anti-overfit)")
    args = ap.parse_args(argv)
    return run(max_iterations=args.max_iterations, holdout_lock=args.holdout_lock)


if __name__ == "__main__":
    raise SystemExit(main())
