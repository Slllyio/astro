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
from typing import Any, Callable

import duckdb

from app.core.ephemeris_engine import DASHA_LORDS
from app.core.shodashavarga import compute_divisional_longitude
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


_MARAKA_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_MARAKA_DEFS = ("lords", "lords_occupants", "full")


def _maraka_set(asc_sign: int, graha_houses: dict[str, int], definition: str) -> set[str]:
    """Maraka planets for a chart under a given doctrine definition.

    - "lords": the 2nd and 7th house lords (primary marakas).
    - "lords_occupants": + planets posited in the 2nd or 7th house.
    - "full": + Saturn (the natural maraka). Empirically the strongest.
    """
    m = {_house_lord(asc_sign, 2), _house_lord(asc_sign, 7)}
    if definition in ("lords_occupants", "full"):
        m |= {g for g, h in graha_houses.items() if h in (2, 7)}
    if definition == "full":
        m.add("Saturn")
    return m


@dataclass(frozen=True)
class MarakaResult:
    event_class: str
    level: str
    definition: str
    n_events: int
    n_maraka: int
    observed_rate: float
    expected_rate: float   # dasha-length-weighted, per-ascendant baseline
    lift: float
    z: float
    p_value: float
    verdict: str
    # MD-and-AD both-maraka confluence (vs an independence baseline)
    confluence_rate: float
    confluence_expected: float
    confluence_lift: float
    confluence_p: float
    by_ascendant: list[dict]


def validate_maraka(con: duckdb.DuckDBPyConnection, event_class: str = "death_cause_unspecified",
                    level: str = "md", definition: str = "full") -> MarakaResult:
    """Test the maraka doctrine: do deaths run under a maraka-planet dasha more
    than chance, accounting for each ascendant's marakas AND their dasha lengths?

    The baseline is the per-person dasha-length share of that person's own maraka
    set (so a Libra native whose maraka is short-dasha Mars has a low expected
    rate, a Leo native whose maraka is long-dasha Saturn a high one). ``definition``
    selects how broadly marakas are defined; ``full`` (lords + 2/7 occupants +
    Saturn) is empirically the most predictive. Also reports MD&AD confluence.
    """
    col = {"md": "md_lord_at_event", "ad": "ad_lord_at_event"}.get(level)
    if col is None:
        raise ValueError("level must be 'md' or 'ad'")
    if definition not in _MARAKA_DEFS:
        raise ValueError(f"definition must be one of {_MARAKA_DEFS}")

    house_cols = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    rows = con.execute(
        f"""SELECT e.{col} AS lord, e.md_lord_at_event AS md, e.ad_lord_at_event AS ad,
                   c.asc_sign, {house_cols}
            FROM events_with_dasha e JOIN charts c USING(person_id)
            WHERE e.event_class = '{_q(event_class)}'
              AND e.{col} IS NOT NULL AND c.asc_sign IS NOT NULL"""
    ).fetchall()

    n = k = k_conf = 0
    exp_sum = exp_conf = 0.0
    per: dict[int, dict] = {}
    for lord, md, ad, asc, *houses in rows:
        asc = int(asc)
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        mset = _maraka_set(asc, gh, definition)
        share = sum(LORD_SHARE[m] for m in mset)
        n += 1
        is_mar = lord in mset
        k += is_mar
        exp_sum += share
        if md in mset and ad in mset:
            k_conf += 1
        exp_conf += share * share  # independence baseline for both-maraka
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

    conf_obs = (k_conf / n) if n else 0.0
    conf_exp = (exp_conf / n) if n else 0.0
    conf_lift = (conf_obs / conf_exp) if conf_exp else 0.0
    conf_se = math.sqrt(n * conf_exp * (1 - conf_exp)) if n else 0.0
    conf_p = 2.0 * _norm_sf(abs((k_conf - n * conf_exp) / conf_se)) if conf_se else 1.0

    by_asc = [
        {**per[a], "maraka_rate": round(per[a]["n_maraka"] / per[a]["n"], 4)}
        for a in sorted(per)
    ]
    return MarakaResult(
        event_class=event_class, level=level, definition=definition,
        n_events=n, n_maraka=k, observed_rate=round(obs_rate, 4),
        expected_rate=round(exp_rate, 4), lift=round(lift, 3), z=round(z, 3),
        p_value=round(p, 6), verdict=_verdict(lift, p, k),
        confluence_rate=round(conf_obs, 4), confluence_expected=round(conf_exp, 4),
        confluence_lift=round(conf_lift, 3), confluence_p=round(conf_p, 6),
        by_ascendant=by_asc,
    )


# --------------------------------------------------------------------------- #
# Death significators — classical death-timing lords, tested head-to-head      #
# --------------------------------------------------------------------------- #

_MOVABLE = {1, 4, 7, 10}
_FIXED = {2, 5, 8, 11}


def _badhaka_house(asc_sign: int) -> int:
    """Badhaka house: 11th for movable, 9th for fixed, 7th for dual signs."""
    return 11 if asc_sign in _MOVABLE else (9 if asc_sign in _FIXED else 7)


def _div_sign_lord(longitude: float, divisor: int) -> str:
    """Ruler of the divisional (D-`divisor`) sign at a longitude."""
    dl = compute_divisional_longitude(longitude % 360.0, divisor)
    return SIGN_RULERS[int(dl // 30) + 1]


# Each significator maps a chart -> the set of planets that "time" the event by
# classical doctrine. asc_lon drives the 210°-from-Lagna points (22nd drekkana,
# 64th navamsa); graha_houses feeds maraka occupants.
_SIGNIFICATORS: dict[str, "Callable"] = {
    "maraka_full": lambda asc, lon, gh: _maraka_set(asc, gh, "full"),
    "maraka_lords": lambda asc, lon, gh: _maraka_set(asc, gh, "lords"),
    "eighth_lord": lambda asc, lon, gh: {_house_lord(asc, 8)},
    "third_lord": lambda asc, lon, gh: {_house_lord(asc, 3)},
    "badhakesa": lambda asc, lon, gh: {_house_lord(asc, _badhaka_house(asc))},
    "drekkana_22": lambda asc, lon, gh: {_div_sign_lord(lon + 210.0, 3)},
    "navamsa_64": lambda asc, lon, gh: {_div_sign_lord(lon + 210.0, 9)},
    # maraka counted from the Sun sign (2nd/7th-from-Sun lords + Saturn). Doctrine-
    # mined: individually a STRONGER death significator than the Lagna maraka
    # (lift 1.058 vs 1.035, p≈0 on 37k deaths), though correlated so it doesn't lift
    # the composite ceiling. sun_sign = whole-sign from Lagna + Sun's house.
    "maraka_from_sun": lambda asc, lon, gh: {
        _house_lord(((asc - 1) + (gh.get("Sun", 1) - 1)) % 12 + 1, 2),
        _house_lord(((asc - 1) + (gh.get("Sun", 1) - 1)) % 12 + 1, 7), "Saturn"},
    # Marriage / relationship significators
    "seventh_lord": lambda asc, lon, gh: {_house_lord(asc, 7)},
    "second_lord": lambda asc, lon, gh: {_house_lord(asc, 2)},
    "venus_karaka": lambda asc, lon, gh: {"Venus"},      # kalatra (spouse) karaka
    "jupiter_karaka": lambda asc, lon, gh: {"Jupiter"},  # saubhagya / husband karaka
    # Career significators
    "tenth_lord": lambda asc, lon, gh: {_house_lord(asc, 10)},
    "saturn_karaka": lambda asc, lon, gh: {"Saturn"},    # karma karaka
    "sun_karaka": lambda asc, lon, gh: {"Sun"},          # authority / status
    "mercury_karaka": lambda asc, lon, gh: {"Mercury"},  # commerce / skill
}

# Per-event-class composite significator panels — the classical "who times this
# event" sets, tested head-to-head and as a confluence. Death is the validated
# flagship; marriage & career are the karaka-driven analogues.
EVENT_SIGNIFICATORS: dict[str, tuple[str, ...]] = {
    "death_cause_unspecified": ("maraka_full", "third_lord", "navamsa_64"),
    "relationships": ("seventh_lord", "venus_karaka", "jupiter_karaka"),
    "career": ("tenth_lord", "saturn_karaka", "jupiter_karaka"),
}


@dataclass(frozen=True)
class SignificatorResult:
    significator: str
    event_class: str
    level: str
    n_events: int
    n_hit: int
    observed_rate: float
    expected_rate: float
    lift: float
    z: float
    p_value: float
    verdict: str


def death_significators_report(
    con: duckdb.DuckDBPyConnection,
    event_class: str = "death_cause_unspecified",
    level: str = "md",
    significators: tuple[str, ...] | None = None,
) -> list[SignificatorResult]:
    """Test every classical death-timing significator head-to-head.

    For each, computes how often the active dasha lord is that significator vs a
    per-person dasha-length-weighted baseline (so longer-dasha significators are
    not unfairly credited). Returns results sorted by lift descending.
    """
    col = {"md": "md_lord_at_event", "ad": "ad_lord_at_event"}.get(level)
    if col is None:
        raise ValueError("level must be 'md' or 'ad'")
    names = significators or tuple(_SIGNIFICATORS)
    bad = [s for s in names if s not in _SIGNIFICATORS]
    if bad:
        raise ValueError(f"unknown significator(s): {bad}; choose from {tuple(_SIGNIFICATORS)}")

    house_cols = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    rows = con.execute(
        f"""SELECT e.{col} AS lord, c.asc_sign, c.asc_lon, {house_cols}
            FROM events_with_dasha e JOIN charts c USING(person_id)
            WHERE e.event_class = '{_q(event_class)}'
              AND e.{col} IS NOT NULL AND c.asc_sign IS NOT NULL AND c.asc_lon IS NOT NULL"""
    ).fetchall()

    acc = {s: {"n": 0, "k": 0, "exp": 0.0} for s in names}
    for lord, asc, lon, *houses in rows:
        asc, lon = int(asc), float(lon)
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        for s in names:
            sset = _SIGNIFICATORS[s](asc, lon, gh)
            if not sset:
                continue
            a = acc[s]
            a["n"] += 1
            a["k"] += lord in sset
            a["exp"] += sum(LORD_SHARE[p] for p in sset)

    out: list[SignificatorResult] = []
    for s in names:
        a = acc[s]
        n, k = a["n"], a["k"]
        exp_rate = (a["exp"] / n) if n else 0.0
        obs = (k / n) if n else 0.0
        lift = (obs / exp_rate) if exp_rate else 0.0
        se = math.sqrt(n * exp_rate * (1 - exp_rate)) if n else 0.0
        z = (k - n * exp_rate) / se if se else 0.0
        p = 2.0 * _norm_sf(abs(z))
        out.append(SignificatorResult(
            significator=s, event_class=event_class, level=level,
            n_events=n, n_hit=k, observed_rate=round(obs, 4),
            expected_rate=round(exp_rate, 4), lift=round(lift, 3),
            z=round(z, 3), p_value=round(p, 6), verdict=_verdict(lift, p, k),
        ))
    out.sort(key=lambda r: r.lift, reverse=True)
    return out


# --------------------------------------------------------------------------- #
# Composite death-risk score (confluence / dose-response)                     #
# --------------------------------------------------------------------------- #

_DEATH_COMPOSITE = ("maraka_full", "third_lord", "navamsa_64")


@dataclass(frozen=True)
class CompositeResult:
    event_class: str
    level: str
    significators: list[str]
    n_events: int
    thresholds: list[dict]   # one per k: {k, observed, expected, lift, z, p_value, verdict}


def validate_composite_death_score(
    con: duckdb.DuckDBPyConnection,
    event_class: str = "death_cause_unspecified",
    level: str = "md",
    significators: tuple[str, ...] = _DEATH_COMPOSITE,
) -> CompositeResult:
    """Confluence test: does the dasha lord playing MORE death-significator roles
    raise the risk (a dose-response)? For each event the active lord's score is the
    number of `significators` whose set it belongs to; we test P(score>=k) at the
    event vs the dasha-length-weighted baseline P(a random lord has score>=k)."""
    col = {"md": "md_lord_at_event", "ad": "ad_lord_at_event"}.get(level)
    if col is None:
        raise ValueError("level must be 'md' or 'ad'")
    bad = [s for s in significators if s not in _SIGNIFICATORS]
    if bad:
        raise ValueError(f"unknown significator(s): {bad}")

    house_cols = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    rows = con.execute(
        f"""SELECT e.{col} AS lord, c.asc_sign, c.asc_lon, {house_cols}
            FROM events_with_dasha e JOIN charts c USING(person_id)
            WHERE e.event_class = '{_q(event_class)}'
              AND e.{col} IS NOT NULL AND c.asc_sign IS NOT NULL AND c.asc_lon IS NOT NULL"""
    ).fetchall()

    nsig = len(significators)
    obs = [0] * (nsig + 1)
    exp = [0.0] * (nsig + 1)
    all_lords = [lord for lord, _ in DASHA_LORDS]
    for lord, asc, lon, *houses in rows:
        asc, lon = int(asc), float(lon)
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        sets = [_SIGNIFICATORS[s](asc, lon, gh) for s in significators]
        obs[sum(lord in S for S in sets)] += 1
        for L in all_lords:
            exp[sum(L in S for S in sets)] += LORD_SHARE[L]

    n = len(rows)
    thresholds = []
    for k in range(1, nsig + 1):
        ok = sum(obs[k:])
        ek = sum(exp[k:]) / n if n else 0.0
        obs_p = ok / n if n else 0.0
        lift = obs_p / ek if ek else 0.0
        se = math.sqrt(n * ek * (1 - ek)) if (n and 0 < ek < 1) else 0.0
        z = (ok - n * ek) / se if se else 0.0
        p = 2.0 * _norm_sf(abs(z))
        thresholds.append({
            "k": k, "observed": round(obs_p, 4), "expected": round(ek, 4),
            "lift": round(lift, 3), "z": round(z, 3), "p_value": round(p, 6),
            "verdict": _verdict(lift, p, ok),
        })
    return CompositeResult(event_class=event_class, level=level,
                           significators=list(significators), n_events=n,
                           thresholds=thresholds)


# --------------------------------------------------------------------------- #
# Longevity bracket (ayurdaya) — do significators fire in a specific window?   #
# --------------------------------------------------------------------------- #

DEFAULT_BRACKETS: tuple[tuple[str, float, float], ...] = (
    ("alpa", 0.0, 32.0), ("madhya", 32.0, 70.0), ("purna", 70.0, 200.0),
)


@dataclass(frozen=True)
class BracketResult:
    significator: str
    event_class: str
    level: str
    brackets: list[dict]   # {name, lo, hi, n, observed, expected, lift, z, p_value, verdict}


def validate_significator_by_bracket(
    con: duckdb.DuckDBPyConnection,
    significator: str = "maraka_full",
    event_class: str = "death_cause_unspecified",
    level: str = "md",
    brackets: tuple[tuple[str, float, float], ...] = DEFAULT_BRACKETS,
) -> BracketResult:
    """Does a significator's timing power concentrate in a longevity bracket?

    Splits events by age-at-event (alpa/madhya/purna by default) and computes the
    significator's lift within each, against the same dasha-weighted baseline.
    """
    col = {"md": "md_lord_at_event", "ad": "ad_lord_at_event"}.get(level)
    if col is None:
        raise ValueError("level must be 'md' or 'ad'")
    if significator not in _SIGNIFICATORS:
        raise ValueError(f"unknown significator {significator!r}")

    house_cols = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    rows = con.execute(
        f"""SELECT e.{col} AS lord, c.asc_sign, c.asc_lon, e.age_at_event_years AS age, {house_cols}
            FROM events_with_dasha e JOIN charts c USING(person_id)
            WHERE e.event_class = '{_q(event_class)}'
              AND e.{col} IS NOT NULL AND c.asc_sign IS NOT NULL AND c.asc_lon IS NOT NULL
              AND e.age_at_event_years IS NOT NULL"""
    ).fetchall()

    fn = _SIGNIFICATORS[significator]
    acc = {name: {"n": 0, "k": 0, "exp": 0.0} for name, _, _ in brackets}
    for lord, asc, lon, age, *houses in rows:
        age = float(age)
        bracket = next((name for name, lo, hi in brackets if lo <= age < hi), None)
        if bracket is None:
            continue
        asc, lon = int(asc), float(lon)
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        s = fn(asc, lon, gh)
        a = acc[bracket]
        a["n"] += 1
        a["k"] += lord in s
        a["exp"] += sum(LORD_SHARE[p] for p in s)

    out = []
    for name, lo, hi in brackets:
        a = acc[name]
        n, k = a["n"], a["k"]
        ek = a["exp"] / n if n else 0.0
        obs = k / n if n else 0.0
        lift = obs / ek if ek else 0.0
        se = math.sqrt(n * ek * (1 - ek)) if (n and 0 < ek < 1) else 0.0
        z = (k - n * ek) / se if se else 0.0
        p = 2.0 * _norm_sf(abs(z))
        out.append({
            "name": name, "lo": lo, "hi": hi, "n": n,
            "observed": round(obs, 4), "expected": round(ek, 4),
            "lift": round(lift, 3), "z": round(z, 3), "p_value": round(p, 6),
            "verdict": _verdict(lift, p, k),
        })
    return BracketResult(significator=significator, event_class=event_class,
                         level=level, brackets=out)


# --------------------------------------------------------------------------- #
# Transit (gochara) at the event                                              #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class TransitResult:
    event_class: str
    planet: str
    houses: list[int]
    n_events: int
    n_hit: int
    observed_rate: float
    expected_rate: float
    lift: float
    z: float
    p_value: float
    verdict: str


def validate_transit_house(con: duckdb.DuckDBPyConnection, planet: str = "Saturn",
                           houses: tuple[int, ...] = (6, 8, 12),
                           event_class: str = "death_cause_unspecified") -> TransitResult:
    """Is a planet transiting one of `houses` (from natal Lagna) at the event more
    than chance? Baseline = len(houses)/12 (uniform-house null)."""
    in_list = ",".join(str(int(h)) for h in houses)
    n, k = con.execute(
        f"""SELECT COUNT(*), COALESCE(SUM(CASE WHEN t.transit_natal_house IN ({in_list}) THEN 1 ELSE 0 END),0)
            FROM event_transits t JOIN events_with_dasha e USING(event_id)
            WHERE e.event_class = '{_q(event_class)}' AND t.transit_planet = '{_q(planet)}'"""
    ).fetchone()
    n, k = int(n), int(k)
    exp = len(houses) / 12.0
    obs = (k / n) if n else 0.0
    lift = obs / exp if exp else 0.0
    se = math.sqrt(n * exp * (1 - exp)) if n else 0.0
    z = (k - n * exp) / se if se else 0.0
    p = 2.0 * _norm_sf(abs(z))
    return TransitResult(
        event_class=event_class, planet=planet, houses=list(houses),
        n_events=n, n_hit=k, observed_rate=round(obs, 4), expected_rate=round(exp, 4),
        lift=round(lift, 3), z=round(z, 3), p_value=round(p, 6),
        verdict=_verdict(lift, p, k),
    )


def open_catalog(catalog: Path = DEFAULT_CATALOG) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(catalog), read_only=True)
