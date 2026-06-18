"""Per-chart death-window predictor — rank a living person's future dāśā periods.

This is the *forward* (per-chart) application of the population-scale findings in
``doctrine_validator``. Given a living person's birth data we:

  1. cast the natal chart (asc, graha houses, Moon longitude) — reusing the same
     ``_compute_chart`` the Silver layer uses, so the chart is identical to what the
     validator measured over 30k deaths;
  2. enumerate the 81 Vimśottarī MD×AD windows (``build_dasha_windows`` logic) and
     keep the ones that fall *after* an as-of date (the person's future);
  3. score each window's death risk by combining the two empirically-validated
     levers — the **composite death-significator confluence** (how many of
     {maraka_full, 3rd-lord, 64th-navāṁśa} the running MD lord plays, a measured
     dose-response) and the **longevity bracket** (does the window land in the
     alpa / madhya / pūrṇa age-window where that confluence actually fires);
  4. return the windows ranked by composite × bracket risk.

The risk multipliers default to the lifts measured this session (see
``DEFAULT_COMPOSITE_FACTOR`` / ``DEFAULT_BRACKET_FACTOR``) but can be re-calibrated
live from the DuckDB catalog via :func:`calibrate_factors`, so the predictor always
reflects the current corpus rather than frozen magic numbers.

Pure-Python + swisseph; no catalog required for the core path (the validated lifts
are baked in), which keeps it serveable and CI-testable without the heavy parquet.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from typing import Any

import swisseph as swe

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR, calculate_jd
from app.medini.analysis.doctrine_validator import (
    DEFAULT_BRACKETS,
    LORD_SHARE,
    _DEATH_COMPOSITE,
    _MARAKA_GRAHAS,
    _SIGNIFICATORS,
    validate_composite_death_score,
    validate_significator_by_bracket,
)
from app.medini.etl.build_charts_table import _compute_chart
from app.medini.etl.build_dasha_windows import _windows_for_person

# Empirically measured this session over ~30.9k dated deaths (death_cause_unspecified,
# MD level). Composite = P(MD lord plays >= k of {maraka_full, 3rd-lord, 64th-navāṁśa})
# lifts at each threshold; mapped here to a per-window factor by the lord's exact role
# count (0 roles = neutral, the dose-response climbs from there).
DEFAULT_COMPOSITE_FACTOR: dict[int, float] = {0: 1.0, 1: 1.022, 2: 1.086, 3: 1.151}

# Longevity bracket (āyurdāya) lift for the maraka_full significator: the confluence
# fires in madhya (32–70), is under-represented in alpa (<32), and is null in pūrṇa.
DEFAULT_BRACKET_FACTOR: dict[str, float] = {"alpa": 0.89, "madhya": 1.085, "purna": 1.01}

# How much an antardaśā lord's own confluence reinforces the mahādaśā's risk. The
# AD modulates but does not dominate the MD, so its excess-over-1 is down-weighted.
# (A blend heuristic, not a measured lift — kept explicit and tunable.)
AD_WEIGHT: float = 0.5


@dataclass(frozen=True)
class DeathWindow:
    """One ranked future MD×AD period and its composite death-risk."""
    rank: int
    window_id: str
    md_lord: str
    ad_lord: str
    md_seq: int
    ad_seq: int
    start_date: str        # ISO date (UTC) of AD start
    end_date: str          # ISO date (UTC) of AD end
    start_age: float       # age in years at window start
    end_age: float
    bracket: str           # alpa | madhya | purna (by mid-window age)
    md_score: int          # # of composite roles the MD lord plays (0..3)
    md_roles: list[str]    # which significators (maraka_full / third_lord / navamsa_64)
    ad_score: int
    composite_factor: float
    bracket_factor: float
    ad_factor: float
    risk_score: float      # composite × bracket × AD reinforcement

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _jd_to_iso(jd: float) -> str:
    """Julian Day → ISO date string (UTC, day precision)."""
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _bracket_for_age(age: float,
                     brackets: tuple[tuple[str, float, float], ...]) -> str:
    for name, lo, hi in brackets:
        if lo <= age < hi:
            return name
    return brackets[-1][0]  # ages past the last bound fall in the final bracket


def _role_count(lord: str, asc_sign: int, asc_lon: float,
                graha_houses: dict[str, int],
                significators: tuple[str, ...]) -> tuple[int, list[str]]:
    """How many of `significators` the given dasha lord plays, and which ones."""
    roles = [s for s in significators
             if lord in _SIGNIFICATORS[s](asc_sign, asc_lon, graha_houses)]
    return len(roles), roles


def calibrate_factors(
    con: Any,
    event_class: str = "death_cause_unspecified",
    level: str = "md",
) -> tuple[dict[int, float], dict[str, float]]:
    """Re-derive the composite + bracket factors live from the DuckDB catalog.

    Returns ``(composite_factor, bracket_factor)`` in the same shape as the
    DEFAULT_* constants, read straight off the validators so the predictor tracks
    the current corpus. Score 0 stays neutral (1.0); thresholds k=1..n take that
    threshold's measured lift.
    """
    comp = validate_composite_death_score(con, event_class, level)
    composite = {0: 1.0}
    for t in comp.thresholds:
        composite[int(t["k"])] = float(t["lift"]) or 1.0

    br = validate_significator_by_bracket(con, "maraka_full", event_class, level)
    bracket = {b["name"]: (float(b["lift"]) or 1.0) for b in br.brackets}
    return composite, bracket


def predict_death_windows(
    *,
    year: int, month: int, day: int,
    hour: int = 12, minute: int = 0,
    latitude: float, longitude: float,
    tz_offset: float = 0.0,
    as_of: dt.date | None = None,
    top_n: int | None = None,
    significators: tuple[str, ...] = _DEATH_COMPOSITE,
    brackets: tuple[tuple[str, float, float], ...] = DEFAULT_BRACKETS,
    composite_factor: dict[int, float] | None = None,
    bracket_factor: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Rank a living person's future Vimśottarī windows by composite × bracket risk.

    Casts the natal chart, enumerates the MD×AD windows, keeps those ending after
    `as_of` (default = today, UTC), scores each, and returns them ranked.
    """
    if latitude is None or longitude is None:
        raise ValueError("latitude and longitude are required to cast the chart")
    composite_factor = composite_factor or DEFAULT_COMPOSITE_FACTOR
    bracket_factor = bracket_factor or DEFAULT_BRACKET_FACTOR
    bad = [s for s in significators if s not in _SIGNIFICATORS]
    if bad:
        raise ValueError(f"unknown significator(s): {bad}")

    decimal_hour = hour + minute / 60.0
    birth_jd = calculate_jd(year, month, day, decimal_hour, tz_offset)

    chart = _compute_chart("live", birth_jd, None, latitude, longitude)
    if chart is None:
        raise ValueError("could not cast chart from the supplied birth data")
    asc_sign = int(chart["asc_sign"])
    asc_lon = float(chart["asc_lon"])
    moon_lon = float(chart["moon_lon"])
    graha_houses = {g: int(chart[f"{g.lower()}_house"]) for g in _MARAKA_GRAHAS}

    as_of = as_of or dt.datetime.now(dt.timezone.utc).date()
    as_of_jd = calculate_jd(as_of.year, as_of.month, as_of.day, 12.0, 0.0)
    current_age = round((as_of_jd - birth_jd) / DAYS_PER_VEDIC_YEAR, 2)

    raw = _windows_for_person("live", birth_jd, moon_lon)

    # Cache each lord's composite role-count — only 9 distinct lords.
    role_cache: dict[str, tuple[int, list[str]]] = {}

    def roles(lord: str) -> tuple[int, list[str]]:
        if lord not in role_cache:
            role_cache[lord] = _role_count(lord, asc_sign, asc_lon, graha_houses, significators)
        return role_cache[lord]

    scored: list[DeathWindow] = []
    for w in raw:
        if w["end_jd"] <= as_of_jd:   # entirely in the past
            continue
        start_age = (w["start_jd"] - birth_jd) / DAYS_PER_VEDIC_YEAR
        end_age = (w["end_jd"] - birth_jd) / DAYS_PER_VEDIC_YEAR
        mid_age = (start_age + end_age) / 2.0
        bracket = _bracket_for_age(mid_age, brackets)

        md_score, md_roles = roles(w["md_lord"])
        ad_score, _ = roles(w["ad_lord"])

        c_factor = composite_factor.get(md_score, composite_factor.get(max(composite_factor), 1.0))
        b_factor = bracket_factor.get(bracket, 1.0)
        ad_c = composite_factor.get(ad_score, 1.0)
        ad_factor = 1.0 + AD_WEIGHT * (ad_c - 1.0)
        risk = c_factor * b_factor * ad_factor

        scored.append(DeathWindow(
            rank=0,  # filled after sort
            window_id=w["window_id"], md_lord=w["md_lord"], ad_lord=w["ad_lord"],
            md_seq=w["md_seq"], ad_seq=w["ad_seq"],
            start_date=_jd_to_iso(w["start_jd"]), end_date=_jd_to_iso(w["end_jd"]),
            start_age=round(start_age, 2), end_age=round(end_age, 2),
            bracket=bracket, md_score=md_score, md_roles=md_roles, ad_score=ad_score,
            composite_factor=round(c_factor, 4), bracket_factor=round(b_factor, 4),
            ad_factor=round(ad_factor, 4), risk_score=round(risk, 4),
        ))

    scored.sort(key=lambda d: d.risk_score, reverse=True)
    ranked = [DeathWindow(**{**asdict(d), "rank": i + 1}) for i, d in enumerate(scored)]
    if top_n is not None:
        ranked = ranked[:top_n]

    return {
        "birth_jd": birth_jd,
        "as_of": as_of.isoformat(),
        "current_age": current_age,
        "asc_sign": asc_sign,
        "significators": list(significators),
        "n_future_windows": len(scored),
        "windows": [d.to_dict() for d in ranked],
    }
