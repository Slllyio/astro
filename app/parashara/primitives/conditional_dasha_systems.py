"""The count-from-anchor conditional dashas (BPHS ch.46) — seven systems, one shape.

Beyond Ashtottari and Yogini (their own modules), BPHS ch.46 gives a family whose seed rule is the
same shape: "count from <anchor nakshatra> to the Janma Nakshatra, divide by N, the remainder
indicates the Dasa lord." Only the lord sequence, the year table, the anchor, the divisor and the
applicability condition vary — so they are data here, over the shared `nakshatra_dasha` framework.

## The counting convention (pinned, not assumed)

Parashara's "count from A to B" is INCLUSIVE (A is 1). Three of these systems carry worked
examples, and all three confirm inclusive counting exactly:
  * Shodasottari — Rohini -> Venus (BPHS-46:24-26)
  * Panchottari  — Mrigasira -> Mercury (BPHS-46:29-31)
  * Shatabdika   — Mrigasira -> Mars (BPHS-46:32-34)
Chaturashiti-sama's lone example is visibly OCR-corrupted ("The lord of the lit :a Dasa is of
Mars") and computes to Mercury under the same verified rule; three clean confirmations outweigh one
garbled line, so the rule stands and the discrepancy is recorded rather than special-cased.

## Not encoded here
  * **Shastihayani (should be 60y)** — the OCR sloka gives 13+13+13+6x5 = 69, not 60, and its
    example implies Sun=10 not 13. The section is internally inconsistent; encoding either reading
    would be a guess. Deferred until a clean source resolves it (see BPHS_CORPUS_COVERAGE notes).
  * **Kalachakra / Chara / Sthira** — rasi-based, a different machine entirely (not nakshatra-seeded
    lord cycles); their own framework, a later tranche.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.nakshatra_dasha import DashaPeriod, dasha_timeline, total_years

Direction = Literal["from_anchor", "to_anchor"]


@dataclass(frozen=True)
class CountDashaSystem:
    name: str
    lords: tuple[str, ...]
    years: tuple[float, ...]
    anchor: int                 # anchor nakshatra number (Aswini = 1)
    divisor: int                # remainder base (== len(lords))
    direction: Direction        # "from_anchor": count anchor->janma; "to_anchor": count janma->anchor
    total: float                # the system's defining year-total (== sum(years))
    applicability: str          # Parashara's adoption condition, in brief
    source: Citation

    def __post_init__(self) -> None:
        assert len(self.lords) == len(self.years) == self.divisor, f"{self.name}: shape mismatch"
        assert abs(sum(self.years) - self.total) < 1e-9, (
            f"{self.name}: years total {sum(self.years)}, not {self.total}")

    def seed_index(self, janma_nakshatra: int) -> int:
        """0-based index into `lords` of the mahadasha running at birth (inclusive count)."""
        if not 1 <= janma_nakshatra <= 27:
            raise ValueError(f"janma_nakshatra must be 1..27, got {janma_nakshatra}")
        if self.direction == "from_anchor":
            count = (janma_nakshatra - self.anchor) % 27 + 1
        else:  # to_anchor: count from janma up to the anchor
            count = (self.anchor - janma_nakshatra) % 27 + 1
        remainder = count % self.divisor
        return (self.divisor - 1) if remainder == 0 else remainder - 1

    def seed_lord(self, janma_nakshatra: int) -> str:
        return self.lords[self.seed_index(janma_nakshatra)]

    def cycle(self) -> tuple[tuple[str, float], ...]:
        return tuple(zip(self.lords, self.years))

    def timeline(self, janma_nakshatra: int, *,
                 elapsed_fraction: float = 0.0) -> tuple[DashaPeriod, ...]:
        return dasha_timeline(self.cycle(), self.seed_index(janma_nakshatra),
                              elapsed_fraction=elapsed_fraction)


# Nakshatra numbers used as anchors (Aswini = 1).
_PUSHYA, _ANURADHA, _SWATI, _MOOLA, _SRAVANA, _REVATI = 8, 17, 15, 19, 22, 27

SYSTEMS: Final[dict[str, CountDashaSystem]] = {
    s.name: s for s in (
        CountDashaSystem(
            "shodasottari",
            ("Sun", "Mars", "Jupiter", "Saturn", "Ketu", "Moon", "Mercury", "Venus"),
            (11, 12, 13, 14, 15, 16, 17, 18), _PUSHYA, 8, "from_anchor", 116,
            "Lagna in the Moon's Hora with Krishna Paksha, or the Sun's Hora with Shukla Paksha",
            Citation("BPHS-46", 1910)),
        CountDashaSystem(
            "dwadasottari",
            ("Sun", "Jupiter", "Ketu", "Mercury", "Rahu", "Mars", "Saturn", "Moon"),
            (7, 9, 11, 13, 15, 17, 19, 21), _REVATI, 8, "to_anchor", 112,
            "Ascendant in the Navamsa of Venus",
            Citation("BPHS-46", 1949)),
        CountDashaSystem(
            "panchottari",
            ("Sun", "Mercury", "Saturn", "Mars", "Venus", "Moon", "Jupiter"),
            (12, 13, 14, 15, 16, 17, 18), _ANURADHA, 7, "from_anchor", 105,
            "Ascendant in Cancer and in the Cancer Dwadasamsa",
            Citation("BPHS-46", 1971)),
        CountDashaSystem(
            "shatabdika",
            ("Sun", "Moon", "Venus", "Mercury", "Jupiter", "Mars", "Saturn"),
            (5, 5, 10, 10, 20, 20, 30), _REVATI, 7, "from_anchor", 100,
            "Ascendant is Vargottama (same sign in rasi and navamsa)",
            Citation("BPHS-46", 2474)),
        CountDashaSystem(
            "chaturashiti_sama",
            ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"),
            (12, 12, 12, 12, 12, 12, 12), _SWATI, 7, "from_anchor", 84,
            "the lord of the 10th house is posited in the 10th",
            Citation("BPHS-46", 2507)),
        CountDashaSystem(
            "dwisaptati_sama",
            ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"),
            (9, 9, 9, 9, 9, 9, 9, 9), _MOOLA, 8, "from_anchor", 72,
            "the lord of the Ascendant is in the Ascendant or the 7th",
            Citation("BPHS-46", 2536)),
        CountDashaSystem(
            "shattrimsat_sama",
            ("Moon", "Sun", "Jupiter", "Mars", "Mercury", "Saturn", "Venus", "Rahu"),
            (1, 2, 3, 4, 5, 6, 7, 8), _SRAVANA, 8, "from_anchor", 36,
            "birth during the day with the Ascendant in the Sun's Hora",
            Citation("BPHS-46", 3027)),
    )
}


def system(name: str) -> CountDashaSystem:
    try:
        return SYSTEMS[name]
    except KeyError:
        raise ValueError(f"unknown dasha system {name!r}; have {sorted(SYSTEMS)}") from None


# Fail at import if any table drifts from its name's year-total.
for _s in SYSTEMS.values():
    assert total_years(_s.cycle()) == _s.total, f"{_s.name} total mismatch"
