"""Backtest the assembled death-window predictor against real deaths.

The doctrine validators proved each *ingredient* (maraka, composite confluence,
longevity bracket) at population scale. This module tests the *assembled ranker*:
given a decedent's chart, does the predictor concentrate their actual death in the
windows it calls high-risk — and does it beat the obvious confound?

The confound: a death is more likely in a *long* window simply because it spans more
time-at-risk. So we score three NESTED models of P(death lands in window w), and ask
what each successive lever adds:

    M0:  P(w) ∝ duration_w                                   (pure time-at-risk)
    M1:  P(w) ∝ duration_w · bracket_factor(age_w)           (+ age-of-death shape)
    M2:  P(w) ∝ duration_w · bracket_factor · composite(md)  (+ lord-specific signal)

For every test death we read off the probability each model assigned to the window
that *actually* occurred, and compare mean per-death log-likelihood. M0→M1 measures
how much the āyurdāya bracket helps (largely the empirical age-at-death shape); the
**headline is M1→M2** — does *which lord runs* add predictive power once age and
duration are already accounted for?

Leakage control: the bracket + composite factors are calibrated on a TRAIN split of
persons and the likelihoods are evaluated on a disjoint TEST split, so no test death
informs its own risk factors.

Usage:
    python -m app.medini.analysis.death_backtest
    python -m app.medini.analysis.death_backtest --test-frac 0.25 --event-class death_cause_unspecified
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import math
from dataclasses import asdict, dataclass
from typing import Any, Final

import duckdb

from app.medini.analysis import doctrine_validator as dv
from app.medini.analysis import death_window_predictor as dwp
from app.medini.analysis.death_window_predictor import _bracket_for_age, _role_count

logger = logging.getLogger(__name__)

_DAYS_PER_YEAR: Final = 365.2425


def _in_test(person_id: str, test_frac: float, salt: str = "bt1") -> bool:
    """Deterministic person-level split via a stable hash (no global RNG state)."""
    h = hashlib.md5(f"{salt}:{person_id}".encode()).hexdigest()
    return (int(h[:8], 16) / 0xFFFFFFFF) < test_frac


def _calibrate_on_train(
    con: duckdb.DuckDBPyConnection, train_ids: set[str],
    event_class: str, level: str,
) -> tuple[dict[int, float], dict[str, float]]:
    """Run the real validators on a TRAIN-only in-memory catalog so the risk
    factors never see a test death."""
    charts_df = con.execute("SELECT * FROM charts").df()
    ev_df = con.execute(
        f"SELECT * FROM events_with_dasha WHERE event_class = '{dv._q(event_class)}'"
    ).df()
    ev_df = ev_df[ev_df["person_id"].isin(train_ids)].copy()

    tmp = duckdb.connect()
    try:
        tmp.register("charts", charts_df)
        tmp.register("events_with_dasha", ev_df)
        return dwp.calibrate_factors(tmp, event_class, level)
    finally:
        tmp.close()


@dataclass(frozen=True)
class BacktestResult:
    event_class: str
    level: str
    n_test_deaths: int
    n_train_deaths: int
    composite_factor: dict
    bracket_factor: dict
    # mean per-death log-likelihood under each nested model (higher = better)
    loglik_m0: float
    loglik_m1: float
    loglik_m2: float
    delta_m1_m0: float        # bracket's added predictive value
    delta_m2_m1: float        # composite (lord-specific) added value — the headline
    z_m2_m1: float            # paired z on per-death (M2-M1)
    p_m2_m1: float
    # interpretable capture metrics (true window in model's top-decile of risk)
    top_decile_capture_m0: float
    top_decile_capture_m2: float
    # realized-risk lift: composite factor of the true window vs the person's
    # duration-weighted average composite factor (isolates the lord signal)
    composite_realized_lift: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def backtest(
    con: duckdb.DuckDBPyConnection,
    event_class: str = "death_cause_unspecified",
    level: str = "md",
    test_frac: float = 0.25,
    brackets=dwp.DEFAULT_BRACKETS,
) -> BacktestResult:
    # ---- split deaths by person -------------------------------------------------
    deaths = con.execute(
        f"""SELECT person_id, md_seq, ad_seq
            FROM events_with_dasha
            WHERE event_class = '{dv._q(event_class)}'
              AND md_seq IS NOT NULL AND ad_seq IS NOT NULL"""
    ).fetchall()
    true_win = {pid: (int(ms), int(as_)) for pid, ms, as_ in deaths}
    test_ids = {pid for pid in true_win if _in_test(pid, test_frac)}
    train_ids = {pid for pid in true_win if pid not in test_ids}

    composite_factor, bracket_factor = _calibrate_on_train(con, train_ids, event_class, level)
    logger.info("Calibrated on %d train deaths: composite=%s bracket=%s",
                len(train_ids), composite_factor, bracket_factor)

    # ---- pull every window + chart for the test persons -------------------------
    house_cols = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in dv._MARAKA_GRAHAS)
    lord_col = "w.md_lord" if level == "md" else "w.ad_lord"
    rows = con.execute(
        f"""SELECT w.person_id, w.md_seq, w.ad_seq, {lord_col} AS lord,
                   w.duration_days, w.start_jd, w.end_jd,
                   c.asc_sign, c.asc_lon, c.birth_jd_used AS birth_jd, {house_cols}
            FROM dasha_windows w JOIN charts c USING(person_id)
            WHERE w.person_id IN (SELECT UNNEST(?))
              AND c.asc_sign IS NOT NULL AND c.asc_lon IS NOT NULL""",
        [list(test_ids)],
    ).fetchall()

    # group windows by person
    per: dict[str, list[dict]] = {}
    chart_of: dict[str, tuple[int, float, dict[str, int]]] = {}
    for r in rows:
        pid, ms, as_, lord, dur, sjd, ejd, asc, alon, bjd, *houses = r
        if pid not in chart_of:
            gh = {g: (int(h) if h is not None else 0)
                  for g, h in zip(dv._MARAKA_GRAHAS, houses)}
            chart_of[pid] = (int(asc), float(alon), gh)
        mid_age = (((float(sjd) + float(ejd)) / 2.0) - float(bjd)) / _DAYS_PER_YEAR
        per.setdefault(pid, []).append({
            "md_seq": int(ms), "ad_seq": int(as_), "lord": lord,
            "dur": float(dur), "mid_age": mid_age,
        })

    sig = dwp._DEATH_COMPOSITE
    score_cache: dict[tuple[str, str], int] = {}

    def md_score(pid: str, lord: str) -> int:
        key = (pid, lord)
        if key not in score_cache:
            asc, alon, gh = chart_of[pid]
            score_cache[key] = _role_count(lord, asc, alon, gh, sig)[0]
        return score_cache[key]

    # ---- evaluate each test death ----------------------------------------------
    ll0 = ll1 = ll2 = 0.0
    deltas21: list[float] = []
    cap0 = cap2 = 0
    real_lift_num = real_lift_den = 0
    n = 0

    for pid, wins in per.items():
        if pid not in true_win:
            continue
        tms, tas = true_win[pid]
        # weights under each model
        w0, w1, w2 = [], [], []
        comp_facs = []
        true_i = None
        for i, w in enumerate(wins):
            br = _bracket_for_age(w["mid_age"], brackets)
            bf = bracket_factor.get(br, 1.0)
            cf = composite_factor.get(md_score(pid, w["lord"]), 1.0)
            comp_facs.append(cf)
            w0.append(w["dur"])
            w1.append(w["dur"] * bf)
            w2.append(w["dur"] * bf * cf)
            if w["md_seq"] == tms and w["ad_seq"] == tas:
                true_i = i
        if true_i is None:
            continue
        s0, s1, s2 = sum(w0), sum(w1), sum(w2)
        if s0 <= 0 or s1 <= 0 or s2 <= 0:
            continue
        p0, p1, p2 = w0[true_i] / s0, w1[true_i] / s1, w2[true_i] / s2
        ll0 += math.log(p0); ll1 += math.log(p1); ll2 += math.log(p2)
        deltas21.append(math.log(p2) - math.log(p1))

        # top-decile capture: true window among the model's riskiest 10% by weight
        k = max(1, int(round(0.10 * len(wins))))
        if true_i in sorted(range(len(wins)), key=lambda j: w0[j], reverse=True)[:k]:
            cap0 += 1
        if true_i in sorted(range(len(wins)), key=lambda j: w2[j], reverse=True)[:k]:
            cap2 += 1

        # composite realized lift: true window's composite factor vs the person's
        # duration-weighted average composite factor (age/duration cancel out)
        dw_mean_cf = sum(comp_facs[j] * w0[j] for j in range(len(wins))) / s0
        if dw_mean_cf > 0:
            real_lift_num += comp_facs[true_i] / dw_mean_cf
            real_lift_den += 1
        n += 1

    mu = sum(deltas21) / len(deltas21) if deltas21 else 0.0
    var = (sum((d - mu) ** 2 for d in deltas21) / len(deltas21)) if deltas21 else 0.0
    se = math.sqrt(var / len(deltas21)) if deltas21 and var > 0 else 0.0
    z = mu / se if se else 0.0
    p = 2.0 * dv._norm_sf(abs(z))

    return BacktestResult(
        event_class=event_class, level=level,
        n_test_deaths=n, n_train_deaths=len(train_ids),
        composite_factor={int(k): round(v, 4) for k, v in composite_factor.items()},
        bracket_factor={k: round(v, 4) for k, v in bracket_factor.items()},
        loglik_m0=round(ll0 / n, 4) if n else 0.0,
        loglik_m1=round(ll1 / n, 4) if n else 0.0,
        loglik_m2=round(ll2 / n, 4) if n else 0.0,
        delta_m1_m0=round((ll1 - ll0) / n, 5) if n else 0.0,
        delta_m2_m1=round((ll2 - ll1) / n, 5) if n else 0.0,
        z_m2_m1=round(z, 3), p_m2_m1=round(p, 6),
        top_decile_capture_m0=round(cap0 / n, 4) if n else 0.0,
        top_decile_capture_m2=round(cap2 / n, 4) if n else 0.0,
        composite_realized_lift=round(real_lift_num / real_lift_den, 4) if real_lift_den else 0.0,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-class", default="death_cause_unspecified")
    parser.add_argument("--level", default="md", choices=["md", "ad"])
    parser.add_argument("--test-frac", type=float, default=0.25)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s | %(message)s")

    con = dv.open_catalog()
    try:
        res = backtest(con, args.event_class, args.level, args.test_frac)
    finally:
        con.close()

    d = res.to_dict()
    print("\n=== Death-window predictor backtest ===")
    print(f"test deaths: {d['n_test_deaths']}  |  train deaths: {d['n_train_deaths']}")
    print(f"composite factor: {d['composite_factor']}")
    print(f"bracket factor:   {d['bracket_factor']}")
    print(f"\nmean per-death log-likelihood (higher = better):")
    print(f"  M0 duration-only          : {d['loglik_m0']}")
    print(f"  M1 + longevity bracket     : {d['loglik_m1']}   (Δ {d['delta_m1_m0']:+})")
    print(f"  M2 + composite confluence  : {d['loglik_m2']}   (Δ {d['delta_m2_m1']:+})")
    print(f"\nHEADLINE M1→M2 (does the running lord add signal beyond age+duration?):")
    print(f"  per-death Δ logLik = {d['delta_m2_m1']:+}  z={d['z_m2_m1']}  p={d['p_m2_m1']}")
    print(f"  composite realized lift = {d['composite_realized_lift']} "
          f"(true death window's confluence vs duration-weighted average)")
    print(f"\ntop-decile capture (true window in model's riskiest 10%):")
    print(f"  M0 duration-only: {d['top_decile_capture_m0']}   "
          f"M2 full: {d['top_decile_capture_m2']}   (null ≈ 0.10)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
