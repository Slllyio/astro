"""Look up the Vimshottari MD active at any given JD — including NOW.

Track A's ``reading.chart.extras.current_mahadasha`` is misleadingly
named — it returns the MD active AT BIRTH (the balance-of-MD on the
day the native was born), NOT the MD active at the moment the reading
was generated.

For a 1989-born native sitting in 2026, those are different. The
1989 native was born inside Rahu MD (1974-12-21 to 1992-12-21) — so
at birth they had ~3 years of Rahu MD remaining. The CURRENT MD now
(2026) is Saturn MD (started 2008-12-21).

This module provides ``md_at_jd(reading, target_jd)`` that walks the
``sequences.md_judgments`` 9-MD timeline (which Track A emits) and
returns the MD covering the target date — works for birth-MD,
current-time MD, or any future/past date.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timezone
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field


class MDLookup(BaseModel):
    """Result of looking up the active MD at one JD."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_jd: float
    target_iso: str | None = None
    md_lord: str
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    age_at_start_years: float
    age_at_end_years: float
    age_now_years: float
    is_at_birth: bool  # whether the target_jd is within ~1 day of birth_jd


def _jd_now_utc() -> float:
    """Current Julian Day (UTC) using the standard astronomical algorithm.

    Avoids relying on swisseph since this module is dependency-light.
    """
    now = datetime.now(timezone.utc)
    y, m, d = now.year, now.month, now.day
    hh, mm, ss = now.hour, now.minute, now.second
    day_fraction = (hh + mm / 60 + ss / 3600) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + (a // 4)
    jd = (
        int(365.25 * (y + 4716))
        + int(30.6001 * (m + 1))
        + d + b - 1524.5 + day_fraction
    )
    return jd


def md_at_jd(
    reading: Mapping[str, Any],
    target_jd: float | None = None,
) -> MDLookup:
    """Look up which Vimshottari MD is active at ``target_jd``.

    Parameters
    ----------
    reading
        Track-A reading dict (must contain ``sequences.md_judgments``
        with the full 9-MD timeline).
    target_jd
        Julian Day to query. If None, uses the CURRENT moment (UTC).

    Returns
    -------
    MDLookup
        Details of the active MD plus the native's age at start/end/now.

    Raises
    ------
    ValueError
        If the reading has no md_judgments timeline or target_jd is
        outside the natal Vimshottari coverage (~120 years).
    """
    if target_jd is None:
        target_jd = _jd_now_utc()

    md_judgments = (reading.get("sequences") or {}).get("md_judgments") or []
    if not md_judgments:
        raise ValueError(
            "reading.sequences.md_judgments is missing or empty — "
            "cannot look up MD without the timeline"
        )

    birth_jd = float(
        (reading.get("chart") or {}).get("extras", {}).get("birth_jd")
        or md_judgments[0].get("start_jd")
        or 0.0
    )

    chosen: dict[str, Any] | None = None
    for entry in md_judgments:
        start = float(entry.get("start_jd", 0))
        end = float(entry.get("end_jd", 0))
        if start <= target_jd < end:
            chosen = entry
            break
    if chosen is None:
        # Target outside the 120-yr Vimshottari window — fall back to nearest.
        # For ages 120+ classical doctrine repeats the cycle; we don't model that here.
        raise ValueError(
            f"target_jd {target_jd} not within any md_judgments window "
            f"(natal Vimshottari coverage is ~120 years from birth)"
        )

    start = float(chosen["start_jd"])
    end = float(chosen["end_jd"])
    age_at_start = (start - birth_jd) / 365.2425
    age_at_end = (end - birth_jd) / 365.2425
    age_now = (target_jd - birth_jd) / 365.2425

    return MDLookup(
        target_jd=target_jd,
        target_iso=_iso_from_jd(target_jd),
        md_lord=str(chosen.get("md_lord", "")),
        start_jd=start,
        end_jd=end,
        start_date=str(chosen.get("start_date", "")),
        end_date=str(chosen.get("end_date", "")),
        age_at_start_years=age_at_start,
        age_at_end_years=age_at_end,
        age_now_years=age_now,
        is_at_birth=abs(target_jd - birth_jd) < 1.0,
    )


def _iso_from_jd(jd: float) -> str | None:
    """Reverse JD -> YYYY-MM-DD using the inverse of the standard algo."""
    try:
        jd = jd + 0.5
        z = int(jd)
        f = jd - z
        if z < 2299161:
            a = z
        else:
            alpha = int((z - 1867216.25) / 36524.25)
            a = z + 1 + alpha - alpha // 4
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        day = b - d - int(30.6001 * e) + f
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    except Exception:
        return None


def md_at_birth(reading: Mapping[str, Any]) -> MDLookup:
    """Convenience: look up the MD active at birth (balance-of-MD)."""
    birth_jd = float((reading.get("chart") or {}).get("extras", {}).get("birth_jd", 0))
    if birth_jd <= 0:
        raise ValueError("reading.chart.extras.birth_jd missing")
    return md_at_jd(reading, target_jd=birth_jd)


def md_at_now(reading: Mapping[str, Any]) -> MDLookup:
    """Convenience: look up the MD active at the current UTC moment."""
    return md_at_jd(reading, target_jd=_jd_now_utc())
