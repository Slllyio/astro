"""Vimsopaka Bala — composite multi-varga dignity score (Gap G).

BPHS Ch.7 + Phaladeepika Ch.5. Vimsopaka ("20-point") is the
weighted-sum dignity strength across multiple divisional charts —
the integrative metric Raman insisted on for serious chart reading.

Where Shadbala measures six kinds of planetary strength on a single
chart (Sthana + Dig + Kala + Cheshta + Naisargika + Drik), Vimsopaka
asks the orthogonal question: **how strong is this planet's dignity
profile across multiple vargas simultaneously?** A planet that's
exalted in D1 but debilitated in D9 has weaker Vimsopaka than one
own-sign in BOTH D1 and D9.

## Three Vimsopaka schemes

### Saptavargaja (7-varga)
Used in basic readings. Vargas: D1, D2, D3, D7, D9, D12, D30.
Weights (total 20): 5, 2, 3, 2.5, 4.5, 2, 1.

### Dashavargaja (10-varga)
Used in marriage + career readings. Adds D10, D16, D60 to Saptavargaja.
Weights (total 20): 3, 1.5, 1.5, 1.5, 1.5, 3, 1.5, 1, 1, 5.

### Shodashavargaja (16-varga)
Full Vimsopaka used in deep dharmic readings. All 16 vargas with
classical weights summing to 20.

## Dignity values (per varga, before weighting)

Each planet in each varga gets a raw dignity value 0..20:

  - Exalted / Own sign: 20
  - Mooltrikona: 18
  - Friend's sign: 15
  - Neutral: 10
  - Enemy: 7
  - Debilitated: 2

These are then multiplied by the varga's weight and summed across all
included vargas.

## Output interpretation

Vimsopaka Bala result (rupas, 0-20 scale):
- ≥18 STRONG — planet delivers fully
- 15-17 GOOD — favorable
- 10-14 AVERAGE — neutral
- 7-9 WEAK — diluted delivery
- <7 VERY WEAK — significations fail

## Why this matters

A bhava judge that only reads D1 dignity treats "Mercury in own Virgo"
as universally good. Vimsopaka catches the case where the SAME Mercury
is debilitated in D9 (Pisces navamsha) and broken in D60 — the D1
goodness is largely illusory.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart
from app.core.dignity import is_debilitated, is_exalted, is_own_sign


@dataclass(frozen=True)
class VimsopakaReport:
    """Vimsopaka result for one planet across one varga scheme."""
    planet: str
    scheme: str                  # "saptavargaja" | "dashavargaja" | "shodashavargaja"
    composite_rupas: float       # 0..20
    strength_label: str          # "VERY WEAK" / "WEAK" / "AVERAGE" / "GOOD" / "STRONG"
    per_varga_dignity: Mapping[str, float]   # varga_name -> raw dignity (0..20)


# ─── Scheme weights (BPHS Ch.7, sum = 20) ───────────────────────────


_SAPTAVARGAJA_WEIGHTS: Final[Mapping[str, float]] = {
    "D1":  5.0,    # Rashi
    "D2":  2.0,    # Hora
    "D3":  3.0,    # Drekkana
    "D7":  2.5,    # Saptamsa
    "D9":  4.5,    # Navamsa — heaviest
    "D12": 2.0,    # Dvadasamsa
    "D30": 1.0,    # Trimsamsa
}

_DASHAVARGAJA_WEIGHTS: Final[Mapping[str, float]] = {
    "D1":  3.0,
    "D2":  1.5,
    "D3":  1.5,
    "D7":  1.5,
    "D9":  1.5,
    "D10": 1.5,    # Dasamsa
    "D12": 1.5,
    "D16": 1.5,    # Shodasamsa
    "D30": 1.5,
    "D60": 5.0,    # Shashtiamsa — heaviest in 10-varga
}

_SHODASHAVARGAJA_WEIGHTS: Final[Mapping[str, float]] = {
    "D1":  3.5,
    "D2":  1.0,
    "D3":  1.0,
    "D4":  0.5,
    "D7":  0.5,
    "D9":  3.0,
    "D10": 0.5,
    "D12": 0.5,
    "D16": 2.0,
    "D20": 0.5,
    "D24": 0.5,
    "D27": 0.5,
    "D30": 1.0,
    "D40": 0.5,
    "D45": 0.5,
    "D60": 4.0,    # Shashtiamsa — heaviest in 16-varga
}

_SCHEME_WEIGHTS: Final[Mapping[str, Mapping[str, float]]] = {
    "saptavargaja": _SAPTAVARGAJA_WEIGHTS,
    "dashavargaja": _DASHAVARGAJA_WEIGHTS,
    "shodashavargaja": _SHODASHAVARGAJA_WEIGHTS,
}


# Dignity → raw value (0..20). Sum × weight = component contribution.
_DIGNITY_VALUE: Final[Mapping[str, float]] = {
    "exalted":     20.0,
    "own":         20.0,
    "mooltrikona": 18.0,
    "friend":      15.0,
    "neutral":     10.0,
    "enemy":       7.0,
    "debilitated": 2.0,
}


def _dignity_label_for_planet_in_sign(planet: str, sign: int) -> str:
    """Reduce planet+sign to one of the 7 dignity labels.

    Simplified rule set (full Saptavargaja in dignity.py uses friendship
    matrix; here we use the coarse 5-tier: exalt > own > neutral > enemy
    > debilitated). Friend/enemy could be expanded later via
    naisargika_relation from dignity.py.
    """
    if is_exalted(planet, sign):
        return "exalted"
    if is_own_sign(planet, sign):
        return "own"
    if is_debilitated(planet, sign):
        return "debilitated"
    # For finer friend/enemy resolution, dignity.naisargika_relation
    # could be used here; default neutral for v1.
    return "neutral"


def _classify(composite: float) -> str:
    """Map composite rupas (0..20) to strength label."""
    if composite >= 18:
        return "STRONG"
    if composite >= 15:
        return "GOOD"
    if composite >= 10:
        return "AVERAGE"
    if composite >= 7:
        return "WEAK"
    return "VERY WEAK"


def vimsopaka_bala(
    planet: str,
    per_varga_sign: Mapping[str, int],
    scheme: str = "saptavargaja",
) -> VimsopakaReport:
    """Compute Vimsopaka Bala for one planet.

    Args:
        planet: name (Sun..Saturn).
        per_varga_sign: mapping of varga name ("D1", "D9", ...) to the
            sign (1..12) the planet occupies in that varga. Caller is
            responsible for computing the divisional sign upstream
            (via app/core/shodashavarga.py).
        scheme: which Vimsopaka scheme to use.

    Returns:
        VimsopakaReport with composite rupas + per-varga dignity values.

    Note: vargas absent from per_varga_sign contribute 0 weighted dignity.
    The caller can choose how much of the scheme to populate.
    """
    if scheme not in _SCHEME_WEIGHTS:
        raise ValueError(
            f"scheme must be one of {list(_SCHEME_WEIGHTS.keys())}, got {scheme}"
        )
    weights = _SCHEME_WEIGHTS[scheme]
    per_varga_dignity: dict[str, float] = {}
    composite = 0.0
    for varga_name, weight in weights.items():
        sign = per_varga_sign.get(varga_name)
        if sign is None:
            continue
        label = _dignity_label_for_planet_in_sign(planet, sign)
        raw_dignity = _DIGNITY_VALUE[label]
        per_varga_dignity[varga_name] = raw_dignity
        # Vimsopaka per-varga contribution = raw_dignity * (weight / 20)
        composite += raw_dignity * (weight / 20.0)
    return VimsopakaReport(
        planet=planet, scheme=scheme,
        composite_rupas=composite,
        strength_label=_classify(composite),
        per_varga_dignity=per_varga_dignity,
    )


def vimsopaka_for_chart(
    chart: Chart,
    per_planet_varga_signs: Mapping[str, Mapping[str, int]] | None = None,
    scheme: str = "saptavargaja",
) -> dict[str, VimsopakaReport]:
    """Compute Vimsopaka for every visible planet in the chart.

    When ``per_planet_varga_signs`` is None, falls back to D1-only —
    composite = D1 dignity × (D1 weight / 20). This is a minimal
    default; the divisional-chart-aware caller should pre-compute the
    per-varga signs and pass them in for a meaningful Vimsopaka.
    """
    visible = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    out: dict[str, VimsopakaReport] = {}
    for p in visible:
        if p not in chart.planet_signs:
            continue
        if per_planet_varga_signs and p in per_planet_varga_signs:
            varga_signs = per_planet_varga_signs[p]
        else:
            # Default: D1 only
            varga_signs = {"D1": chart.planet_signs[p]}
        out[p] = vimsopaka_bala(p, varga_signs, scheme)
    return out
