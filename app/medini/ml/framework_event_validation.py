"""Path C — empirically validate the astrologer's-lens framework.

Tests the framework's structured verdicts against real event data at
population scale. The hypothesis after Round 11's null verdict was:
"univariate features don't predict events at population scale; perhaps
multi-condition AND-gate doctrine predicates will".

This module operationalises that test:

1. For each event class with N ≥ 200 events (marriage, career, fame,
   death, relationships), pick the target bhava per classical doctrine:
   marriage->7H, career->10H, fame->10H, death->8H, relationships->7H.
2. For each event in that class, compose the framework Reading **at the
   event_jd** (gochara triggers active) and record the bhava verdict
   label.
3. Compute the verdict-label distribution at events vs the same-person
   baseline (the static natal verdict from ``readings.parquet``).
4. Report lift = P(strong | event) / P(strong | baseline). Lift > 1.2
   = framework adds population-scale signal beyond chance.

## What "lift > 1.2" would mean

Population RR was exhausted on single features in Round 11. If the
framework's composite verdict shows meaningful lift on event timing,
the multi-condition AND-gate IS picking up signal that linear ML
missed. If lift ~ 1.0, the framework is doctrinally faithful but not
predictive at population scale — and the value is per-person, per-
prashna, not statistical.

Usage:
    python -m app.medini.ml.framework_event_validation
"""
from __future__ import annotations

import argparse
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping

import pandas as pd

from app.core.chart_model import Chart
from app.core.dkp_modulation import DKPContext
from app.core.gochara_engine import compute_gochara
from app.core.reading_composer import compose_reading

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")

# Event class -> target bhava per classical doctrine (BPHS Ch.6 mapping).
_EVENT_BHAVA: Final[Mapping[str, int]] = {
    "marriage":                  7,
    "career":                   10,
    "fame":                     10,
    "death_cause_unspecified":   8,
    "relationships":             7,
}

_LABELS: Final[tuple[str, ...]] = ("strong", "medium", "weak", "afflicted")


@dataclass(frozen=True)
class EventClassResult:
    """Per-event-class verdict distribution + lift."""
    event_class: str
    target_bhava: int
    n_events: int
    n_baseline: int
    event_dist: dict[str, float]    # label -> fraction
    baseline_dist: dict[str, float]
    lift_strong: float              # P(strong|event) / P(strong|baseline)
    lift_afflicted: float


def _baseline_distribution(
    readings_df: pd.DataFrame, bhava: int,
) -> tuple[dict[str, float], int]:
    """All persons' static verdict for this bhava — the chance baseline."""
    col = f"b{bhava}_label"
    if col not in readings_df.columns:
        return ({lbl: 0.0 for lbl in _LABELS}, 0)
    counts = readings_df[col].value_counts(dropna=True).to_dict()
    total = sum(counts.values())
    dist = {lbl: counts.get(lbl, 0) / total if total else 0.0 for lbl in _LABELS}
    return dist, total


def _event_distribution(
    events_df: pd.DataFrame, charts_lookup: dict[str, Chart],
    bhava: int, event_class: str,
) -> tuple[dict[str, float], int]:
    """Verdict distribution at event times for the given event class.

    For each event in the class:
      1. Look up the person's Chart from the cached map.
      2. Build transit_signs from the event_dossier transit columns.
      3. Compose the framework Reading at this event_jd.
      4. Record the target bhava's verdict label.
    """
    sub = events_df[events_df["event_class"] == event_class]
    counts: dict[str, int] = defaultdict(int)
    n_evaluated = 0
    for _, row in sub.iterrows():
        person_id = row["person_id"]
        chart = charts_lookup.get(person_id)
        if chart is None:
            continue
        transit_signs = _extract_transit_signs(row)
        if not transit_signs:
            continue
        try:
            reading = compose_reading(
                chart, DKPContext(),
                transit_signs=transit_signs,
                vimshottari_md_lord=row.get("active_md_lord"),
            )
        except Exception:  # noqa: BLE001
            continue
        claim = reading.bhava_claims.get(bhava)
        if claim is None:
            continue
        counts[claim.verdict_label] += 1
        n_evaluated += 1
    if n_evaluated == 0:
        return {lbl: 0.0 for lbl in _LABELS}, 0
    dist = {lbl: counts.get(lbl, 0) / n_evaluated for lbl in _LABELS}
    return dist, n_evaluated


def _extract_transit_signs(event_row: pd.Series) -> dict[str, int]:
    """Pull the 9 transit signs from event_dossier wide columns.

    event_dossier has ``t_<planet>_sign`` columns. Returns empty dict
    if any planet's sign is missing/NA (entire transit block must be
    present for valid gochara computation).
    """
    grahas = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
              "Venus", "Saturn", "Rahu", "Ketu")
    out: dict[str, int] = {}
    for g in grahas:
        key = f"t_{g.lower()}_sign"
        val = event_row.get(key)
        if val is None or pd.isna(val):
            return {}
        try:
            s = int(val)
        except (ValueError, TypeError):
            return {}
        if not 1 <= s <= 12:
            return {}
        out[g] = s
    return out


def _lift(p_event: float, p_baseline: float) -> float:
    """Lift ratio with zero-baseline guard."""
    if p_baseline <= 0:
        return float("nan")
    return p_event / p_baseline


def validate_all_event_classes(
    data_dir: Path = DEFAULT_DATA_DIR,
    limit_events_per_class: int | None = None,
) -> list[EventClassResult]:
    """Run the full validation across all canonical event classes."""
    readings_df = pd.read_parquet(data_dir / "readings.parquet")
    persons_df = pd.read_parquet(data_dir / "person_dossier.parquet")
    events_df = pd.read_parquet(data_dir / "event_dossier.parquet")
    logger.info(
        "Loaded readings=%d persons=%d events=%d",
        len(readings_df), len(persons_df), len(events_df),
    )

    # Build Chart lookup keyed by person_id (one-time cost).
    charts_lookup: dict[str, Chart] = {}
    for _, row in persons_df.iterrows():
        try:
            ch = Chart.from_dossier_row(row.to_dict())
            charts_lookup[ch.person_id or row["person_id"]] = ch
        except Exception:  # noqa: BLE001
            continue
    logger.info("Built %d chart objects", len(charts_lookup))

    results: list[EventClassResult] = []
    for event_class, target_bhava in _EVENT_BHAVA.items():
        logger.info(
            "Evaluating %s -> bhava %d ...", event_class, target_bhava,
        )
        sub = events_df[events_df["event_class"] == event_class]
        if limit_events_per_class is not None:
            sub = sub.head(limit_events_per_class)
        baseline_dist, n_baseline = _baseline_distribution(
            readings_df, target_bhava,
        )
        event_dist, n_events = _event_distribution(
            sub, charts_lookup, target_bhava, event_class,
        )
        result = EventClassResult(
            event_class=event_class,
            target_bhava=target_bhava,
            n_events=n_events,
            n_baseline=n_baseline,
            event_dist=event_dist,
            baseline_dist=baseline_dist,
            lift_strong=_lift(event_dist["strong"], baseline_dist["strong"]),
            lift_afflicted=_lift(event_dist["afflicted"], baseline_dist["afflicted"]),
        )
        results.append(result)
    return results


def format_results(results: list[EventClassResult]) -> str:
    """Plain-text report of the validation."""
    lines = ["=" * 80]
    lines.append("FRAMEWORK EVENT-VALIDATION — does the AND-gate predict events?")
    lines.append("=" * 80)
    for r in results:
        lines.append("")
        lines.append(f"Event class: {r.event_class}  ->  target bhava {r.target_bhava}")
        lines.append(f"  N at events: {r.n_events:>6}   baseline N: {r.n_baseline:>6}")
        lines.append(f"  {'label':>10s}  {'event %':>8s}  {'baseline %':>10s}  {'lift':>6s}")
        for lbl in _LABELS:
            ep = r.event_dist[lbl] * 100
            bp = r.baseline_dist[lbl] * 100
            lift = _lift(r.event_dist[lbl], r.baseline_dist[lbl])
            lift_s = f"{lift:.2f}" if not (lift != lift) else "nan"  # NaN safe
            lines.append(f"  {lbl:>10s}  {ep:7.1f}%  {bp:9.1f}%  {lift_s:>6s}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("INTERPRETATION GUIDE")
    lines.append("=" * 80)
    lines.append(
        "lift > 1.20  -> framework verdict meaningfully enriched at events"
    )
    lines.append(
        "lift 0.85-1.20 -> null at population scale (framework doctrinally"
    )
    lines.append(
        "                  faithful but not statistically predictive)"
    )
    lines.append(
        "lift < 0.85  -> directionally INVERTED (worth investigating)"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument(
        "--limit-per-class", type=int, default=None,
        help="Cap events per class (smoke test)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    results = validate_all_event_classes(
        args.data_dir, limit_events_per_class=args.limit_per_class,
    )
    print(format_results(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
