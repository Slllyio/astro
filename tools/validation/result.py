"""The one results record every validation test emits (plan: Phase 0, "better output").

Each test ends in exactly one verdict:
  SHAM_FAIL     the sham/placebo arm was not null -> the pipeline is not trustworthy
  SIGNAL        CI95 excludes 0 AND the chart-vs-chartless-baseline delta CI excludes 0
  BOUNDED_NULL  TOST at the pre-registered SESOI passes (90% CI inside +/- sesoi)
  UNDERPOWERED  none of the above: neither an effect nor its absence is established

Effects are on a 0 = no-effect scale (AUC-0.5, log RR, hit difference). Fidelity numbers live in
their own `fidelity` block and are never combined with prediction numbers.

Usage (library):
    from tools.validation.result import Result, emit
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.validation.stats import mde80, tost

DEFAULT_SINK = Path("data/validation/results.jsonl")
_Z95, _Z90 = 1.959964, 1.644854


@dataclass(frozen=True)
class Result:
    test_id: str
    prereg_id: str
    engine: str                       # "parashara" | "raman" | "none"
    statistic: str                    # "AUC-0.5" | "logRR" | "logOR_clr" | "hit_diff" ...
    unit: str                         # "person" | "event" | "rule"
    effect: float
    se: float
    se0: float                        # SE under the null, from n alone -> MDE80
    sesoi: float
    n_cases: int
    n_clusters: int
    sham_ok: bool
    split: str = "discovery"          # "discovery" | holdout name
    n_controls: int = 0
    ayanamsa: str = "lahiri"
    baseline_delta_ci: tuple[float, float] | None = None   # None = no chartless arm for this test
    planted_recovered: bool | None = None
    ci95_override: tuple[float, float] | None = None       # e.g. a cluster-bootstrap CI
    config: dict[str, Any] = field(default_factory=dict)
    fidelity: dict[str, Any] = field(default_factory=dict)

    @property
    def ci95(self) -> tuple[float, float]:
        return self.ci95_override or (self.effect - _Z95 * self.se, self.effect + _Z95 * self.se)

    @property
    def ci90(self) -> tuple[float, float]:
        return (self.effect - _Z90 * self.se, self.effect + _Z90 * self.se)

    @property
    def p_tost(self) -> float:
        return tost(self.effect, self.se, self.sesoi)

    @property
    def verdict(self) -> str:
        if not self.sham_ok:
            return "SHAM_FAIL"
        lo, hi = self.ci95
        beats_baseline = (self.baseline_delta_ci is None
                          or self.baseline_delta_ci[0] > 0 or self.baseline_delta_ci[1] < 0)
        if (lo > 0 or hi < 0) and beats_baseline:
            return "SIGNAL"
        if self.p_tost < 0.05:
            return "BOUNDED_NULL"
        return "UNDERPOWERED"


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()[:12]
    except Exception:  # noqa: BLE001 - outside a checkout the record still emits, marked
        return "unknown"


def emit(r: Result, sink: Path = DEFAULT_SINK) -> dict[str, Any]:
    """Append one JSON line with every derived field and provenance. Returns the record."""
    rec = asdict(r) | {
        "ci95": r.ci95, "ci90": r.ci90, "p_tost": r.p_tost, "mde80": mde80(r.se0),
        "powered": mde80(r.se0) <= r.sesoi, "verdict": r.verdict,
        "engine_sha": _git_sha(), "config_sha": _sha(r.config),
        "emitted": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    sink.parent.mkdir(parents=True, exist_ok=True)
    with sink.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    return rec


if __name__ == "__main__":
    base = dict(test_id="t", prereg_id="p", engine="none", statistic="AUC-0.5", unit="person",
                se0=0.01, sesoi=0.03, n_cases=1000, n_clusters=1000)
    assert Result(**base, effect=0.0, se=0.009, sham_ok=True).verdict == "BOUNDED_NULL"
    assert Result(**base, effect=0.0, se=0.05, sham_ok=True).verdict == "UNDERPOWERED"
    assert Result(**base, effect=0.06, se=0.01, sham_ok=True).verdict == "SIGNAL"
    assert Result(**base, effect=0.06, se=0.01, sham_ok=False).verdict == "SHAM_FAIL"
    # an effect the chartless baseline explains just as well is not a signal
    assert Result(**base, effect=0.06, se=0.01, sham_ok=True,
                  baseline_delta_ci=(-0.01, 0.02)).verdict == "UNDERPOWERED"
    print("result self-check OK")
