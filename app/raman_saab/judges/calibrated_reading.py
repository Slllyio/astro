"""Population-calibrated reading overlay — the honest-instrument correction layer (report-only).

WHY THIS EXISTS (Failure Atlas, docs/raman_saab/FAILURE_ATLAS.md): on ordinary charts the engine's
verdicts are DEGENERATE AS STATEMENTS — e.g. 71.6% of all charts read H5-children afflicted-mild,
so "your 5th house is afflicted" carries no information about YOUR chart relative to anyone else's.
This overlay corrects the *instrument's honesty*, not its verdicts: every unchanged Raman reading is
contextualized against the empirical distribution of 16,450 real charts (the committed
`doctrine/data/calibration_table.json`), yielding a population percentile, a rarity note, and — for
the two channels the atlas proved INVERTED (H3 courage, H12 incarceration) — an explicit warning.

WHAT THIS DELIBERATELY DOES NOT DO: it does not adjust any verdict toward real outcomes. The
astrobank program proved (five independent ways) that the readings carry no chart-specific
real-outcome signal; a layer "trained" on outcomes would learn only base rates — a vacuous
correction. Per METHODOLOGY.md governance, astrobank results never tune the engine: the Raman
verdict passes through UNCHANGED, and this overlay is imported by NOTHING in the verdict path
(VERDICT-AUTHORITY INVARIANT — the golden ratchet is untouched by construction).

Provenance: every calibration field is tagged EMPIRICAL_ASTRODATABANK — explicitly not Raman.

Usage:
    from app.raman_saab.judges.calibrated_reading import build_calibrated_reading
    reading = build_calibrated_reading(chart, 5)
    for e in reading.entries:
        print(e.signification, e.verdict, e.degree, f"p{e.favourability_percentile:.0%}", e.note)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges import house_template as ht

CalibrationProvenance = Literal["EMPIRICAL_ASTRODATABANK"]

_TABLE_PATH: Final[Path] = Path(__file__).resolve().parents[1] / "doctrine" / "calibration_table.json"

#: channels the Failure Atlas classified INVERTED (real cases read in the WRONG direction).
_INVERTED: Final[frozenset[str]] = frozenset({"H3_courage", "H12_incarceration"})

_LEVEL_INDEX: Final[dict[tuple[str, str | None], int]] = {
    ("afflicted", "strong"): 0, ("afflicted", "moderate"): 1, ("afflicted", "mild"): 2,
    ("mixed", None): 3,
    ("favourable", "mild"): 4, ("favourable", "moderate"): 5, ("favourable", "strong"): 6,
}


@lru_cache(maxsize=1)
def _table() -> dict:
    return json.loads(_TABLE_PATH.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class CalibratedEntry:
    """One signification: the UNCHANGED Raman verdict + its population context."""
    signification: str
    verdict: str                       # Raman's verdict, untouched
    degree: str
    favourability_percentile: float | None   # share of population reading MORE afflicted (mid-rank)
    band_share: float | None           # how common this exact reading is in the population
    rarity: str                        # "common" (>=25%), "notable" (5-25%), "rare" (<5%)
    inverted_warning: bool             # atlas-proven inverted channel
    note: str
    provenance: CalibrationProvenance = "EMPIRICAL_ASTRODATABANK"


@dataclass(frozen=True)
class CalibratedHouseReading:
    house: int
    entries: tuple[CalibratedEntry, ...]
    population_n: int
    validity_note: str


_VALIDITY: Final[str] = (
    "Percentiles state how this chart's reading compares with 16,450 real charts under Raman's "
    "method — a statement about the METHOD'S OUTPUT, not a validated prediction about life "
    "outcomes (the astrobank program measured no chart-specific real-outcome signal; see "
    "docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md).")


def _calibrate(house: int, sig: str, verdict: str, degree: str) -> CalibratedEntry:
    key = f"H{house}_{sig}"
    row = _table()["table"].get(key)
    inverted = key in _INVERTED
    if row is None or verdict in ("insufficient-evidence", "", None):
        return CalibratedEntry(sig, verdict or "insufficient-evidence", degree or "",
                               None, None, "uncalibrated", inverted,
                               "no calibration row / abstained reading")
    idx = _LEVEL_INDEX.get((verdict, degree if verdict != "mixed" else None))
    if idx is None:
        idx = _LEVEL_INDEX.get((verdict, "moderate"), 3)
    shares = row["shares"]
    below = sum(shares[:idx])
    band = shares[idx]
    pct = below + 0.5 * band            # mid-rank: share of population MORE afflicted than this
    rarity = "common" if band >= 0.25 else "notable" if band >= 0.05 else "rare"
    bits = [f"{band:.0%} of charts share this exact reading",
            f"more favourable than {pct:.0%} of the population"]
    if band >= 0.5:
        bits.append("NEAR-UNIVERSAL reading on this signification — carries little information")
    if inverted:
        bits.append("WARNING: atlas-proven INVERTED channel — real-world cases were read in the "
                    "opposite direction; treat with maximal skepticism")
    return CalibratedEntry(sig, verdict, degree, round(pct, 4), round(band, 4), rarity,
                           inverted, "; ".join(bits))


def build_calibrated_reading(chart: RamanChart, house: int) -> CalibratedHouseReading:
    """Judge the house with the UNCHANGED Raman engine, then attach population calibration."""
    pf = ht.judge_house(chart, house)
    entries = tuple(_calibrate(house, sv.signification, sv.verdict, str(sv.degree))
                    for sv in pf.significations)
    return CalibratedHouseReading(house=house, entries=entries,
                                  population_n=int(_table()["population_n"]),
                                  validity_note=_VALIDITY)
