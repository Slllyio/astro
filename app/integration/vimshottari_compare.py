"""Cross-engine Vimshottari current-MD comparator.

Both Track A (``app.reading.sequences.vimshottari_md``) and Track B
(``app.core.ephemeris_engine.calculate_vimshottari_mahadasha``) compute the
Vimshottari mahadasha state for a natal chart. Track A produces the FULL
9-MD timeline; Track B produces only the CURRENT MD (lord + start/end +
years_elapsed + years_remaining).

This comparator anchors on the SHARED primitive — current MD — and verifies
both engines agree on:
- Current MD lord (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu)
- Current MD start date (ISO YYYY-MM-DD)
- Current MD end date (ISO YYYY-MM-DD)
- Total duration (years)

Both engines use the same Vimshottari math primitives — nakshatra-floor on
Moon's longitude, DASHA_LORDS sequence, DAYS_PER_VEDIC_YEAR — so full
agreement is the expected outcome. Any divergence here is a real bug.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.ephemeris_engine import calculate_vimshottari_mahadasha


class VimshottariCurrentMDReport(BaseModel):
    """Aggregate report from ``compare_vimshottari_current_md``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    track_a_engine: str = "app.reading.sequences.vimshottari_md"
    track_b_engine: str = "app.core.ephemeris_engine.calculate_vimshottari_mahadasha"

    moon_longitude: float
    birth_jd: float

    track_a_md_lord: str
    track_b_md_lord: str
    md_lord_agrees: bool

    track_a_md_start: str
    track_b_md_start: str
    track_a_md_end: str
    track_b_md_end: str
    md_dates_agree: bool

    track_a_md_duration_years: float
    track_b_md_duration_years: float
    duration_agrees: bool

    verdict_summary: str


def _find_current_md(md_judgments: list[dict[str, Any]]) -> dict[str, Any]:
    """Find the dict with ``is_current=True`` in a md_judgments list."""
    for entry in md_judgments:
        if entry.get("is_current"):
            return entry
    raise ValueError(
        "no md_judgments entry has is_current=True — reading is malformed"
    )


# Vimshottari MD durations in years (matches Track B DASHA_LORDS table).
_MD_DURATIONS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}


def compare_vimshottari_current_md(
    reading: dict[str, Any],
    *,
    moon_longitude: float,
    birth_jd: float,
) -> VimshottariCurrentMDReport:
    """Diff Track A's current MD against Track B's calculate_vimshottari_mahadasha.

    Parameters
    ----------
    reading
        A Track-A ReadingOutput-shaped dict. Comparator reads from
        ``reading.sequences.md_judgments`` and extracts the entry where
        ``is_current=True``.
    moon_longitude
        Same Moon longitude (sidereal) that produced the reading.
    birth_jd
        Same birth Julian Day used in the reading.
    """
    md_judgments = (reading.get("sequences") or {}).get("md_judgments") or []
    a_current = _find_current_md(md_judgments)
    a_lord = str(a_current["md_lord"])
    a_start = str(a_current["start_date"])
    a_end = str(a_current["end_date"])
    a_duration = float(_MD_DURATIONS.get(a_lord, 0))

    b_block = calculate_vimshottari_mahadasha(moon_longitude, birth_jd)
    b_lord = b_block["mahadasha_lord"]
    b_start = b_block["start_date"]
    b_end = b_block["end_date"]
    b_duration = float(b_block["total_duration_years"])

    md_lord_agrees = a_lord == b_lord
    md_dates_agree = a_start == b_start and a_end == b_end
    duration_agrees = abs(a_duration - b_duration) < 1e-6

    if md_lord_agrees and md_dates_agree and duration_agrees:
        verdict = f"FULL AGREEMENT on current MD ({a_lord} {a_start}→{a_end})"
    else:
        parts: list[str] = []
        if not md_lord_agrees:
            parts.append(f"LORD diverges (A={a_lord}, B={b_lord})")
        if not md_dates_agree:
            parts.append(
                f"DATES diverge (A={a_start}→{a_end}, B={b_start}→{b_end})"
            )
        if not duration_agrees:
            parts.append(f"DURATION diverges (A={a_duration}, B={b_duration})")
        verdict = "; ".join(parts)

    return VimshottariCurrentMDReport(
        moon_longitude=moon_longitude,
        birth_jd=birth_jd,
        track_a_md_lord=a_lord,
        track_b_md_lord=b_lord,
        md_lord_agrees=md_lord_agrees,
        track_a_md_start=a_start,
        track_b_md_start=b_start,
        track_a_md_end=a_end,
        track_b_md_end=b_end,
        md_dates_agree=md_dates_agree,
        track_a_md_duration_years=a_duration,
        track_b_md_duration_years=b_duration,
        duration_agrees=duration_agrees,
        verdict_summary=verdict,
    )
