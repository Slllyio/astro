"""Doctrine Validator — measure whether a classical rule holds at population scale.

Given a CONDITION over the canonical store (a yoga, a structured attribute, or a
strong/weak graha) and a binary OUTCOME (a ``person_labels`` flag), it computes the
outcome rate in the condition cohort vs the baseline, the lift, and a two-proportion
z-test p-value. This is the empirical core of the "validated Jyotiṣa" product:

    "Do people with Gajakesari become famous more often than baseline?"
        -> rate 0.150 vs 0.149, lift 1.01, p 0.82  (no, not at population scale)
    "Does Malavya (Venus PMP) associate with fame?"
        -> rate 0.159 vs 0.149, lift 1.07, p 0.03  (a small, real effect)

Pure-Python statistics (no scipy dependency). All queries run against the DuckDB
catalog so they're zero-copy over the Silver parquets.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import duckdb

from app.core.ephemeris_engine import DASHA_LORDS
from app.core.yogas import SIGN_RULERS

DEFAULT_CATALOG = Path("app/medini/data/catalog.duckdb")

# Natural Vimshottari share of an ideal 120-year life per lord — the baseline a
# dasha-timing test compares against ("does death cluster under a lord *more*
# than that lord simply owns of life?").
_TOTAL_DASHA_YEARS = sum(yrs for _, yrs in DASHA_LORDS)
LORD_SHARE: dict[str, float] = {lord: yrs / _TOTAL_DASHA_YEARS for lord, yrs in DASHA_LORDS}

# Outcome flags available in person_labels (boolean columns).
OUTCOMES: tuple[str, ...] = (
    "is_famous", "has_award", "has_major_disease",
    "has_psychological_dx", "has_marriage", "financial_gain",
)


@dataclass(frozen=True)
class DoctrineResult:
    condition: str
    outcome: str
    n_population: int
    n_condition: int
    n_condition_outcome: int
    condition_rate: float
    baseline_rate: float
    lift: float
    z: float
    p_value: float
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm_sf(x: float) -> float:
    """Upper-tail of the standard normal (1 - CDF), via erfc."""
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def _two_proportion_z(k1: int, n1: int, k0: int, n0: int) -> tuple[float, float]:
    """Two-sided two-proportion z-test (cohort vs the rest). Returns (z, p)."""
    if n1 == 0 or n0 == 0:
        return 0.0, 1.0
    p1, p0 = k1 / n1, k0 / n0
    p_pool = (k1 + k0) / (n1 + n0)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n0))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p0) / se
    p = 2.0 * _norm_sf(abs(z))
    return z, p


def _verdict(lift: float, p: float, n_condition: int) -> str:
    if n_condition < 30:
        return "insufficient-n"
    if p >= 0.05:
        return "no-effect"
    return "supports" if lift > 1.0 else "contradicts"


def _evaluate(con: duckdb.DuckDBPyConnection, condition_label: str,
              member_sql: str, outcome: str) -> DoctrineResult:
    """member_sql must SELECT person_id of the condition cohort."""
    if outcome not in OUTCOMES:
        raise ValueError(f"unknown outcome {outcome!r}; choose from {OUTCOMES}")
    # Whole labeled population is the universe.
    n_pop, k_pop = con.execute(
        f"SELECT COUNT(*), COALESCE(SUM(CASE WHEN {outcome} THEN 1 ELSE 0 END),0) "
        f"FROM person_labels"
    ).fetchone()
    n_cond, k_cond = con.execute(
        f"""SELECT COUNT(*), COALESCE(SUM(CASE WHEN l.{outcome} THEN 1 ELSE 0 END),0)
            FROM person_labels l
            WHERE l.person_id IN ({member_sql})"""
    ).fetchone()
    n_cond, k_cond = int(n_cond), int(k_cond)
    n_rest, k_rest = n_pop - n_cond, k_pop - k_cond
    cond_rate = (k_cond / n_cond) if n_cond else 0.0
    base_rate = (k_pop / n_pop) if n_pop else 0.0
    lift = (cond_rate / base_rate) if base_rate else 0.0
    z, p = _two_proportion_z(k_cond, n_cond, k_rest, n_rest)
    return DoctrineResult(
        condition=condition_label, outcome=outcome,
        n_population=int(n_pop), n_condition=n_cond, n_condition_outcome=k_cond,
        condition_rate=round(cond_rate, 4), baseline_rate=round(base_rate, 4),
        lift=round(lift, 3), z=round(z, 3), p_value=round(p, 5),
        verdict=_verdict(lift, p, n_cond),
    )


def _q(s: str) -> str:
    """Strip single quotes — tiny inline sanitizer for interpolated literals."""
    return s.replace("'", "")


def _yoga_member(yoga: str) -> str:
    return f"SELECT person_id FROM chart_yogas WHERE yoga = '{_q(yoga)}'"


def _attr_member(root: str, field: str) -> str:
    return (f"SELECT person_id FROM person_attributes "
            f"WHERE root = '{_q(root)}' AND field = '{_q(field)}'")


def _strong_member(graha: str) -> str:
    return (f"SELECT person_id FROM graha_strength "
            f"WHERE graha = '{_q(graha)}' AND rank = 1")


def validate_yoga(con: duckdb.DuckDBPyConnection, yoga: str, outcome: str) -> DoctrineResult:
    return _evaluate(con, f"yoga:{yoga}", _yoga_member(yoga), outcome)


def validate_attribute(con: duckdb.DuckDBPyConnection, root: str, field: str,
                       outcome: str) -> DoctrineResult:
    return _evaluate(con, f"attr:{root}:{field}", _attr_member(root, field), outcome)


def validate_strong_graha(con: duckdb.DuckDBPyConnection, graha: str,
                          outcome: str) -> DoctrineResult:
    """Condition = this graha is the strongest (Shadbala rank 1) in the chart."""
    return _evaluate(con, f"strongest:{graha}", _strong_member(graha), outcome)


# --------------------------------------------------------------------------- #
# Event / timing outcomes (over events_with_dasha)                            #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class DashaTimingResult:
    event_class: str
    level: str            # "md" or "ad"
    lord: str
    n_events: int
    n_lord: int
    observed_share: float
    expected_share: float   # natural Vimshottari share of life
    lift: float
    z: float
    p_value: float
    verdict: str


def validate_dasha_timing(con: duckdb.DuckDBPyConnection, event_class: str,
                          level: str = "md") -> list[DashaTimingResult]:
    """Does an event class cluster under particular dasha lords?

    Compares the observed lord-at-event distribution to each lord's natural
    Vimshottari share of life (a lord that owns 1/6 of life should, by chance,
    be running at ~1/6 of events). A binomial z-test flags real deviations.
    """
    col = {"md": "md_lord_at_event", "ad": "ad_lord_at_event"}.get(level)
    if col is None:
        raise ValueError("level must be 'md' or 'ad'")
    rows = con.execute(
        f"""SELECT {col} AS lord, COUNT(*) n
            FROM events_with_dasha
            WHERE event_class = '{_q(event_class)}' AND {col} IS NOT NULL
            GROUP BY 1"""
    ).fetchall()
    counts = {lord: int(n) for lord, n in rows}
    n_total = sum(counts.values())
    out: list[DashaTimingResult] = []
    for lord, exp_share in LORD_SHARE.items():
        k = counts.get(lord, 0)
        obs = k / n_total if n_total else 0.0
        lift = obs / exp_share if exp_share else 0.0
        # Binomial z-test: observed k vs expected n*p.
        if n_total:
            se = math.sqrt(n_total * exp_share * (1 - exp_share))
            z = (k - n_total * exp_share) / se if se else 0.0
        else:
            z = 0.0
        p = 2.0 * _norm_sf(abs(z))
        out.append(DashaTimingResult(
            event_class=event_class, level=level, lord=lord,
            n_events=n_total, n_lord=k,
            observed_share=round(obs, 4), expected_share=round(exp_share, 4),
            lift=round(lift, 3), z=round(z, 3), p_value=round(p, 5),
            verdict=_verdict(lift, p, k),
        ))
    out.sort(key=lambda r: r.lift, reverse=True)
    return out


@dataclass(frozen=True)
class AgeShiftResult:
    condition: str
    event_class: str
    n_cohort: int
    n_rest: int
    mean_age_cohort: float
    mean_age_rest: float
    diff_years: float
    z: float
    p_value: float
    verdict: str


def _age_shift(con: duckdb.DuckDBPyConnection, condition_label: str,
               member_sql: str, event_class: str) -> AgeShiftResult:
    """Welch two-sample test (normal approx; large-n) on age-at-event for the
    condition cohort vs the rest, within one event class."""
    def stats(in_cohort: bool) -> tuple[int, float, float]:
        op = "IN" if in_cohort else "NOT IN"
        r = con.execute(
            f"""SELECT COUNT(*), AVG(age_at_event_years), VAR_SAMP(age_at_event_years)
                FROM events_with_dasha
                WHERE event_class = '{_q(event_class)}'
                  AND age_at_event_years IS NOT NULL
                  AND person_id {op} ({member_sql})"""
        ).fetchone()
        return int(r[0]), float(r[1] or 0.0), float(r[2] or 0.0)

    n1, m1, v1 = stats(True)
    n0, m0, v0 = stats(False)
    diff = m1 - m0
    se = math.sqrt((v1 / n1 if n1 else 0) + (v0 / n0 if n0 else 0))
    z = diff / se if se else 0.0
    p = 2.0 * _norm_sf(abs(z))
    verdict = ("insufficient-n" if min(n1, n0) < 30
               else "no-effect" if p >= 0.05
               else "later" if diff > 0 else "earlier")
    return AgeShiftResult(
        condition=condition_label, event_class=event_class,
        n_cohort=n1, n_rest=n0,
        mean_age_cohort=round(m1, 2), mean_age_rest=round(m0, 2),
        diff_years=round(diff, 2), z=round(z, 3), p_value=round(p, 5),
        verdict=verdict,
    )


def validate_age_shift(con: duckdb.DuckDBPyConnection, event_class: str, *,
                       yoga: str | None = None, attr: tuple[str, str] | None = None,
                       strong_graha: str | None = None) -> AgeShiftResult:
    """Does a chart condition shift the age at which an event class strikes?"""
    if yoga:
        return _age_shift(con, f"yoga:{yoga}", _yoga_member(yoga), event_class)
    if attr:
        return _age_shift(con, f"attr:{attr[0]}:{attr[1]}", _attr_member(*attr), event_class)
    if strong_graha:
        return _age_shift(con, f"strongest:{strong_graha}", _strong_member(strong_graha), event_class)
    raise ValueError("provide one condition: yoga, attr=(root,field), or strong_graha")


def scan_yogas(con: duckdb.DuckDBPyConnection, outcome: str) -> list[DoctrineResult]:
    """Validate every yoga against one outcome, sorted by lift descending."""
    yogas = [r[0] for r in con.execute(
        "SELECT DISTINCT yoga FROM chart_yogas ORDER BY 1").fetchall()]
    out = [validate_yoga(con, y, outcome) for y in yogas]
    out.sort(key=lambda r: r.lift, reverse=True)
    return out


# --------------------------------------------------------------------------- #
# Maraka — ascendant-specific death-timing doctrine                           #
# --------------------------------------------------------------------------- #

def _house_lord(asc_sign: int, house: int) -> str:
    """Ruler of the sign occupying `house` counted from `asc_sign` (whole-sign)."""
    return SIGN_RULERS[((asc_sign - 1 + house - 1) % 12) + 1]


def _marakas(asc_sign: int) -> set[str]:
    """Primary marakas for an ascendant: the 2nd and 7th house lords."""
    return {_house_lord(asc_sign, 2), _house_lord(asc_sign, 7)}


@dataclass(frozen=True)
class MarakaResult:
    event_class: str
    level: str
    n_events: int
    n_maraka: int
    observed_rate: float
    expected_rate: float   # dasha-length-weighted, per-ascendant baseline
    lift: float
    z: float
    p_value: float
    verdict: str
    by_ascendant: list[dict]


def validate_maraka(con: duckdb.DuckDBPyConnection, event_class: str = "death_cause_unspecified",
                    level: str = "md") -> MarakaResult:
    """Test the maraka doctrine: do deaths run under the 2nd/7th-lord dasha more
    than chance, accounting for each ascendant's marakas AND their dasha lengths?

    The baseline is the per-person dasha-length share of that person's own
    marakas (so a Libra native whose maraka is short-dasha Mars has a low
    expected rate, a Leo native whose maraka is long-dasha Saturn a high one).
    """
    col = {"md": "md_lord_at_event", "ad": "ad_lord_at_event"}.get(level)
    if col is None:
        raise ValueError("level must be 'md' or 'ad'")
    rows = con.execute(
        f"""SELECT e.{col} AS lord, c.asc_sign
            FROM events_with_dasha e JOIN charts c USING(person_id)
            WHERE e.event_class = '{_q(event_class)}'
              AND e.{col} IS NOT NULL AND c.asc_sign IS NOT NULL"""
    ).fetchall()

    n = len(rows)
    k = 0
    exp_sum = 0.0
    # per-ascendant tallies
    per: dict[int, dict] = {}
    for lord, asc in rows:
        asc = int(asc)
        mar = _marakas(asc)
        is_mar = lord in mar
        k += is_mar
        exp_sum += sum(LORD_SHARE[m] for m in mar)
        b = per.setdefault(asc, {"asc_sign": asc, "second_lord": _house_lord(asc, 2),
                                 "seventh_lord": _house_lord(asc, 7), "n": 0, "n_maraka": 0})
        b["n"] += 1
        b["n_maraka"] += is_mar

    exp_rate = (exp_sum / n) if n else 0.0
    obs_rate = (k / n) if n else 0.0
    lift = (obs_rate / exp_rate) if exp_rate else 0.0
    se = math.sqrt(n * exp_rate * (1 - exp_rate)) if n else 0.0
    z = (k - n * exp_rate) / se if se else 0.0
    p = 2.0 * _norm_sf(abs(z))

    by_asc = []
    for asc in sorted(per):
        b = per[asc]
        by_asc.append({**b, "maraka_rate": round(b["n_maraka"] / b["n"], 4) if b["n"] else 0.0})

    return MarakaResult(
        event_class=event_class, level=level, n_events=n, n_maraka=k,
        observed_rate=round(obs_rate, 4), expected_rate=round(exp_rate, 4),
        lift=round(lift, 3), z=round(z, 3), p_value=round(p, 6),
        verdict=_verdict(lift, p, k), by_ascendant=by_asc,
    )


def open_catalog(catalog: Path = DEFAULT_CATALOG) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(catalog), read_only=True)
