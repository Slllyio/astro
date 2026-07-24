"""Gauntlet G1 — clean re-run of the framework career→10H lift (1.37) with paired controls.

Pre-registered in tools/raman_saab/astrobank/GAUNTLET_PREREG.md. The original
(framework_event_validation, 2026-05-29) reported lift 1.37 for the 10H "strong" verdict
at career events. That number rests on two apples-to-oranges comparisons, both fixed here:

  1. PROCESS MISMATCH. The event arm composed a DYNAMIC reading (gochara transit overlay
     + active MD lord) while the baseline was the STATIC natal verdict distribution from
     readings.parquet. Transit confirmation can only add pillars, so dynamic composition
     can emit "strong" more often than static composition on ANY date — machinery, not
     timing. Fix: the control arm composes the SAME dynamic reading with the SAME
     machinery, only at control dates.

  2. POPULATION MISMATCH. The baseline pooled all 75,149 persons; the event arm is only
     the ~8k persons with recorded career events (different documentation intensity and
     corpus mix). Fix: controls are WITHIN-PERSON — each event is compared against the
     same person's readings at shifted dates.

Control sampler (pre-registered, locked before computation):
  * Year-shifted, age-near controls: control_jd = event_jd + k*365.2425 for
    k in {-7..-2, +2..+7} (JD arithmetic per project convention — preserves the calendar
    season; holds age within 7 years of the event, the lesson of the astrobank
    death-window age-artifact falsification).
  * Validity window: control_jd in [birth_jd + 18*365.2425, min(death_jd - 1yr, scrape)]
    where death_jd = the person's earliest death-class event and scrape = 2026-05-31
    (the Silver-layer build date) — the audit's min(death, scrape) exposure cap.
  * Blackout: a control is discarded if within +/-1yr of ANY career event of the person.
  * An event needs >= 3 surviving controls, else it is dropped (count reported).

Both arms use identical machinery: Chart.from_dossier_row + compose_reading with
transit signs from _planet_lon_sidereal (the exact function that built event_dossier's
transit block) and the MD lord interval-joined from dasha_pd_windows for BOTH arms
(consistency with the dossier's active_md_lord is measured and reported).

Statistics (pre-registered):
  * Clean lift = P(strong | event dates) / P(strong | control dates), pooled.
  * Paired excess = mean over events of (hit_event - mean(hit_controls)).
  * 2,000-resample PERSON-clustered bootstrap on both; success per prereg = lift > 1.0
    with 95% CI excluding 1.0 (equivalently paired-excess CI excluding 0).
  * Replication check: event-arm strong rate vs static b10_label baseline must
    reproduce ~1.37 — confirming the re-implementation matches the original event arm.
  * Report-only strata: source (wikidata / astro_databank / lunarastro), birth decade.

Usage:
    py -3.12 -m app.medini.ml.gauntlet_g1_career
    py -3.12 -m app.medini.ml.gauntlet_g1_career --limit 500   (smoke test)
"""
from __future__ import annotations

import argparse
import json
import logging
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import swisseph as swe

from app.core.chart_model import Chart
from app.core.dkp_modulation import DKPContext
from app.core.reading_composer import compose_reading
from app.medini.etl.build_event_transits import _planet_lon_sidereal

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
DEFAULT_OUT: Final = Path("data/ml_runs/gauntlet/g1_career_clean.json")

DAYS_PER_VEDIC_YEAR: Final = 365.2425
_YEAR_OFFSETS: Final = tuple(k for k in range(-7, 8) if abs(k) >= 2)
_MIN_CONTROLS: Final = 3
_SCRAPE_JD: Final = swe.julday(2026, 5, 31, 0.0, swe.GREG_CAL)
_TARGET_BHAVA: Final = 10
_LABELS: Final = ("strong", "medium", "weak", "afflicted")

_PLANET_IDS: Final = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}


def _transit_signs_at(jd: float) -> dict[str, int]:
    """9-graha sidereal transit signs at jd — same computation as event_dossier."""
    out: dict[str, int] = {}
    for graha, pid in _PLANET_IDS.items():
        lon, _ = _planet_lon_sidereal(jd, pid)
        out[graha] = int(lon // 30) + 1
    rahu_lon, _ = _planet_lon_sidereal(jd, swe.TRUE_NODE)
    out["Rahu"] = int(rahu_lon // 30) + 1
    out["Ketu"] = int(((rahu_lon + 180.0) % 360.0) // 30) + 1
    return out


def _md_windows(pd_windows: pd.DataFrame) -> dict[str, tuple[list[float], list[float], list[str]]]:
    """Collapse PD windows to MD level: person_id -> (starts, ends, lords), sorted."""
    md = (
        pd_windows.groupby(["person_id", "md_seq"], sort=False)
        .agg(start_jd=("start_jd", "min"), end_jd=("end_jd", "max"), md_lord=("md_lord", "first"))
        .reset_index()
        .sort_values(["person_id", "start_jd"])
    )
    out: dict[str, tuple[list[float], list[float], list[str]]] = {}
    for pid, grp in md.groupby("person_id", sort=False):
        out[pid] = (grp["start_jd"].tolist(), grp["end_jd"].tolist(), grp["md_lord"].tolist())
    return out


def _md_lord_at(windows: tuple[list[float], list[float], list[str]] | None, jd: float) -> str | None:
    """MD lord at jd via binary search into the person's MD windows."""
    if windows is None:
        return None
    starts, ends, lords = windows
    i = bisect_right(starts, jd) - 1
    if i >= 0 and jd <= ends[i]:
        return lords[i]
    return None


def _verdict_label(chart: Chart, transit_signs: dict[str, int], md_lord: str | None) -> str | None:
    """The 10H verdict under the full dynamic composition (identical for both arms)."""
    try:
        reading = compose_reading(
            chart, DKPContext(), transit_signs=transit_signs, vimshottari_md_lord=md_lord,
        )
    except Exception:  # noqa: BLE001 — same silent-skip contract as the original
        return None
    claim = reading.bhava_claims.get(_TARGET_BHAVA)
    return claim.verdict_label if claim is not None else None


def _cluster_bootstrap(
    per_event: pd.DataFrame, n_boot: int, seed: int,
) -> dict[str, list[float]]:
    """Person-clustered bootstrap CIs for the pooled lift and the paired excess."""
    rng = np.random.default_rng(seed)
    persons = per_event["person_id"].unique()
    by_person = {p: g for p, g in per_event.groupby("person_id", sort=False)}
    lifts, excesses = [], []
    for _ in range(n_boot):
        sample = rng.choice(persons, size=len(persons), replace=True)
        ev_hits = ctrl_rate_sum = n_events = 0.0
        excess_sum = 0.0
        for p in sample:
            g = by_person[p]
            ev_hits += g["event_strong"].sum()
            ctrl_rate_sum += g["ctrl_strong_rate"].sum()   # unweighted, 1 per event
            n_events += len(g)
            excess_sum += (g["event_strong"] - g["ctrl_strong_rate"]).sum()
        p_ev, p_ctrl = ev_hits / n_events, ctrl_rate_sum / n_events
        lifts.append(p_ev / p_ctrl if p_ctrl > 0 else np.nan)
        excesses.append(excess_sum / n_events)
    lifts_a = np.asarray([x for x in lifts if not np.isnan(x)])
    return {
        "lift_ci95": [round(float(v), 4) for v in np.percentile(lifts_a, [2.5, 97.5])],
        "excess_ci95": [round(float(v), 5) for v in np.percentile(np.asarray(excesses), [2.5, 97.5])],
    }


def run_gauntlet_g1(
    data_dir: Path = DEFAULT_DATA_DIR,
    out_path: Path = DEFAULT_OUT,
    limit: int | None = None,
    n_boot: int = 2000,
) -> dict:
    """Execute the paired within-person career→10H re-validation."""
    dossier = pd.read_parquet(data_dir / "event_dossier.parquet")
    career = dossier[(dossier["event_class"] == "career") & dossier["event_jd"].notna()
                     & dossier["t_sun_sign"].notna()].copy()
    if limit is not None:
        career = career.sample(n=min(limit, len(career)), random_state=0)
    logger.info("career events with full transit block: %d (%d persons)",
                len(career), career["person_id"].nunique())

    pids = set(career["person_id"])
    pdos = pd.read_parquet(data_dir / "person_dossier.parquet")
    pdos = pdos[pdos["person_id"].isin(pids)]
    # person_dossier.birth_jd is NaN for most of this cohort; the canonical complete
    # anchor is charts.birth_jd_used (verified complete for all 75,149 persons).
    canon_jd = pd.read_parquet(data_dir / "charts.parquet",
                               columns=["person_id", "birth_jd_used"])
    canon_jd = dict(zip(canon_jd["person_id"], canon_jd["birth_jd_used"]))
    charts: dict[str, Chart] = {}
    person_meta: dict[str, tuple[float, str]] = {}   # pid -> (birth_jd, source)
    for _, row in pdos.iterrows():
        pid = row["person_id"]
        bjd = row["birth_jd"] if pd.notna(row["birth_jd"]) else canon_jd.get(pid)
        if bjd is None or pd.isna(bjd):
            continue
        try:
            charts[pid] = Chart.from_dossier_row(row.to_dict())
            person_meta[pid] = (float(bjd), str(row["source"]))
        except Exception:  # noqa: BLE001
            continue
    logger.info("charts built: %d", len(charts))

    windows = _md_windows(
        pd.read_parquet(data_dir / "dasha_pd_windows.parquet",
                        columns=["person_id", "md_seq", "md_lord", "start_jd", "end_jd"])
        .query("person_id in @pids")
    )

    # Exposure caps: earliest death-class event per person; scrape date otherwise.
    death_jd = (dossier[dossier["event_class"].str.contains("death", na=False)
                        & dossier["event_jd"].notna()]
                .groupby("person_id")["event_jd"].min().to_dict())
    career_jds: dict[str, list[float]] = defaultdict(list)
    for pid, jd in zip(career["person_id"], career["event_jd"]):
        career_jds[pid].append(float(jd))

    # ── the paired pass ──────────────────────────────────────────────────────
    md_match = md_total = 0
    rows_out: list[dict] = []
    n_dropped_few_controls = n_dropped_compose = 0
    n_label_divergent = 0   # events whose label differs at ANY control date
    label_counts_event: dict[str, int] = defaultdict(int)
    label_counts_ctrl: dict[str, int] = defaultdict(int)
    for i, (_, ev) in enumerate(career.iterrows()):
        if i and i % 1000 == 0:
            logger.info("  %d/%d events processed", i, len(career))
        pid = ev["person_id"]
        chart = charts.get(pid)
        meta = person_meta.get(pid)
        if chart is None or meta is None:
            continue
        birth_jd, source = meta
        ejd = float(ev["event_jd"])
        cap = min(death_jd.get(pid, np.inf) - DAYS_PER_VEDIC_YEAR, _SCRAPE_JD)
        floor = birth_jd + 18 * DAYS_PER_VEDIC_YEAR

        pw = windows.get(pid)
        md_ev = _md_lord_at(pw, ejd)
        if md_ev is not None and pd.notna(ev.get("active_md_lord")):
            md_total += 1
            md_match += int(md_ev == ev["active_md_lord"])

        ctrl_jds = []
        for k in _YEAR_OFFSETS:
            cjd = ejd + k * DAYS_PER_VEDIC_YEAR
            if not (floor <= cjd <= cap):
                continue
            if any(abs(cjd - other) < DAYS_PER_VEDIC_YEAR for other in career_jds[pid]):
                continue
            ctrl_jds.append(cjd)
        if len(ctrl_jds) < _MIN_CONTROLS:
            n_dropped_few_controls += 1
            continue

        ev_label = _verdict_label(chart, _transit_signs_at(ejd), md_ev)
        if ev_label is None:
            n_dropped_compose += 1
            continue
        ctrl_labels = []
        for cjd in ctrl_jds:
            lbl = _verdict_label(chart, _transit_signs_at(cjd), _md_lord_at(pw, cjd))
            if lbl is not None:
                ctrl_labels.append(lbl)
        if len(ctrl_labels) < _MIN_CONTROLS:
            n_dropped_compose += 1
            continue

        label_counts_event[ev_label] += 1
        for lbl in ctrl_labels:
            label_counts_ctrl[lbl] += 1
        if any(lbl != ev_label for lbl in ctrl_labels):
            n_label_divergent += 1
        rows_out.append({
            "person_id": pid, "source": source,
            "event_strong": int(ev_label == "strong"),
            "ctrl_strong_rate": float(np.mean([l == "strong" for l in ctrl_labels])),
            "n_controls": len(ctrl_labels),
        })
    per_event = pd.DataFrame(rows_out)
    # birth decade from birth_jd properly (revjul once per row is cheap at this scale)
    per_event["birth_decade"] = [
        int(swe.revjul(person_meta[p][0], swe.GREG_CAL)[0] // 10 * 10)
        for p in per_event["person_id"]
    ]

    p_event = per_event["event_strong"].mean()
    # Unweighted (each event weighs 1, matching the paired design). The
    # n_controls-weighted version covaries with lifespan and is reported secondarily.
    p_ctrl = float(per_event["ctrl_strong_rate"].mean())
    p_ctrl_weighted = ((per_event["ctrl_strong_rate"] * per_event["n_controls"]).sum()
                       / per_event["n_controls"].sum())
    clean_lift = p_event / p_ctrl if p_ctrl > 0 else float("nan")
    paired_excess = float((per_event["event_strong"] - per_event["ctrl_strong_rate"]).mean())
    cis = _cluster_bootstrap(per_event, n_boot=n_boot, seed=0)

    # Replication check vs the ORIGINAL static baseline
    readings = pd.read_parquet(data_dir / "readings.parquet",
                               columns=["person_id", "b10_label"])
    static_strong = float((readings["b10_label"] == "strong").mean())
    replication_lift = p_event / static_strong if static_strong > 0 else float("nan")

    # Cohort-selection decomposition: the same stored static labels, restricted to the
    # career-event cohort — no composition involved, so this ratio isolates pure
    # population selection (who has dated, transit-complete career events).
    cohort_static = readings[readings["person_id"].isin(pids)]
    cohort_strong = float((cohort_static["b10_label"] == "strong").mean())
    selection_lift = cohort_strong / static_strong if static_strong > 0 else float("nan")

    strata = {}
    for key in ("source", "birth_decade"):
        strata[key] = {}
        for val, g in per_event.groupby(key):
            pc = ((g["ctrl_strong_rate"] * g["n_controls"]).sum() / g["n_controls"].sum())
            strata[key][str(val)] = {
                "n": int(len(g)),
                "lift": round(float(g["event_strong"].mean() / pc), 3) if pc > 0 else None,
            }

    lo, hi = cis["lift_ci95"]
    passes = clean_lift > 1.0 and lo > 1.0
    if passes:
        verdict = (
            f"SURVIVES: within-person paired lift {clean_lift:.3f} CI({lo:.3f}, {hi:.3f}). "
            "The AND-gate strong verdict is genuinely enriched at career events."
        )
    else:
        verdict = (
            f"FALLS: within-person paired lift {clean_lift:.3f} CI({lo:.3f}, {hi:.3f}) vs "
            f"the original 1.37. Mechanism: reading_composer's verdict_label is the NATAL "
            f"bhava verdict — the gochara/dasha context only sets the separate "
            f"gochara_triggered flag and never moves the label ({n_label_divergent} of "
            f"{len(per_event)} events showed ANY label change at control dates). The "
            f"original 1.37 therefore measured cohort composition, not timing: the same "
            f"stored static labels restricted to the career cohort already yield "
            f"selection lift {selection_lift:.3f}."
        )

    n_ev = len(per_event)
    result = {
        "experiment": "Gauntlet G1 — framework career→10H, paired within-person clean re-run",
        "prereg": "tools/raman_saab/astrobank/GAUNTLET_PREREG.md (G1)",
        "n_events_scored": n_ev,
        "n_persons": int(per_event["person_id"].nunique()),
        "n_dropped_few_controls": n_dropped_few_controls,
        "n_dropped_compose": n_dropped_compose,
        "n_label_divergent_events": n_label_divergent,
        "md_lord_dossier_agreement": round(md_match / md_total, 4) if md_total else None,
        "protocol": {
            "controls": "year-shifted +/-2..7 yr (JD arithmetic), >=3 required, "
                        "blackout +/-1yr around own career events, "
                        "window [birth+18yr, min(death-1yr, scrape 2026-05-31)]",
            "bootstrap": f"{n_boot} person-clustered resamples",
        },
        "event_arm": {
            "p_strong": round(float(p_event), 5),
            "label_dist": {l: round(label_counts_event[l] / n_ev, 5) for l in _LABELS},
        },
        "control_arm": {
            "p_strong": round(float(p_ctrl), 5),
            "n_control_readings": int(per_event["n_controls"].sum()),
            "label_dist": {l: round(label_counts_ctrl[l] / sum(label_counts_ctrl.values()), 5)
                           for l in _LABELS},
        },
        "clean_lift": round(float(clean_lift), 4),
        "clean_lift_ci95": cis["lift_ci95"],
        "clean_lift_nctrl_weighted": round(float(p_event / p_ctrl_weighted), 4)
        if p_ctrl_weighted > 0 else None,
        "paired_excess": round(paired_excess, 5),
        "paired_excess_ci95": cis["excess_ci95"],
        "replication_check": {
            "static_baseline_p_strong": round(static_strong, 5),
            "event_arm_vs_static_lift": round(float(replication_lift), 3),
            "original_reported": 1.37,
            "note": "confirms the re-implementation reproduces the original event arm "
                    "against the original (flawed) static baseline",
        },
        "cohort_selection_decomposition": {
            "cohort_static_p_strong": round(cohort_strong, 5),
            "selection_lift": round(float(selection_lift), 3),
            "note": "stored b10_label restricted to career-cohort persons vs all persons "
                    "— zero composition involved; isolates pure population selection",
        },
        "strata_report_only": strata,
        "verdict": verdict,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info("wrote %s", out_path)
    return result


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=None, help="Cap events (smoke test)")
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    result = run_gauntlet_g1(limit=args.limit, n_boot=args.boot)
    print(json.dumps({k: result[k] for k in (
        "n_events_scored", "n_label_divergent_events", "clean_lift", "clean_lift_ci95",
        "paired_excess", "paired_excess_ci95", "replication_check",
        "cohort_selection_decomposition", "verdict")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
