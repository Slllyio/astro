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
from app.medini.etl.build_dasha_windows import _antardashas_in_md, _windows_for_person
from app.medini.etl.feature_engineering import compute_full_mahadasha_cycle

# Empirically measured over ~36.4k dated deaths (death_cause_unspecified, MD level)
# after the Wikidata day-precision enrichment. Composite = P(MD lord plays >= k of
# {maraka_full, 3rd-lord, 64th-navāṁśa}) lifts at each threshold; mapped here to a
# per-window factor by the lord's exact role count (0 roles = neutral, the
# dose-response climbs from there).
DEFAULT_COMPOSITE_FACTOR: dict[int, float] = {0: 1.0, 1: 1.026, 2: 1.096, 3: 1.189}

# Longevity bracket (āyurdāya) lift for the maraka_full significator: the confluence
# fires in madhya (32–70), is under-represented in alpa (<32), and is only marginal
# in pūrṇa (>70).
DEFAULT_BRACKET_FACTOR: dict[str, float] = {"alpa": 0.895, "madhya": 1.092, "purna": 1.016}

# How much an antardaśā (AD) / pratyantardaśā (PD) lord's own confluence reinforces
# the mahādaśā's risk. Sub-periods modulate but do not dominate the MD, so each
# successively finer level's excess-over-1 is down-weighted further. (Blend
# heuristics, not measured lifts — kept explicit and tunable.)
AD_WEIGHT: float = 0.5
PD_WEIGHT: float = 0.25


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
    risk_score: float      # composite × bracket × AD (× PD) reinforcement
    probability: float | None = None   # calibrated P(death in this window | alive now)
    pd_lord: str | None = None          # pratyantardaśā lord (depth="pd" only)
    pd_seq: int | None = None
    pd_score: int | None = None
    pd_factor: float | None = None
    trigger_bands: list[dict] | None = None  # transit-Saturn danger bands (transit_refine)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MortalityModel:
    """Empirical age-at-death distribution from the corpus, as a conditional
    survival model. Holds the sorted death ages so window masses and remaining-life
    quantiles are exact ECDF reads (no parametric assumption)."""
    ages: tuple[float, ...]   # sorted ascending

    @classmethod
    def from_catalog(cls, con: Any, event_class: str = "death_cause_unspecified") -> "MortalityModel":
        rows = con.execute(
            "SELECT age_at_event_years FROM events_with_dasha "
            "WHERE event_class = ? AND age_at_event_years IS NOT NULL "
            "AND age_at_event_years >= 0 AND age_at_event_years <= 120",
            [event_class],
        ).fetchall()
        return cls(ages=tuple(sorted(float(r[0]) for r in rows)))

    def _below(self, a: float) -> int:
        import bisect
        return bisect.bisect_left(self.ages, a)

    def mass(self, a0: float, a1: float) -> float:
        """Fraction of deaths with age in [a0, a1)."""
        n = len(self.ages)
        if n == 0 or a1 <= a0:
            return 0.0
        return (self._below(a1) - self._below(a0)) / n

    def survival(self, c: float) -> float:
        """Fraction of deaths occurring at age >= c (≈ P(still to die | this cohort))."""
        n = len(self.ages)
        return (n - self._below(c)) / n if n else 0.0

    def prob_within(self, c: float, years: float) -> float:
        """P(death in (c, c+years] | alive at c)."""
        s = self.survival(c)
        return self.mass(c, c + years) / s if s > 0 else 0.0

    def median_remaining(self, c: float) -> float | None:
        """Conditional median remaining years given alive at age c."""
        s = self.survival(c)
        if s <= 0:
            return None
        target = 0.5 * s            # half the surviving mass
        n = len(self.ages)
        base = self._below(c)
        idx = base + int(round(target * n))
        if idx >= n:
            return None
        return round(self.ages[min(idx, n - 1)] - c, 1)


def _jd_to_iso(jd: float) -> str:
    """Julian Day → ISO date string (UTC, day precision)."""
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _iso_to_ymd(iso: str) -> tuple[int, int, int]:
    """'YYYY-MM-DD' → (year, month, day)."""
    y, m, d = iso.split("-")
    return int(y), int(m), int(d)


def _bracket_for_age(age: float,
                     brackets: tuple[tuple[str, float, float], ...]) -> str:
    for name, lo, hi in brackets:
        if lo <= age < hi:
            return name
    return brackets[-1][0]  # ages past the last bound fall in the final bracket


def _future_windows(birth_jd: float, moon_lon: float, depth: str) -> list[dict[str, Any]]:
    """Enumerate the natal Vimśottarī windows at the requested resolution.

    depth="ad": the 81 MD×AD windows (reuses the Silver builder).
    depth="pd": the 729 MD×AD×PD (pratyantardaśā) windows — month-resolution — by
    expanding each AD into 9 PDs with the same proportional rule (PD starts with the
    AD lord, then the canonical order; PD_years = AD_years · lord_years / 120)."""
    if depth == "ad":
        out = _windows_for_person("live", birth_jd, moon_lon)
        for w in out:
            w["pd_lord"], w["pd_seq"] = None, None
        return out
    if depth != "pd":
        raise ValueError("depth must be 'ad' or 'pd'")
    cycle = compute_full_mahadasha_cycle(birth_jd, moon_lon)
    out: list[dict[str, Any]] = []
    for md_seq, (md_lord, md_start, md_end) in enumerate(cycle):
        md_years = (md_end - md_start) / DAYS_PER_VEDIC_YEAR
        for ad_seq, (ad_lord, ad_start, ad_end) in enumerate(
            _antardashas_in_md(md_lord, md_start, md_years)
        ):
            ad_years = (ad_end - ad_start) / DAYS_PER_VEDIC_YEAR
            for pd_seq, (pd_lord, pd_start, pd_end) in enumerate(
                _antardashas_in_md(ad_lord, ad_start, ad_years)
            ):
                out.append({
                    "window_id": f"live::MD::{md_lord}::AD::{ad_lord}::PD::{pd_lord}::{md_seq}.{ad_seq}",
                    "md_lord": md_lord, "ad_lord": ad_lord, "pd_lord": pd_lord,
                    "md_seq": md_seq, "ad_seq": ad_seq, "pd_seq": pd_seq,
                    "start_jd": pd_start, "end_jd": pd_end,
                })
    return out


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
    mortality: "MortalityModel | None" = None,
    depth: str = "ad",
    transit_refine: bool = False,
) -> dict[str, Any]:
    """Rank a living person's future Vimśottarī windows by composite × bracket risk.

    Casts the natal chart, enumerates the MD×AD windows, keeps those ending after
    `as_of` (default = today, UTC), scores each, and returns them ranked.

    If a `mortality` model is supplied, each window also gets a *calibrated*
    ``probability`` — P(death falls in this window | alive now) — and the windows are
    ranked by it. The probability is the empirical age-at-death mass over the window's
    age span (which already encodes duration + age-of-death shape) tilted by the
    composite confluence factor, renormalized over the person's future windows. The
    bracket factor is deliberately NOT re-applied here: the empirical age density
    already carries the longevity-bracket effect, so applying it again would
    double-count age.
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

    raw = _future_windows(birth_jd, moon_lon, depth)

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

        pd_lord = w.get("pd_lord")
        pd_score = pd_factor = None
        if pd_lord is not None:
            pd_score, _ = roles(pd_lord)
            pd_c = composite_factor.get(pd_score, 1.0)
            pd_factor = 1.0 + PD_WEIGHT * (pd_c - 1.0)
            risk *= pd_factor

        scored.append(DeathWindow(
            rank=0,  # filled after sort
            window_id=w["window_id"], md_lord=w["md_lord"], ad_lord=w["ad_lord"],
            md_seq=w["md_seq"], ad_seq=w["ad_seq"],
            start_date=_jd_to_iso(w["start_jd"]), end_date=_jd_to_iso(w["end_jd"]),
            start_age=round(start_age, 2), end_age=round(end_age, 2),
            bracket=bracket, md_score=md_score, md_roles=md_roles, ad_score=ad_score,
            composite_factor=round(c_factor, 4), bracket_factor=round(b_factor, 4),
            ad_factor=round(ad_factor, 4), risk_score=round(risk, 4),
            pd_lord=pd_lord, pd_seq=w.get("pd_seq"), pd_score=pd_score,
            pd_factor=round(pd_factor, 4) if pd_factor is not None else None,
        ))

    # Calibrated probabilities from the empirical age-at-death model.
    summary: dict[str, Any] = {}
    if mortality is not None and scored:
        bases = []
        for d in scored:
            lo = max(d.start_age, current_age)   # condition on survival to now
            base = mortality.mass(lo, d.end_age) * d.composite_factor
            bases.append(max(base, 0.0))
        total = sum(bases)
        scored = [
            DeathWindow(**{**asdict(d),
                           "probability": round(b / total, 4) if total > 0 else 0.0})
            for d, b in zip(scored, bases)
        ]
        summary = {
            "median_remaining_years": mortality.median_remaining(current_age),
            "prob_within_5y": round(mortality.prob_within(current_age, 5.0), 4),
            "prob_within_10y": round(mortality.prob_within(current_age, 10.0), 4),
        }

    sort_key = ((lambda d: (d.probability or 0.0)) if mortality is not None
                else (lambda d: d.risk_score))
    scored.sort(key=sort_key, reverse=True)
    ranked = [DeathWindow(**{**asdict(d), "rank": i + 1}) for i, d in enumerate(scored)]
    if top_n is not None:
        ranked = ranked[:top_n]

    # Transit-trigger refinement: narrow each returned window to the weeks when
    # transit Saturn is within orb of a natal maraka/Sun point (validated lift 1.13).
    if transit_refine and ranked:
        from app.medini.analysis import transit_triggers as tt
        natal_lons = {g: float(chart[f"{g.lower()}_lon"]) for g in _MARAKA_GRAHAS}
        natal_lons["Sun"] = float(chart["sun_lon"])
        pts = tt.death_trigger_points(asc_sign, graha_houses, natal_lons)
        ranked = [
            DeathWindow(**{**asdict(d), "trigger_bands": [
                {"start_date": iv.start_date, "end_date": iv.end_date, "days": iv.days}
                for iv in tt.active_trigger_intervals(
                    calculate_jd(*_iso_to_ymd(d.start_date), 12.0, 0.0),
                    calculate_jd(*_iso_to_ymd(d.end_date), 12.0, 0.0), pts)
            ]})
            for d in ranked
        ]

    return {
        "birth_jd": birth_jd,
        "as_of": as_of.isoformat(),
        "current_age": current_age,
        "asc_sign": asc_sign,
        "significators": list(significators),
        "depth": depth,
        "calibrated": mortality is not None,
        **summary,
        "n_future_windows": len(scored),
        "windows": [d.to_dict() for d in ranked],
    }
