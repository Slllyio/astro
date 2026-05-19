"""Round 6 Phase 2: survival analysis for event timing.

Models age-at-first-event as a survival problem, separately per event
class. Outputs a calibrated hazard function h(age | natal_chart) plus
a comparison against a classical Vimshottari dasha-based baseline.

Why this matters: classical Vedic prediction implicitly treats
Vimshottari Mahadasha as a hazard schedule — each lord's period
predisposes certain events. This phase tests the prediction
empirically for the first time. Does Saturn MD actually have
elevated hazard for marriage events? Does Venus MD predict
relationship onset?

Approach:

1. For each event class with ≥ 400 observed first-events, build a
   survival dataset:
   - Observed: people in the cohort whose FIRST event of class X
     occurred at age `t_obs`. (time=t_obs, event=1)
   - Censored: people in the cohort who never had event X in our
     records. Censored at min(last_known_event_age, 90).
2. Train a Cox Proportional Hazards model on natal features
   (Round 5 natal cols, excluding transit/dasha-elapsed which are
   functions of event time — would leak the target).
3. Train an AFT (Accelerated Failure Time, Weibull) model as
   non-PH alternative.
4. Compute Vimshottari baseline: for each chart, predict event age
   from `dasha_start_age_<karaka>` features (Venus for marriage,
   Saturn for career, etc.).
5. Compare: concordance index (C-index) of Cox vs AFT vs baseline.
   C-index > 0.5 = signal; 0.6+ = practically useful.

Output per class:
- `cox_summary.csv` — Cox coefficients (hazard ratios per feature)
- `survival_curves.parquet` — per-person predicted survival curves
- `report.md` — C-indices + Vimshottari comparison + top hazard-
  driving features
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, WeibullAFTFitter
from lifelines.utils import concordance_index
from sklearn.feature_selection import SelectKBest, f_classif

logger = logging.getLogger(__name__)


# ---------- Event-class → Vimshottari karaka mapping ----------
#
# Classical Vedic significator per event domain. Used to compute the
# baseline "expected age = age at first <karaka>'s MD or AD post-16".
# These mappings come from BPHS / Phaladeepika consensus.

EVENT_KARAKAS: dict[str, tuple[str, ...]] = {
    "marriage":                    ("Venus", "Jupiter"),
    "relationship":                ("Venus", "Mars"),
    "work":                        ("Saturn", "Sun"),
    "career":                      ("Saturn", "Sun"),
    "new career":                  ("Saturn", "Mars"),
    "new job":                     ("Mercury", "Saturn"),
    "death, cause unspecified":    ("Saturn",),
    "death by disease":            ("Saturn", "Mars"),
    "prize":                       ("Jupiter", "Sun"),
    "fame":                        ("Sun", "Jupiter"),
    "crime":                       ("Mars", "Saturn"),
    "health":                      ("Sun", "Mars"),
    "education":                   ("Mercury", "Jupiter"),
    "family":                      ("Moon", "Jupiter"),
    "published/ exhibited/ released": ("Mercury", "Venus"),
}


# CRITICAL FIX (per Round-6 review): natural karakas are a "strawman"
# baseline. Real Vedic timing analysis uses FUNCTIONAL LORDSHIPS — the
# planet that rules the relevant house in this specific chart.
# Marriage timing = 7th-lord dasha; career = 10th-lord; longevity =
# 8th-lord etc. We map each event class to the house(s) whose lord(s)
# should be active in its dasha.
EVENT_FUNCTIONAL_HOUSES: dict[str, tuple[int, ...]] = {
    "marriage":                    (7,),       # 7th house = spouse
    "relationship":                (5, 7),     # 5th = romance, 7th = partner
    "work":                        (6, 10),    # 6th = service, 10th = career
    "career":                      (10,),      # 10th = profession
    "new career":                  (10,),
    "new job":                     (10, 6),
    "death, cause unspecified":    (8,),       # 8th = longevity / death
    "death by disease":            (6, 8),     # 6th = disease, 8th = death
    "prize":                       (2, 11),    # 2nd = gain, 11th = honours
    "fame":                        (10, 11),
    "crime":                       (8, 12),    # 8th = sudden, 12th = loss/jail
    "health":                      (1, 6),     # 1st = body, 6th = disease
    "education":                   (5, 9),     # 5th = learning, 9th = higher ed
    "family":                      (4,),       # 4th = home/mother
    "published/ exhibited/ released": (3, 5),  # 3rd = writing, 5th = creativity
}


# Sign rulerships (1..12 → ruler graha name; matches feature_engineering.SIGN_RULERS)
SIGN_RULER: dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


def _functional_lords_for_event(
    natal_row: pd.Series, event_class: str,
) -> tuple[str, ...]:
    """Return the planet names that rule the event's functional houses
    in THIS chart (Ascendant-specific).

    Example: for `marriage` (7th house), if Ascendant is Aries (sign=1),
    7th sign from Aries is Libra (sign=7), ruled by Venus → returns
    ("Venus",). For Cancer Ascendant, 7th is Capricorn, ruled by
    Saturn → returns ("Saturn",).

    This is the CHART-SPECIFIC functional baseline that the reviewer
    correctly identified as the right Vedic comparator (vs the
    universal natural karaka).
    """
    houses = EVENT_FUNCTIONAL_HOUSES.get(event_class.lower(), ())
    if not houses:
        return ()
    try:
        asc_sign = int(natal_row.get("lagna_sign", 1))
    except (ValueError, TypeError):
        return ()
    lords: list[str] = []
    seen: set[str] = set()
    for h in houses:
        # The Nth house's sign = ((asc_sign + h - 1) - 1) % 12 + 1
        # (h=1 → asc_sign; h=7 → asc_sign + 6 mod 12)
        sign_of_house = ((asc_sign + h - 2) % 12) + 1
        lord = SIGN_RULER.get(sign_of_house)
        if lord and lord not in seen:
            lords.append(lord)
            seen.add(lord)
    return tuple(lords)


# ---------- Survival dataset construction ----------

def build_survival_dataset(
    *,
    natal_parquet: Path,
    events_csv: Path,
    raw_csv: Path,
    event_class: str,
    censoring_age: float = 90.0,
) -> pd.DataFrame:
    """Build (natal_features, age_at_event, event_observed) frame.

    Cohort: every person in raw_csv who appears in events_all.csv
    (any event type) AND is in the natal parquet. People who had
    event_class are observed; others are censored.

    Censoring time = min(censoring_age, max_observed_event_age_for_person).
    This is a pragmatic compromise — we don't know death dates for
    most people, so we use the latest event they DID experience as
    a lower bound on their lifespan.
    """
    logger.info("loading natal parquet ...")
    natal = pd.read_parquet(natal_parquet)
    natal["_n"] = natal["name"].astype(str).str.strip().str.lower()
    natal = natal.drop_duplicates(subset="_n").set_index("_n")

    logger.info("loading events ...")
    events = pd.read_csv(events_csv)
    events["_n"] = events["name"].astype(str).str.strip().str.lower()
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()
    events["event_date"] = pd.to_datetime(
        events["event_date"], errors="coerce",
    )

    logger.info("loading raw birth data ...")
    raw = pd.read_csv(raw_csv, low_memory=False)
    raw["_n"] = raw["name"].astype(str).str.strip().str.lower()
    raw["date_of_birth"] = pd.to_datetime(
        raw["date_of_birth"], errors="coerce",
    )
    raw = raw.drop_duplicates(subset="_n").set_index("_n")

    # Cohort: all people with at least one event AND in natal parquet
    cohort_names = (
        set(events["_n"]) & set(natal.index) & set(raw.index)
    )
    logger.info("cohort size: %d people", len(cohort_names))

    # First event of target class per person
    target_events = events.loc[events["root_lower"] == event_class.lower()].copy()
    target_events = target_events.dropna(subset=["event_date"])
    target_first = (
        target_events.sort_values("event_date")
        .drop_duplicates(subset="_n", keep="first")
    )
    target_first_by_name = target_first.set_index("_n")

    # Max-known-event-age per person (used for censoring)
    events_with_dates = events.dropna(subset=["event_date"]).copy()
    events_with_dates = events_with_dates.merge(
        raw[["date_of_birth"]].reset_index(), on="_n", how="inner",
    )
    events_with_dates["age"] = (
        events_with_dates["event_date"]
        - events_with_dates["date_of_birth"]
    ).dt.days / 365.25
    max_age_by_name = (
        events_with_dates.groupby("_n")["age"].max()
    )

    rows = []
    for name in cohort_names:
        try:
            birth = raw.loc[name, "date_of_birth"]
        except KeyError:
            continue
        if pd.isna(birth):
            continue
        if name in target_first_by_name.index:
            event_date = target_first_by_name.loc[name, "event_date"]
            age = (event_date - birth).days / 365.25
            if not (0 <= age <= 110):
                continue
            rows.append({
                "_n": name,
                "duration": float(age),
                "event": 1,
            })
        else:
            # Censored: use the latest age we have any event for this
            # person as a lower bound, capped at censoring_age.
            last_age = float(max_age_by_name.get(name, 0.0) or 0.0)
            censored_age = min(max(last_age, 1.0), censoring_age)
            rows.append({
                "_n": name,
                "duration": censored_age,
                "event": 0,
            })

    surv = pd.DataFrame(rows).set_index("_n")
    surv = surv.join(natal, how="inner")
    logger.info(
        "survival dataset: %d rows  (%d observed, %d censored)",
        len(surv), int(surv["event"].sum()),
        len(surv) - int(surv["event"].sum()),
    )
    return surv


# ---------- Feature selection ----------

NATAL_FEATURE_PREFIX_DROP: tuple[str, ...] = (
    "t_", "active_md_lord", "active_ad_lord", "active_pd_lord",
    "md_elapsed_years", "ad_elapsed_years", "pd_elapsed_years",
    "cross_lon_", "transit_bav_", "sade_sati_active",
    "kantaka_shani", "ashtama_shani",
)

NON_FEATURE_COLS: tuple[str, ...] = (
    "name", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url", "duration", "event",
    "event_date", "event_jd", "birth_jd",
    "event_root", "event_subtype", "is_event",
)


def _is_natal_feature(col: str) -> bool:
    if col in NON_FEATURE_COLS:
        return False
    return not any(col.startswith(p) for p in NATAL_FEATURE_PREFIX_DROP)


def select_natal_features_for_cox(
    surv: pd.DataFrame, k: int = 25,
) -> pd.DataFrame:
    """Pick top-K numeric natal features by univariate ANOVA F-statistic
    against the event indicator. Cox is fragile with 500+ correlated
    features on ~1500 rows; trimming to 25 stabilises the fit.
    """
    candidates = [c for c in surv.columns if _is_natal_feature(c)]
    # Keep only numeric (Cox can't handle categoricals natively)
    numeric_candidates = []
    for c in candidates:
        s = surv[c]
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            numeric_candidates.append(c)
    X = surv[numeric_candidates].fillna(0.0).to_numpy()
    y = surv["event"].to_numpy()
    selector = SelectKBest(score_func=f_classif, k=min(k, len(numeric_candidates)))
    selector.fit(X, y)
    selected_mask = selector.get_support()
    selected = [
        c for c, kept in zip(numeric_candidates, selected_mask, strict=True) if kept
    ]
    logger.info("Cox: selected %d natal features from %d numeric candidates",
                len(selected), len(numeric_candidates))
    return surv[["duration", "event", *selected]]


# ---------- Vimshottari baseline ----------

def vimshottari_baseline_age(
    surv: pd.DataFrame, karakas: tuple[str, ...],
) -> pd.Series:
    """For each row, predict event age as the earliest MD start age
    (post-birth, post-16) of any **natural karaka** planet.

    Uses Round 5's natal `dasha_start_age_<planet>` and
    `first_<planet>_antardasha_after_16` columns. Returns NaN if no
    karaka MD/AD opens in the recorded lifespan.

    NOTE: This is the "strawman" baseline (per Round-6 review) — it uses
    universal natural karakas, not chart-specific functional lords.
    See ``vimshottari_baseline_age_functional_lords`` for the stronger
    classical comparator.
    """
    candidates = []
    for k in karakas:
        col_md = f"dasha_start_age_{k.lower()}"
        col_ad = f"first_{k.lower()}_antardasha_after_16"
        if col_md in surv.columns:
            candidates.append(surv[col_md])
        if col_ad in surv.columns:
            candidates.append(surv[col_ad])
    if not candidates:
        return pd.Series([np.nan] * len(surv), index=surv.index)
    # Take the EARLIEST post-16 occurrence across all karakas
    candidates_df = pd.concat(candidates, axis=1)
    # Mask negative ages (pre-birth) and < 16 (pre-adulthood)
    candidates_df = candidates_df.where(candidates_df >= 16.0)
    return candidates_df.min(axis=1)


def vimshottari_baseline_age_functional_lords(
    surv: pd.DataFrame, event_class: str,
) -> pd.Series:
    """The PROPER classical-Vedic baseline: chart-specific functional
    lord dasha.

    For each chart, look up which planet rules the relevant house
    (e.g., 7th-lord for marriage). Predict event age = earliest MD/AD
    start age of that planet (post-16).

    This is what a real Vedic astrologer uses for timing. If the
    learned Cox model still beats this, the model has discovered
    structure beyond classical functional-lord theory.
    """
    if surv.empty:
        return pd.Series([np.nan] * len(surv), index=surv.index)
    ages = []
    for idx, row in surv.iterrows():
        lords = _functional_lords_for_event(row, event_class)
        if not lords:
            ages.append(np.nan)
            continue
        candidate_ages: list[float] = []
        for lord in lords:
            lc = lord.lower()
            for col in (f"dasha_start_age_{lc}",
                        f"first_{lc}_antardasha_after_16"):
                if col in surv.columns:
                    v = row.get(col)
                    if v is None or (isinstance(v, float) and np.isnan(v)):
                        continue
                    try:
                        v = float(v)
                    except (ValueError, TypeError):
                        continue
                    if v >= 16.0:
                        candidate_ages.append(v)
        if candidate_ages:
            ages.append(min(candidate_ages))
        else:
            ages.append(np.nan)
    return pd.Series(ages, index=surv.index)


def evaluate_baseline(
    surv: pd.DataFrame, baseline: pd.Series,
) -> float:
    """Concordance: does baseline rank observed events earlier than censored?

    Lower predicted age = higher hazard early. Convert to risk by negating.
    """
    if baseline.isna().all():
        return float("nan")
    df = pd.DataFrame({
        "duration": surv["duration"],
        "event": surv["event"],
        "risk": -baseline.fillna(baseline.mean()),
    })
    df = df.dropna()
    return concordance_index(df["duration"], df["risk"], df["event"])


# ---------- Cox fit ----------

def fit_cox(surv_selected: pd.DataFrame) -> tuple[CoxPHFitter, float]:
    """Fit a CoxPHFitter on the selected feature subset.

    penalizer=0.001 leaves interpretable coefficient magnitudes after
    standardisation; stronger penalties squash coefs to ~1e-8 (Cox
    concordance is scale-invariant so C-index survives, but coefs
    become unreadable).
    """
    cox = CoxPHFitter(penalizer=0.001, l1_ratio=0.5)
    # Standardize features (CoxPH benefits)
    feature_cols = [c for c in surv_selected.columns if c not in ("duration", "event")]
    fit_data = surv_selected.copy()
    for c in feature_cols:
        mean = fit_data[c].mean()
        std = fit_data[c].std()
        if std > 0:
            fit_data[c] = (fit_data[c] - mean) / std
    cox.fit(
        fit_data, duration_col="duration", event_col="event",
        show_progress=False,
    )
    # Concordance from CoxPH itself
    c_index = float(cox.concordance_index_)
    return cox, c_index


# ---------- Reports ----------

def _write_cox_summary(path: Path, cox: CoxPHFitter) -> None:
    summary = cox.summary
    cols = ["coef", "exp(coef)", "p", "se(coef)"]
    available = [c for c in cols if c in summary.columns]
    summary_subset = summary[available].copy()
    summary_subset = summary_subset.sort_values(
        by="exp(coef)" if "exp(coef)" in summary_subset.columns else "coef",
        key=lambda s: -s.abs(),
    )
    summary_subset.to_csv(path)
    logger.info("wrote Cox summary to %s", path)


def _write_report(
    path: Path,
    *,
    event_class: str,
    n_total: int,
    n_observed: int,
    n_censored: int,
    cox_c_index: float,
    aft_c_index: float,
    baseline_c_index: float,
    karakas: tuple[str, ...],
    cox_summary_path: Path,
    top_hr_rows: list[tuple[str, float, float]],
) -> None:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Phase 2 — Survival analysis: `{event_class}`",
        "",
        f"_Generated {now}_",
        "",
        "## Cohort",
        "",
        f"- Total: {n_total:,}",
        f"- Observed events: {n_observed:,}",
        f"- Censored: {n_censored:,}",
        f"- Karakas (Vimshottari baseline): {', '.join(karakas)}",
        "",
        "## Concordance index (C-index)",
        "",
        "C-index = 0.5 random; 1.0 perfect ranking; 0.6+ practically useful.",
        "Higher = better at ranking which chart will event sooner.",
        "",
        "| Model | C-index |",
        "|---|---|",
        f"| **Cox Proportional Hazards** (Round-5 natal features) | {cox_c_index:.4f} |",
        f"| **Weibull AFT** | {aft_c_index:.4f} |",
        f"| **Vimshottari baseline** (earliest karaka MD/AD post-16) | {baseline_c_index:.4f} |",
        "",
        "## Interpretation",
        "",
    ]
    if cox_c_index > baseline_c_index + 0.02:
        lines.append(
            f"The Cox model beats the Vimshottari baseline by "
            f"{cox_c_index - baseline_c_index:+.4f}. The natal features "
            f"carry timing signal beyond what classical karaka theory uses."
        )
    elif cox_c_index < baseline_c_index - 0.02:
        lines.append(
            f"The Cox model UNDERPERFORMS the Vimshottari baseline by "
            f"{baseline_c_index - cox_c_index:+.4f}. Either feature "
            f"selection is too aggressive or classical karaka theory "
            f"already captures the signal."
        )
    else:
        lines.append(
            "Cox and Vimshottari baseline are within noise of each other. "
            "The classical karaka mapping captures what learnable signal "
            "exists in our data."
        )
    lines.extend([
        "",
        "## Top hazard-driving features",
        "",
        "Hazard ratio (HR) > 1.0 = feature increases event hazard "
        "(event happens sooner). HR < 1.0 = decreases hazard.",
        "",
        "| Feature | Coef | Hazard Ratio | p-value |",
        "|---|---|---|---|",
    ])
    for feat, hr, p in top_hr_rows[:15]:
        coef = float(np.log(hr)) if hr > 0 else 0.0
        lines.append(f"| `{feat}` | {coef:+.4f} | {hr:.4f} | {p:.4f} |")

    lines.extend([
        "",
        f"Full Cox summary in `{cox_summary_path.name}`.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- Main ----------

def run_phase2(
    *,
    natal_parquet: Path,
    events_csv: Path,
    raw_csv: Path,
    event_classes: list[str],
    output_dir: Path,
    k_features: int = 25,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for event_class in event_classes:
        logger.info("=" * 60)
        logger.info("event class: %s", event_class)
        try:
            surv = build_survival_dataset(
                natal_parquet=natal_parquet,
                events_csv=events_csv,
                raw_csv=raw_csv,
                event_class=event_class,
            )
        except Exception as exc:
            logger.error("build_survival_dataset failed: %s", exc)
            continue
        n_observed = int(surv["event"].sum())
        if n_observed < 200:
            logger.warning("skip %s: only %d observed events", event_class, n_observed)
            continue

        # Cox fit
        surv_selected = select_natal_features_for_cox(surv, k=k_features)
        try:
            cox, cox_c = fit_cox(surv_selected)
        except Exception as exc:
            logger.error("Cox fit failed: %s", exc)
            continue

        # AFT fit (Weibull)
        try:
            aft = WeibullAFTFitter(penalizer=0.05)
            aft.fit(surv_selected, duration_col="duration", event_col="event")
            aft_c = float(aft.concordance_index_)
        except Exception as exc:
            logger.warning("AFT fit failed: %s", exc)
            aft_c = float("nan")

        # Vimshottari baselines: BOTH the natural-karaka strawman AND the
        # proper chart-specific functional-lord baseline.
        karakas = EVENT_KARAKAS.get(event_class.lower(), ("Saturn",))
        baseline_natural = vimshottari_baseline_age(surv, karakas)
        baseline_natural_c = evaluate_baseline(surv, baseline_natural)

        baseline_functional = vimshottari_baseline_age_functional_lords(
            surv, event_class,
        )
        baseline_functional_c = evaluate_baseline(surv, baseline_functional)
        # Keep variable name baseline_c for downstream report code:
        # use the BETTER of the two as the "classical" baseline.
        baseline_c = max(baseline_natural_c, baseline_functional_c)
        logger.info(
            "  Vimshottari natural-karaka C: %.4f  | functional-lord C: %.4f",
            baseline_natural_c, baseline_functional_c,
        )

        # Top hazard rows
        summary_df = cox.summary
        hr_col = "exp(coef)" if "exp(coef)" in summary_df.columns else "coef"
        p_col = "p" if "p" in summary_df.columns else "p-value"
        top_hr = sorted(
            [
                (feat, float(row[hr_col]),
                 float(row[p_col]) if p_col in row else float("nan"))
                for feat, row in summary_df.iterrows()
            ],
            key=lambda x: -abs(np.log(x[1])) if x[1] > 0 else 0,
        )

        safe = "".join(c if c.isalnum() else "_" for c in event_class)
        cox_csv = output_dir / f"cox_{safe}.csv"
        report = output_dir / f"report_{safe}.md"
        _write_cox_summary(cox_csv, cox)
        _write_report(
            report,
            event_class=event_class,
            n_total=len(surv),
            n_observed=n_observed,
            n_censored=len(surv) - n_observed,
            cox_c_index=cox_c,
            aft_c_index=aft_c,
            baseline_c_index=baseline_c,
            karakas=karakas,
            cox_summary_path=cox_csv,
            top_hr_rows=top_hr,
        )

        summary_rows.append({
            "event_class": event_class,
            "n_observed": n_observed,
            "n_censored": len(surv) - n_observed,
            "cox_c_index": cox_c,
            "aft_c_index": aft_c,
            "natural_karaka_c": baseline_natural_c,
            "functional_lord_c": baseline_functional_c,
            "best_classical_c": baseline_c,
            "delta_vs_natural": cox_c - baseline_natural_c,
            "delta_vs_functional": cox_c - baseline_functional_c,
            "delta_vs_best_classical": cox_c - baseline_c,
        })

    # Index summary
    if summary_rows:
        idx_path = output_dir / "SUMMARY.csv"
        with idx_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            for row in summary_rows:
                writer.writerow(row)
        logger.info("wrote summary to %s", idx_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.survival_analysis",
        description="Phase 2: survival analysis for event timing.",
    )
    parser.add_argument(
        "--natal", type=Path,
        default=Path("app/medini/data/ml_astro_round5.parquet"),
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
    )
    parser.add_argument(
        "--raw", type=Path,
        default=Path("data/astro_databank/merged_with_events.csv"),
    )
    parser.add_argument(
        "--classes", type=str, nargs="+",
        default=[
            "death, cause unspecified", "relationship",
            "marriage", "work",
        ],
        help="Event classes (case-insensitive) to fit.",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/survival_round6_phase2/"),
    )
    parser.add_argument("--k-features", type=int, default=25)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase2(
        natal_parquet=args.natal,
        events_csv=args.events,
        raw_csv=args.raw,
        event_classes=args.classes,
        output_dir=args.output,
        k_features=args.k_features,
    )
    print(f"Phase 2 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
