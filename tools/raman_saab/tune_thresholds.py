"""Threshold tuner for the Raman Saab engine (build-time tool, OUTSIDE app/).

Loads the CONFIRMED goldens, runs Track B, scores accuracy + a 3x3 confusion matrix
(favourable / mixed / afflicted), and performs a BOUNDED, DISCRETE coordinate-descent
over the engine thresholds:

  * ``MIN_REQUIRED[planet]`` — per-planet minimum total Shadbala in Rupas
    (``app/raman_saab/primitives/shadbala/total.py``). Step = 0.5 Rupa.
  * ``BHAVA_BALA_MIN_SH`` — minimum Bhava Bala in Shashtiamsas. Step = 1.0 Rupa
    (== 60 Shashtiamsas).
  * ``CONTRA_AFFLICT_MARGIN`` / ``CONTRA_FAVOUR_MARGIN`` — the per-signification
    preponderance margins (clause-2 of ``judges/house_template._decide``). Swept over
    the discrete set {1,2,3,4,5} plus the no-op 99. Default 99 is effectively infinite
    (always 'mixed'); lower values let a malefic/benefic fired-rule surplus decide.

It NEVER writes ``total.py``. It prints a report (with SEPARATE fit-set and holdout-set
accuracies, so an "improves fit / drops holdout" comparison is computable) and emits a
*candidate diff* (the proposed constant changes) for a human to apply. ``--holdout-lock``
excludes the held-out charts from the fit so the famous charts cannot be over-fit;
``--max-iterations`` bounds the descent.

Holdout membership is STABLE (does not churn as records are added): a record is held out
iff its id is in ``HOLDOUT_IDS`` (the 4 death charts, always held out) OR
``zlib.crc32(id) % 5 == 0`` (a deterministic ~20% slice of the worked examples). Index-
based selection is deliberately NOT used — adding a record must not reshuffle the split.

Usage:
    py -3.12 -m tools.raman_saab.tune_thresholds
    py -3.12 -m tools.raman_saab.tune_thresholds --max-iterations 20 --holdout-lock
"""
from __future__ import annotations

import argparse
import zlib
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.raman_saab.chart.model import RamanChart
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

# Preponderance-margin discrete sweep set: the active band {1..5} plus the no-op 99.
# (clause-2 of house_template._decide; default 99 == always 'mixed'.)
_CONTRA_MARGIN_STEPS: tuple[int, ...] = (1, 2, 3, 4, 5, 99)

# ---------------------------------------------------------------------------
# Holdout membership (STABLE — must NOT churn as records are added).
# ---------------------------------------------------------------------------
# The 4 death charts are ALWAYS held out (longevity worked examples — their span class
# is owned by the Phase-E engine, not the house judge, so they must never enter the fit).
HOLDOUT_IDS: frozenset[str] = frozenset({
    "HTJAH-II.chart_73", "HTJAH-II.chart_74",
    "HTJAH-II.chart_75", "HTJAH-II.chart_78",
})
# Plus a deterministic ~20% slice of the *other* worked examples, selected by a stable
# hash of the record id (NOT a list index, so adding a record never reshuffles the split).
_HOLDOUT_HASH_MODULUS: int = 5


def is_holdout(record_id: str) -> bool:
    """True iff `record_id` is held out of the fit: a named death chart, or a member
    of the stable crc32-hash slice. Pure function of the id — stable across runs and
    across corpus growth."""
    if record_id in HOLDOUT_IDS:
        return True
    return zlib.crc32(record_id.encode()) % _HOLDOUT_HASH_MODULUS == 0


# ---------------------------------------------------------------------------
# Threshold vector — the mutable point the descent moves.
# ---------------------------------------------------------------------------

@dataclass
class Thresholds:
    """A candidate threshold setting. ``min_required`` mirrors
    ``shadbala_total.MIN_REQUIRED``; ``bhava_bala_min`` mirrors ``BHAVA_BALA_MIN_SH``;
    ``contra_afflict``/``contra_favour`` mirror the preponderance margins."""
    min_required: dict[str, float]
    bhava_bala_min: float
    contra_afflict: int
    contra_favour: int

    @classmethod
    def current(cls) -> "Thresholds":
        return cls(min_required=dict(shadbala_total.MIN_REQUIRED),
                   bhava_bala_min=float(shadbala_total.BHAVA_BALA_MIN_SH),
                   contra_afflict=int(shadbala_total.CONTRA_AFFLICT_MARGIN),
                   contra_favour=int(shadbala_total.CONTRA_FAVOUR_MARGIN))

    def clone(self) -> "Thresholds":
        return Thresholds(min_required=dict(self.min_required),
                          bhava_bala_min=self.bhava_bala_min,
                          contra_afflict=self.contra_afflict,
                          contra_favour=self.contra_favour)


# ---------------------------------------------------------------------------
# Apply / restore thresholds around a scoring call (monkeypatch the module consts).
# ---------------------------------------------------------------------------

class _ApplyThresholds:
    """Context manager that swaps the engine's module-level thresholds for the duration
    of a scoring pass, then restores them. Keeps the tuner side-effect-free.

    All four knobs live on ``shadbala_total`` and are documented golden-tuned (NOT
    ``typing.Final``), so they may be rebound directly. ``house_template._decide`` reads
    ``shadbala_total.CONTRA_*`` LIVE (module-attribute access, not an import-time bind),
    so patching here takes effect for the in-flight scoring pass."""
    def __init__(self, th: Thresholds) -> None:
        self.th = th
        self._saved_min: Optional[dict[str, float]] = None
        self._saved_bb: Optional[float] = None
        self._saved_afflict: Optional[int] = None
        self._saved_favour: Optional[int] = None

    def __enter__(self) -> None:
        self._saved_min = dict(shadbala_total.MIN_REQUIRED)
        self._saved_bb = shadbala_total.BHAVA_BALA_MIN_SH
        self._saved_afflict = shadbala_total.CONTRA_AFFLICT_MARGIN
        self._saved_favour = shadbala_total.CONTRA_FAVOUR_MARGIN
        shadbala_total.MIN_REQUIRED.clear()
        shadbala_total.MIN_REQUIRED.update(self.th.min_required)
        shadbala_total.BHAVA_BALA_MIN_SH = self.th.bhava_bala_min
        shadbala_total.CONTRA_AFFLICT_MARGIN = self.th.contra_afflict
        shadbala_total.CONTRA_FAVOUR_MARGIN = self.th.contra_favour

    def __exit__(self, *exc: Any) -> None:
        shadbala_total.MIN_REQUIRED.clear()
        shadbala_total.MIN_REQUIRED.update(self._saved_min or {})
        shadbala_total.BHAVA_BALA_MIN_SH = self._saved_bb
        shadbala_total.CONTRA_AFFLICT_MARGIN = self._saved_afflict
        shadbala_total.CONTRA_FAVOUR_MARGIN = self._saved_favour


# ---------------------------------------------------------------------------
# Chart-cast cache — keyed by golden id (the cast is a pure function of the record's
# birth/stated positions and is threshold-independent, so it is computed at most once).
# ---------------------------------------------------------------------------

class _ChartCache:
    """Memoises ``build_chart`` per golden id so the sweep does not re-cast a chart on
    every coordinate-descent iteration. Charts are threshold-independent (thresholds only
    affect the VERDICT, never the cast), so this is safe to share across scoring passes."""
    def __init__(self) -> None:
        self._cache: dict[str, RamanChart] = {}

    def get(self, rec: dict[str, Any]) -> RamanChart:
        key = str(rec.get("id", id(rec)))
        chart = self._cache.get(key)
        if chart is None:
            chart = build_chart(rec)
            self._cache[key] = chart
        return chart


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


def score(records: list[dict[str, Any]], th: Thresholds,
          cache: Optional[_ChartCache] = None) -> Score:
    """Run Track B under ``th`` and tally accuracy + the 3x3 confusion matrix.

    ``cache`` (when supplied) reuses casts across iterations; the cast is threshold-
    independent so this never changes a verdict, only avoids redundant ephemeris work."""
    cache = cache if cache is not None else _ChartCache()
    sc = Score(confusion=_blank_confusion())
    with _ApplyThresholds(th):
        for rec in records:
            chart = cache.get(rec)
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
    MIN_REQUIRED and on BHAVA_BALA_MIN_SH, plus each discrete preponderance-margin
    value (CONTRA_AFFLICT_MARGIN / CONTRA_FAVOUR_MARGIN) other than the current one.
    Returns (label, candidate)."""
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
    # Preponderance margins: every discrete step value is a candidate (the search space
    # is small and not naturally ordered for +-1 descent, so we expose the full set).
    for step in _CONTRA_MARGIN_STEPS:
        if step != th.contra_afflict:
            cand = th.clone()
            cand.contra_afflict = step
            out.append((f"CONTRA_AFFLICT_MARGIN {th.contra_afflict}->{step}", cand))
    for step in _CONTRA_MARGIN_STEPS:
        if step != th.contra_favour:
            cand = th.clone()
            cand.contra_favour = step
            out.append((f"CONTRA_FAVOUR_MARGIN {th.contra_favour}->{step}", cand))
    return out


def coordinate_descent(records: list[dict[str, Any]], start: Thresholds,
                       max_iterations: int,
                       cache: Optional[_ChartCache] = None,
                       ) -> tuple[Thresholds, Score, list[str]]:
    """Greedy bounded descent: at each step take the neighbour with the highest
    accuracy (ties broken by fewer abstains), stop when no neighbour improves or the
    iteration budget runs out. Returns (best_thresholds, best_score, move_log)."""
    cache = cache if cache is not None else _ChartCache()
    best = start.clone()
    best_score = score(records, best, cache)
    log: list[str] = []
    for it in range(max_iterations):
        improved = False
        for label, cand in _neighbours(best):
            cand_score = score(records, cand, cache)
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
    if tuned.contra_afflict != base.contra_afflict:
        lines.append(f"#   CONTRA_AFFLICT_MARGIN: {base.contra_afflict} -> {tuned.contra_afflict}")
        changed = True
    if tuned.contra_favour != base.contra_favour:
        lines.append(f"#   CONTRA_FAVOUR_MARGIN: {base.contra_favour} -> {tuned.contra_favour}")
        changed = True
    if not changed:
        lines.append("#   (no change -- current thresholds already optimal on this corpus)")
    return "\n".join(lines)


def _split_fit_holdout(
    records: list[dict[str, Any]], lock: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Partition CONFIRMED records into (fit_set, holdout_set).

    Under ``--holdout-lock`` the held-out records (per :func:`is_holdout`) are removed
    from the fit AND returned as a separate scoreable set, so the report can compare
    "improves fit / drops holdout". Without the lock every record is fittable and the
    holdout set is empty."""
    if not lock:
        return records, []
    fit = [r for r in records if not is_holdout(str(r.get("id", "")))]
    holdout = [r for r in records if is_holdout(str(r.get("id", "")))]
    return fit, holdout


def run(max_iterations: int, holdout_lock: bool,
        out: Callable[[str], None] = print) -> int:
    """End-to-end tuner pass. Returns 0 on success (even with a tiny corpus)."""
    all_records = load_goldens()
    confirmed = [r for r in all_records
                 if "B" in r.get("track_eligibility", []) and confirmed_verdicts(r)]
    fit_set, holdout_set = _split_fit_holdout(confirmed, holdout_lock)
    cache = _ChartCache()

    out("=" * 70)
    out("Raman Saab threshold tuner")
    out(f"  CONFIRMED Track-B records: {len(confirmed)}"
        + (f"  (holdout-lock excludes {len(holdout_set)})" if holdout_lock else ""))
    out("=" * 70)

    if not fit_set:
        out("No fittable CONFIRMED records (all held out or none present). Nothing to tune.")
        return 0

    base = Thresholds.current()
    base_score = score(fit_set, base, cache)
    out(f"\nBaseline fit accuracy: {base_score.accuracy:.3f} "
        f"({base_score.correct}/{base_score.total})  "
        f"abstain={base_score.abstain} missing={base_score.missing}")
    out("\nBaseline fit confusion matrix:")
    out(_format_confusion(base_score))

    tuned, tuned_score, log = coordinate_descent(fit_set, base, max_iterations, cache)
    out(f"\nTuned fit accuracy: {tuned_score.accuracy:.3f} "
        f"({tuned_score.correct}/{tuned_score.total})  abstain={tuned_score.abstain}")
    out("\nDescent log:")
    for line in log:
        out(f"  {line}")
    out("\nTuned fit confusion matrix:")
    out(_format_confusion(tuned_score))

    # Holdout scoring — the anti-overfit comparison. The 4 death charts (and any other
    # held-out records) currently carry NO confirmed Track-B verdicts, so the holdout
    # score is often over 0 records; report that gracefully.
    out("")
    if holdout_set:
        base_hold = score(holdout_set, base, cache)
        tuned_hold = score(holdout_set, tuned, cache)
        if base_hold.total == 0:
            out("Holdout accuracy: n=0 (no confirmed verdicts yet)")
        else:
            out(f"Holdout accuracy (baseline): {base_hold.accuracy:.3f} "
                f"({base_hold.correct}/{base_hold.total})")
            out(f"Holdout accuracy (tuned):    {tuned_hold.accuracy:.3f} "
                f"({tuned_hold.correct}/{tuned_hold.total})")
            delta_fit = tuned_score.accuracy - base_score.accuracy
            delta_hold = tuned_hold.accuracy - base_hold.accuracy
            out(f"  delta fit={delta_fit:+.3f}  delta holdout={delta_hold:+.3f}  "
                + ("(improves fit, drops holdout -> likely OVERFIT)"
                   if delta_fit > 0 and delta_hold < 0 else "(no overfit signal)"))
    else:
        out("Holdout accuracy: n=0 (no records held out -- run with --holdout-lock)")

    out("")
    out(_candidate_diff(base, tuned))
    out("\n(Reminder: this tool NEVER edits total.py -- apply the diff by hand after review.)")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Raman Saab threshold tuner.")
    ap.add_argument("--max-iterations", type=int, default=10,
                    help="bound on coordinate-descent iterations (default 10)")
    ap.add_argument("--holdout-lock", action="store_true",
                    help="exclude held-out charts from the fit and score them separately "
                         "(anti-overfit)")
    args = ap.parse_args(argv)
    return run(max_iterations=args.max_iterations, holdout_lock=args.holdout_lock)


if __name__ == "__main__":
    raise SystemExit(main())
