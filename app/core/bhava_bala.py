"""Bhava Bala — intrinsic bhava strength (S-2 part 2).

Phase 6's bhava_judge produces a verdict per bhava using the three-pillar
gate (bhava × bhava-lord × karaka). That answers "is this bhava DELIVERING
on its promise" — but skips the upstream question: "is this bhava
INTRINSICALLY STRONG regardless of its lord's actions?"

Classical Shadbala (BPHS Ch.30) splits Bhava Bala into 3 components:

  1. Bhavadhipati Bala  — strength of the bhava's lord
  2. Bhava Drishti Bala — net benefic aspect on the bhava cusp
                          (benefics' drishti rupas - malefics' drishti rupas)
  3. Bhava Digbala      — directional / categorical bonus
                          (Kendra bhavas 1/4/7/10 get +1.0; Trikonas 5/9 get +0.5;
                           Upachayas 3/6/10/11 get +0.5; Dushtanas 6/8/12 get -0.5)

This module reads the chart + the base Reading (for lord strength labels)
and produces a per-bhava BhavaStrengthReport. Composite Bhava Bala is
normalized to a 0-10 scale (not the classical 0-60 rupas — simpler for
downstream consumers; multiply by 6 if you want classical units).

## What this is NOT

This is not a redundant duplicate of bhava_judge's composite_score.
That score answers "will the bhava DELIVER given chart-time alignments";
Bhava Bala answers "what is the bhava's RAW STRENGTH on the static frame".
They're complementary: a strong bhava with weak lord delivers slowly; a
weak bhava with strong lord delivers spasmodically.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart


# ─── House categories ───────────────────────────────────────────────


_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({5, 9})
_UPACHAYAS: Final[frozenset[int]] = frozenset({3, 6, 10, 11})
_DUSHTANAS: Final[frozenset[int]] = frozenset({6, 8, 12})

_NATURAL_BENEFICS: Final[frozenset[str]] = frozenset(
    {"Jupiter", "Venus", "Mercury", "Moon"}
)
_NATURAL_MALEFICS: Final[frozenset[str]] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)

# Sign-lord table (duplicated to avoid import cycle)
_SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


@dataclass(frozen=True)
class BhavaStrengthReport:
    """Per-bhava intrinsic strength."""
    bhava: int
    lord: str                          # planet ruling this bhava's sign
    bhavadhipati_bala: float           # 0-3 (lord's dignity-based score)
    drishti_bala: float                # -3..+3 (net benefic minus malefic aspects)
    dig_bala: float                    # -1..+1 (house-category bonus/penalty)
    composite_bhava_bala: float        # 0-10 normalized
    strength_label: str                # very strong / strong / average / weak / very weak


def _bhava_sign(chart: Chart, bhava: int) -> int:
    """Sign of the Nth bhava (whole-sign cusp from asc_sign)."""
    return ((chart.asc_sign - 1 + bhava - 1) % 12) + 1


def _planets_in_house(chart: Chart, house: int) -> tuple[str, ...]:
    return tuple(p for p, h in chart.planet_houses.items() if h == house)


def _planets_aspecting_house(
    chart: Chart, target_house: int,
) -> tuple[tuple[str, str], ...]:
    """Return ((planet, kind), ...) where kind is 'opposition' / '5th' / '9th'/etc.

    Uses project's locked whole-sign drishti:
      - Every planet aspects the 7th from itself (opposition)
      - Jupiter additionally aspects 5th + 9th
      - Mars additionally aspects 4th + 8th
      - Saturn additionally aspects 3rd + 10th
      - Rahu/Ketu Jupiter-style 5th + 9th (modern Sukra Nadi convention)
    """
    out: list[tuple[str, str]] = []
    for p, h in chart.planet_houses.items():
        distance = ((target_house - h) % 12) + 1
        if distance == 7:
            out.append((p, "opposition"))
            continue
        if p == "Jupiter" and distance in (5, 9):
            out.append((p, f"{distance}th"))
        elif p == "Mars" and distance in (4, 8):
            out.append((p, f"{distance}th"))
        elif p == "Saturn" and distance in (3, 10):
            out.append((p, f"{distance}th"))
        elif p in ("Rahu", "Ketu") and distance in (5, 9):
            out.append((p, f"{distance}th"))
    return tuple(out)


def _bhavadhipati_score(
    lord: str, chart: Chart,
) -> float:
    """Lord's contribution to its bhava — 0..3 scale.

    Uses dignity + Kendra/Trikona placement as cheap proxies for the
    full classical Sthana-bala. Returns 0..3.
    """
    from app.core.dignity import is_debilitated, is_exalted, is_own_sign

    sign = chart.planet_signs.get(lord)
    house = chart.planet_houses.get(lord)
    if sign is None or house is None:
        return 1.0  # neutral if missing data

    score = 1.0  # baseline

    # Dignity contribution
    if is_exalted(lord, sign):
        score += 1.5
    elif is_own_sign(lord, sign):
        score += 1.0
    elif is_debilitated(lord, sign):
        score -= 1.0

    # Placement contribution
    if house in _KENDRAS or house in _TRIKONAS:
        score += 0.5
    elif house in _DUSHTANAS:
        score -= 0.5

    return max(0.0, min(3.0, score))


def _drishti_balance(chart: Chart, bhava: int) -> tuple[float, int, int]:
    """Net (benefic - malefic) aspectual rupas on the bhava cusp.

    Plus planets IN the bhava count as conjunctive aspects.
    Each aspecting benefic = +0.5; each malefic = -0.5. Range typically
    -3..+3 across 7 visible grahas.
    """
    aspects = _planets_aspecting_house(chart, bhava)
    in_bhava = _planets_in_house(chart, bhava)
    bal = 0.0
    n_ben = 0
    n_mal = 0
    for p, _kind in aspects:
        if p in _NATURAL_BENEFICS:
            bal += 0.5
            n_ben += 1
        elif p in _NATURAL_MALEFICS:
            bal -= 0.5
            n_mal += 1
    for p in in_bhava:
        if p in _NATURAL_BENEFICS:
            bal += 0.75  # occupancy weighs more than aspect
            n_ben += 1
        elif p in _NATURAL_MALEFICS:
            bal -= 0.75
            n_mal += 1
    return (max(-3.0, min(3.0, bal)), n_ben, n_mal)


def _digbala_for_bhava(bhava: int) -> float:
    """House-category-based directional bonus."""
    score = 0.0
    if bhava in _KENDRAS:
        score += 1.0
    if bhava in _TRIKONAS:
        score += 0.5
    if bhava in _UPACHAYAS:
        score += 0.3
    if bhava in _DUSHTANAS:
        score -= 0.5
    return max(-1.0, min(1.0, score))


def _classify_composite(composite: float) -> str:
    """Map composite (0..10) to a strength label."""
    if composite >= 7.5:
        return "very strong"
    if composite >= 6.0:
        return "strong"
    if composite >= 4.5:
        return "average"
    if composite >= 3.0:
        return "weak"
    return "very weak"


def compute_bhava_bala_for(
    chart: Chart, bhava: int,
) -> BhavaStrengthReport:
    """Compute Bhava Bala for one bhava."""
    if not 1 <= bhava <= 12:
        raise ValueError(f"bhava must be 1..12, got {bhava}")
    sign = _bhava_sign(chart, bhava)
    lord = _SIGN_LORDS[sign]
    bd_bala = _bhavadhipati_score(lord, chart)
    drishti_bal, _n_ben, _n_mal = _drishti_balance(chart, bhava)
    dig = _digbala_for_bhava(bhava)
    # Composite on 0..10: weighted sum of the 3 components
    # bhavadhipati 0..3 (weight ~3.3) → contributes 0..10
    # drishti -3..+3 (weight ~1.0) → contributes -3..+3
    # dig -1..+1 (weight ~1.0) → contributes -1..+1
    # Normalize to 0..10 with bhavadhipati as dominant
    composite = (bd_bala * 2.5) + drishti_bal + dig
    composite = max(0.0, min(10.0, composite + 2.0))  # +2 floor so most non-zero
    return BhavaStrengthReport(
        bhava=bhava, lord=lord,
        bhavadhipati_bala=round(bd_bala, 3),
        drishti_bala=round(drishti_bal, 3),
        dig_bala=round(dig, 3),
        composite_bhava_bala=round(composite, 3),
        strength_label=_classify_composite(composite),
    )


def compute_bhava_bala(chart: Chart) -> dict[int, BhavaStrengthReport]:
    """Compute Bhava Bala for all 12 bhavas."""
    return {b: compute_bhava_bala_for(chart, b) for b in range(1, 13)}


def format_bhava_bala(reports: Mapping[int, BhavaStrengthReport]) -> str:
    """Render Bhava Bala summary as text."""
    lines = ["=== BHAVA BALA (intrinsic strength) ==="]
    lines.append(f"  {'Bhv':<4} {'Lord':<8} {'BhAdhi':>6} {'Drishti':>8} {'Dig':>5} {'Total':>6}  Label")
    lines.append("  " + "-" * 60)
    for b in range(1, 13):
        r = reports[b]
        lines.append(
            f"  {b:<4} {r.lord:<8} {r.bhavadhipati_bala:>6.2f} "
            f"{r.drishti_bala:>+8.2f} {r.dig_bala:>+5.2f} "
            f"{r.composite_bhava_bala:>6.2f}  {r.strength_label}"
        )
    return "\n".join(lines)
