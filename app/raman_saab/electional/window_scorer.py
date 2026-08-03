"""Candidate-window evaluation — Raman's own essentials ordering (MUHURTHA-10:226-228).

"For any election, purity of the lunar day, week-day and constellation and Tarabala are
essential and further considerations come in only later on." This module applies exactly
that: HARD-FAIL when the moment sits inside a negative window (Rahu Kalam / Durmuhurtha /
thyajya) or fails Chandrabala/Panchaka; otherwise score by the essentials.

Every factor carries its citation via the underlying modules; this scorer adds no doctrine
of its own. Output is a statement of Raman's electional method, never a validated
prediction (Measured-Truth framing applies wherever surfaced).

Usage:
    from app.raman_saab.electional.window_scorer import evaluate_moment
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.raman_saab.electional.negative_windows import PanchakaResult, Window, panchaka
from app.raman_saab.electional.panchanga_suitability import LimbVerdict, limb_suitability
from app.raman_saab.electional.tarabala import Tarabala, chandrabala, tarabala


@dataclass(frozen=True)
class MomentEvaluation:
    ok: bool                    # no hard failure
    hard_failures: tuple[str, ...]
    tarabala: Tarabala
    chandrabala_ok: bool
    limbs: tuple[LimbVerdict, ...]
    panchaka: PanchakaResult
    score: int                  # favourable essentials count (of 8), for ranking only


def evaluate_moment(*, jd: float, janma_nakshatra: int, janma_rasi: int,
                    tithi_in_paksha: int, weekday: int, day_nakshatra: int, yoga: int,
                    karana: int, election_moon_rasi: int, lagna_sign: int,
                    act: Optional[str] = None,
                    negative_windows: tuple[Window, ...] = ()) -> MomentEvaluation:
    """Evaluate one candidate moment. `negative_windows` are precomputed for the day via
    `negative_windows.rahu_kalam` / `durmuhurtha_windows` / the thyajya helpers; a moment
    inside any of them hard-fails with that window's label."""
    failures: list[str] = []
    for w in negative_windows:
        if w.start_jd <= jd < w.end_jd:
            failures.append(w.label)

    tb = tarabala(janma_nakshatra, day_nakshatra)
    cb = chandrabala(janma_rasi, election_moon_rasi)
    limbs = limb_suitability(tithi_in_paksha=tithi_in_paksha, weekday=weekday,
                             nakshatra=day_nakshatra, yoga=yoga, karana=karana)
    pk = panchaka(tithi_in_paksha, weekday + 1, day_nakshatra, lagna_sign, act=act)

    if not cb:
        failures.append("Chandrabala: election Moon 6/8/12 from Janma Rasi (MUHURTHA-3:66)")
    if not pk.favourable:
        failures.append(f"Panchaka: {pk.name} (MUHURTHA-3:104)")

    score = (sum(1 for lv in limbs if lv.suitable)
             + (1 if tb.favourable else 0) + (1 if cb else 0) + (1 if pk.favourable else 0))
    return MomentEvaluation(ok=not failures, hard_failures=tuple(failures), tarabala=tb,
                            chandrabala_ok=cb, limbs=limbs, panchaka=pk, score=score)
