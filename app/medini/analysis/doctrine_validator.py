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

DEFAULT_CATALOG = Path("app/medini/data/catalog.duckdb")

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


def validate_yoga(con: duckdb.DuckDBPyConnection, yoga: str, outcome: str) -> DoctrineResult:
    member = f"SELECT person_id FROM chart_yogas WHERE yoga = '{yoga.replace(chr(39), '')}'"
    return _evaluate(con, f"yoga:{yoga}", member, outcome)


def validate_attribute(con: duckdb.DuckDBPyConnection, root: str, field: str,
                       outcome: str) -> DoctrineResult:
    safe = lambda s: s.replace("'", "")  # noqa: E731 — tiny inline sanitizer
    member = (f"SELECT person_id FROM person_attributes "
              f"WHERE root = '{safe(root)}' AND field = '{safe(field)}'")
    return _evaluate(con, f"attr:{root}:{field}", member, outcome)


def validate_strong_graha(con: duckdb.DuckDBPyConnection, graha: str,
                          outcome: str) -> DoctrineResult:
    """Condition = this graha is the strongest (Shadbala rank 1) in the chart."""
    member = (f"SELECT person_id FROM graha_strength "
              f"WHERE graha = '{graha.replace(chr(39), '')}' AND rank = 1")
    return _evaluate(con, f"strongest:{graha}", member, outcome)


def scan_yogas(con: duckdb.DuckDBPyConnection, outcome: str) -> list[DoctrineResult]:
    """Validate every yoga against one outcome, sorted by lift descending."""
    yogas = [r[0] for r in con.execute(
        "SELECT DISTINCT yoga FROM chart_yogas ORDER BY 1").fetchall()]
    out = [validate_yoga(con, y, outcome) for y in yogas]
    out.sort(key=lambda r: r.lift, reverse=True)
    return out


def open_catalog(catalog: Path = DEFAULT_CATALOG) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(catalog), read_only=True)
