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


# ---------------------------------------------------------------------------
# M1: Antardasha + Pratyantar at any JD
# ---------------------------------------------------------------------------
#
# Vimshottari sub-period math (BPHS Ch.46):
#   AD_duration = MD_duration * AD_lord_years / 120
#   PD_duration = AD_duration * PD_lord_years / 120
# Sequence inside any period starts with the parent-period's lord and
# continues through the canonical Vimshottari order.

_DASHA_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

_DASHA_ORDER: tuple[str, ...] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
)


def _dasha_order_from(start_lord: str) -> tuple[str, ...]:
    """The 9-lord Vimshottari sequence starting at start_lord, wrapping."""
    if start_lord not in _DASHA_ORDER:
        raise ValueError(f"unknown dasha lord: {start_lord}")
    idx = _DASHA_ORDER.index(start_lord)
    return _DASHA_ORDER[idx:] + _DASHA_ORDER[:idx]


class ADLookup(BaseModel):
    """Result of looking up the active Antardasha at one JD."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_jd: float
    target_iso: str | None = None
    md_lord: str
    ad_lord: str
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    age_at_start_years: float
    age_at_end_years: float
    age_now_years: float
    md_progress_fraction: float = Field(ge=0.0, le=1.0)


class PDLookup(BaseModel):
    """Result of looking up the active Pratyantar at one JD."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_jd: float
    target_iso: str | None = None
    md_lord: str
    ad_lord: str
    pd_lord: str
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    age_at_start_years: float
    age_at_end_years: float
    age_now_years: float
    ad_progress_fraction: float = Field(ge=0.0, le=1.0)


def _ad_windows_within_md(md: MDLookup) -> list[tuple[str, float, float]]:
    """Return 9 (ad_lord, start_jd, end_jd) inside the given MD."""
    md_duration_days = md.end_jd - md.start_jd
    out: list[tuple[str, float, float]] = []
    cursor = md.start_jd
    for ad_lord in _dasha_order_from(md.md_lord):
        ad_years_share = _DASHA_YEARS[ad_lord] / 120.0
        ad_duration_days = md_duration_days * ad_years_share
        end = cursor + ad_duration_days
        out.append((ad_lord, cursor, end))
        cursor = end
    return out


def _pd_windows_within_ad(
    ad_start_jd: float, ad_end_jd: float, ad_lord: str,
) -> list[tuple[str, float, float]]:
    """Return 9 (pd_lord, start_jd, end_jd) inside the given AD."""
    ad_duration_days = ad_end_jd - ad_start_jd
    out: list[tuple[str, float, float]] = []
    cursor = ad_start_jd
    for pd_lord in _dasha_order_from(ad_lord):
        pd_years_share = _DASHA_YEARS[pd_lord] / 120.0
        pd_duration_days = ad_duration_days * pd_years_share
        end = cursor + pd_duration_days
        out.append((pd_lord, cursor, end))
        cursor = end
    return out


def ad_at_jd(
    reading: Mapping[str, Any],
    target_jd: float | None = None,
) -> ADLookup:
    """Look up which Antardasha is active at ``target_jd``.

    Works for any target_jd within the natal Vimshottari window. Computes
    the 9 ADs within the MD covering target_jd via Vimshottari proportional
    math (no Track A/B invocation needed)."""
    if target_jd is None:
        target_jd = _jd_now_utc()

    md = md_at_jd(reading, target_jd=target_jd)
    ad_windows = _ad_windows_within_md(md)

    chosen: tuple[str, float, float] | None = None
    for window in ad_windows:
        ad_lord, start, end = window
        if start <= target_jd < end:
            chosen = window
            break
    if chosen is None:
        raise ValueError(
            f"target_jd {target_jd} not within any AD inside MD {md.md_lord}"
        )

    ad_lord, ad_start, ad_end = chosen
    birth_jd = float(
        (reading.get("chart") or {}).get("extras", {}).get("birth_jd")
        or md.start_jd
    )

    md_progress = (target_jd - md.start_jd) / (md.end_jd - md.start_jd)
    md_progress = max(0.0, min(1.0, md_progress))

    return ADLookup(
        target_jd=target_jd,
        target_iso=_iso_from_jd(target_jd),
        md_lord=md.md_lord,
        ad_lord=ad_lord,
        start_jd=ad_start,
        end_jd=ad_end,
        start_date=_iso_from_jd(ad_start) or "",
        end_date=_iso_from_jd(ad_end) or "",
        age_at_start_years=(ad_start - birth_jd) / 365.2425,
        age_at_end_years=(ad_end - birth_jd) / 365.2425,
        age_now_years=(target_jd - birth_jd) / 365.2425,
        md_progress_fraction=md_progress,
    )


def pd_at_jd(
    reading: Mapping[str, Any],
    target_jd: float | None = None,
) -> PDLookup:
    """Look up which Pratyantar is active at ``target_jd``."""
    if target_jd is None:
        target_jd = _jd_now_utc()

    ad = ad_at_jd(reading, target_jd=target_jd)
    pd_windows = _pd_windows_within_ad(ad.start_jd, ad.end_jd, ad.ad_lord)

    chosen: tuple[str, float, float] | None = None
    for window in pd_windows:
        pd_lord, start, end = window
        if start <= target_jd < end:
            chosen = window
            break
    if chosen is None:
        raise ValueError(
            f"target_jd {target_jd} not within any PD inside "
            f"MD={ad.md_lord} AD={ad.ad_lord}"
        )

    pd_lord, pd_start, pd_end = chosen
    birth_jd = float(
        (reading.get("chart") or {}).get("extras", {}).get("birth_jd")
        or ad.start_jd
    )

    ad_progress = (target_jd - ad.start_jd) / (ad.end_jd - ad.start_jd)
    ad_progress = max(0.0, min(1.0, ad_progress))

    return PDLookup(
        target_jd=target_jd,
        target_iso=_iso_from_jd(target_jd),
        md_lord=ad.md_lord,
        ad_lord=ad.ad_lord,
        pd_lord=pd_lord,
        start_jd=pd_start,
        end_jd=pd_end,
        start_date=_iso_from_jd(pd_start) or "",
        end_date=_iso_from_jd(pd_end) or "",
        age_at_start_years=(pd_start - birth_jd) / 365.2425,
        age_at_end_years=(pd_end - birth_jd) / 365.2425,
        age_now_years=(target_jd - birth_jd) / 365.2425,
        ad_progress_fraction=ad_progress,
    )


def ad_at_now(reading: Mapping[str, Any]) -> ADLookup:
    """Convenience: AD active at the current UTC moment."""
    return ad_at_jd(reading, target_jd=_jd_now_utc())


def pd_at_now(reading: Mapping[str, Any]) -> PDLookup:
    """Convenience: PD active at the current UTC moment."""
    return pd_at_jd(reading, target_jd=_jd_now_utc())
