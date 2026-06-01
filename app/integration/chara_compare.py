"""Cross-engine Chara Dasha comparator.

Both Track A (``app.reading.sequences.chara_dasha``) and Track B
(``app.core.chara_dasha``) independently implement Jaimini Chara Dasha
(D-17 in Track A's doctrine lockfile). If both encode the doctrine
correctly, their per-MD sign sequences and window JDs MUST agree.

Disagreement is doctrine-relevant evidence — either one implementation has
a bug, or they encode different Chara Dasha variants (Sanjay-Rath vs
Iranganti Rangacharya vs Krishnamurti etc.). This comparator surfaces such
disagreements without modifying either engine.

Public surface
--------------
- ``compare_chara_dasha(track_a_result, lagna_sign, birth_jd, target_jd)`` →
  ``CharaComparisonReport`` containing per-MD agreement matrix.
- ``CharaComparisonReport`` — Pydantic envelope with the diff summary.

The comparator does NOT run the full Track-A pipeline. The caller supplies
``track_a_result`` (a ``CharaDashaResult`` from a prior ``run_sequence()``
call) plus the same ``lagna_sign``/``birth_jd`` inputs that produced it.
Track B's run is invoked fresh inside the comparator.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.core.chara_dasha import (
    chara_active_at as b_chara_active_at,
    chara_windows_jd as b_chara_windows_jd,
)
from app.reading.sequences.chara_dasha import CharaDashaResult

# JD tolerance for declaring two window boundaries "equal". 1 day = ~1 in JD;
# Vimshottari/Chara math uses 365.2425 mean days per year so rounding error
# accumulates ~1e-6 over 84 years. 0.001 day = ~86 seconds is generous.
_JD_TOLERANCE_DAYS: float = 0.001


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class MDWindowDiff(BaseModel):
    """Per-MD agreement record between the two engines.

    Both engines emit 12 MDs in Chara Dasha (one per sign cycle). For each
    index ``i`` in 0..11 we compare: sign agreement (do both engines name the
    same sign?), start-JD agreement (within ``_JD_TOLERANCE_DAYS``), end-JD
    agreement, and total-years agreement (derived from end-start).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    track_a_md_sign: int
    track_b_md_sign: int
    sign_agrees: bool
    track_a_start_jd: float
    track_b_start_jd: float
    start_jd_delta_days: float
    track_a_end_jd: float
    track_b_end_jd: float
    end_jd_delta_days: float
    track_a_total_years: float
    track_b_total_years: float
    years_delta: float
    agrees: bool  # all three sub-checks pass


class CharaComparisonReport(BaseModel):
    """Top-level report from ``compare_chara_dasha``.

    Aggregates per-MD diffs plus a summary verdict and the "current MD" cross-
    check at the supplied target JD.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    lagna_sign: int = Field(ge=1, le=12)
    birth_jd: float
    target_jd: float | None
    jd_tolerance_days: float = _JD_TOLERANCE_DAYS

    track_a_engine: str = "app.reading.sequences.chara_dasha"
    track_b_engine: str = "app.core.chara_dasha"

    track_a_md_count: int
    track_b_md_count: int
    count_agrees: bool

    per_md_diffs: list[MDWindowDiff]
    all_signs_agree: bool
    all_boundaries_agree: bool
    full_timeline_agrees: bool

    # Current-MD cross-check at target_jd (None if no target_jd supplied).
    current_md_track_a: int | None
    current_md_track_b: int | None
    current_md_agrees: bool | None

    # Human-readable one-liner of the overall verdict.
    verdict_summary: str


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def compare_chara_dasha(
    track_a_result: CharaDashaResult,
    *,
    lagna_sign: int,
    birth_jd: float,
    target_jd: float | None = None,
) -> CharaComparisonReport:
    """Diff Track A and Track B Chara Dasha timelines.

    Parameters
    ----------
    track_a_result
        A ``CharaDashaResult`` from a prior
        ``app.reading.sequences.chara_dasha.run_sequence()`` call.
    lagna_sign
        1..12, the lagna sign that was used to produce ``track_a_result``.
        Passed to Track B's ``chara_windows_jd()`` for the comparison.
    birth_jd
        The same birth Julian Day used to produce ``track_a_result``.
    target_jd
        Optional. If supplied, the "currently active MD" cross-check at this
        JD is included in the report. Pass ``None`` to skip.

    Returns
    -------
    CharaComparisonReport
        Per-MD diff plus aggregate verdict.
    """
    # Track B fresh run.
    b_windows = b_chara_windows_jd(lagna_sign, birth_jd)  # tuple[(sign, start_jd, end_jd), ...]

    a_timeline = track_a_result.timeline
    a_count = len(a_timeline)
    b_count = len(b_windows)
    count_agrees = a_count == b_count

    per_md: list[MDWindowDiff] = []
    pairs = min(a_count, b_count)
    for i in range(pairs):
        a_period = a_timeline[i]
        b_sign, b_start, b_end = b_windows[i]

        start_delta = abs(a_period.start_jd - b_start)
        end_delta = abs(a_period.end_jd - b_end)
        a_years = a_period.total_years
        b_years = (b_end - b_start) / 365.2425  # same DAYS_PER_VEDIC_YEAR constant
        years_delta = abs(a_years - b_years)

        sign_ok = a_period.md_sign == b_sign
        start_ok = start_delta <= _JD_TOLERANCE_DAYS
        end_ok = end_delta <= _JD_TOLERANCE_DAYS

        per_md.append(MDWindowDiff(
            index=i,
            track_a_md_sign=a_period.md_sign,
            track_b_md_sign=b_sign,
            sign_agrees=sign_ok,
            track_a_start_jd=a_period.start_jd,
            track_b_start_jd=b_start,
            start_jd_delta_days=start_delta,
            track_a_end_jd=a_period.end_jd,
            track_b_end_jd=b_end,
            end_jd_delta_days=end_delta,
            track_a_total_years=a_years,
            track_b_total_years=b_years,
            years_delta=years_delta,
            agrees=sign_ok and start_ok and end_ok,
        ))

    all_signs_agree = count_agrees and all(d.sign_agrees for d in per_md)
    all_boundaries_agree = count_agrees and all(
        d.start_jd_delta_days <= _JD_TOLERANCE_DAYS
        and d.end_jd_delta_days <= _JD_TOLERANCE_DAYS
        for d in per_md
    )
    full_agreement = count_agrees and all(d.agrees for d in per_md)

    # Current-MD cross-check.
    if target_jd is not None:
        current_a = track_a_result.current_md_judgment.md_sign
        current_b = b_chara_active_at(lagna_sign, birth_jd, target_jd)
        current_agrees = current_a == current_b
    else:
        current_a = None
        current_b = None
        current_agrees = None

    verdict = _build_verdict_summary(
        count_agrees=count_agrees,
        a_count=a_count,
        b_count=b_count,
        all_signs_agree=all_signs_agree,
        all_boundaries_agree=all_boundaries_agree,
        full_agreement=full_agreement,
        current_agrees=current_agrees,
    )

    return CharaComparisonReport(
        lagna_sign=lagna_sign,
        birth_jd=birth_jd,
        target_jd=target_jd,
        track_a_md_count=a_count,
        track_b_md_count=b_count,
        count_agrees=count_agrees,
        per_md_diffs=per_md,
        all_signs_agree=all_signs_agree,
        all_boundaries_agree=all_boundaries_agree,
        full_timeline_agrees=full_agreement,
        current_md_track_a=current_a,
        current_md_track_b=current_b,
        current_md_agrees=current_agrees,
        verdict_summary=verdict,
    )


def _build_verdict_summary(
    *,
    count_agrees: bool,
    a_count: int,
    b_count: int,
    all_signs_agree: bool,
    all_boundaries_agree: bool,
    full_agreement: bool,
    current_agrees: bool | None,
) -> str:
    if not count_agrees:
        return f"MD count differs: Track A = {a_count}, Track B = {b_count}"
    if full_agreement and (current_agrees is None or current_agrees):
        return f"FULL AGREEMENT across {a_count} MDs (signs + boundaries)"
    parts: list[str] = []
    if not all_signs_agree:
        parts.append("SIGN sequence diverges")
    if not all_boundaries_agree:
        parts.append("BOUNDARY JDs diverge")
    if current_agrees is False:
        parts.append("CURRENT MD disagrees at target_jd")
    return "; ".join(parts) if parts else "partial agreement"
