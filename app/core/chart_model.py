"""Chart dataclass — universal input contract for the lens framework.

Every downstream phase (yogas, Shadbala, Bhava Judge, Gochara, Reading
Composer) consumes a ``Chart``. It denormalises the dossier's wide row
into the structure-of-arrays shape engines naturally want.

The constructor accepts either:
* a dict (e.g. a row from ``person_dossier.parquet`` converted to dict)
* explicit kwargs (for test fixtures and synthetic charts)

Why dataclass-frozen: prevents downstream mutation surprises (a Phase 6
caller cannot accidentally mutate the natal positions while iterating).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Mapping

_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu",
)


@dataclass(frozen=True)
class Chart:
    """Immutable natal-chart snapshot used by all lens-framework engines.

    ## Required planets

    A full reading requires all 9 grahas (Sun, Moon, Mars, Mercury,
    Jupiter, Venus, Saturn, Rahu, Ketu) to have entries in
    ``planet_signs``, ``planet_houses`` and ``planet_lons``. Engines
    that depend on luminaries (Shadbala, Kemadruma, Sunapha/Anapha,
    Sade Sati, Gajakesari) will either crash or silently degrade
    if Sun/Moon are missing. Use ``Chart.validate_complete()`` to
    fail-fast on partial input.

    ## Retrograde contract (audit-fix flag)

    ``planet_retrograde`` defaults to empty when not provided. Per
    Vedic convention, Rahu/Ketu are ALWAYS retrograde; visible planets
    are typically direct. ``from_dossier_row`` applies these defaults
    because ``person_dossier.parquet`` does not currently persist a
    per-planet retrograde column. Engines that need true retrograde
    state should explicitly query this field; do not assume.

    Attributes:
        asc_sign: Lagna sign (1..12).
        asc_lon: Lagna sidereal longitude (0..360 degrees).
        planet_signs: planet → sign (1..12).
        planet_houses: planet → natal house from Lagna (1..12).
        planet_lons: planet → sidereal longitude (0..360 degrees).
        planet_retrograde: planet → True/False (see Retrograde contract
            above; Rahu/Ketu defaulted to True, visible to False).
        person_id: optional chart identifier for cross-engine logging.
    """
    asc_sign: int
    asc_lon: float
    planet_signs: Mapping[str, int]
    planet_houses: Mapping[str, int]
    planet_lons: Mapping[str, float]
    planet_retrograde: Mapping[str, bool] = field(default_factory=dict)
    person_id: str | None = None

    def validate_complete(self) -> None:
        """Fail-fast check that all 9 grahas have full position data.

        Use this at the entry point of a full-reading pipeline to surface
        partial-input bugs early. Engines that selectively skip planets
        (yoga detectors) tolerate partials; full Shadbala / bhava judge
        does not.

        Raises:
            ValueError: with a specific message naming the missing grahas
                AND the missing field (sign / house / lon).
        """
        missing: list[str] = []
        for g in _GRAHAS:
            for field_name, mapping in (
                ("sign", self.planet_signs),
                ("house", self.planet_houses),
                ("lon", self.planet_lons),
            ):
                if g not in mapping or mapping[g] is None:
                    missing.append(f"{g}.{field_name}")
        if missing:
            raise ValueError(
                f"Chart incomplete — missing position data: "
                f"{', '.join(missing[:10])}"
                + (f" (+{len(missing) - 10} more)" if len(missing) > 10 else "")
            )

    @classmethod
    def from_dossier_row(cls, row: Mapping) -> "Chart":
        """Build a Chart from a person_dossier.parquet row (or dict).

        Reads ``asc_lon``, ``asc_sign`` and per-graha ``{p}_lon``,
        ``{p}_sign``, ``{p}_natal_house`` keys; tolerates missing
        retrograde info (defaults to False for visible planets, True
        for nodes per Vedic convention).
        """
        signs: dict[str, int] = {}
        houses: dict[str, int] = {}
        lons: dict[str, float] = {}
        retrograde: dict[str, bool] = {}
        for g in _GRAHAS:
            prefix = g.lower()
            lon_key = f"{prefix}_lon"
            sign_key = f"{prefix}_sign"
            house_key = f"{prefix}_natal_house"
            if lon_key in row and row[lon_key] is not None:
                lons[g] = float(row[lon_key])
            if sign_key in row and row[sign_key] is not None:
                signs[g] = int(row[sign_key])
            if house_key in row and row[house_key] is not None:
                houses[g] = int(row[house_key])
            # Nodes default retrograde; visible default not.
            retrograde[g] = bool(row.get(f"{prefix}_is_retrograde",
                                         g in {"Rahu", "Ketu"}))
        return cls(
            asc_sign=int(row["asc_sign"]),
            asc_lon=float(row["asc_lon"]),
            planet_signs=signs,
            planet_houses=houses,
            planet_lons=lons,
            planet_retrograde=retrograde,
            person_id=row.get("person_id"),
        )

    def planets_in_house(self, house: int) -> tuple[str, ...]:
        """Sorted tuple of planet names occupying the given natal house."""
        return tuple(sorted(p for p, h in self.planet_houses.items() if h == house))

    def planets_in_sign(self, sign: int) -> tuple[str, ...]:
        """Sorted tuple of planets in the given sign (1..12)."""
        return tuple(sorted(p for p, s in self.planet_signs.items() if s == sign))

    def house_of(self, planet: str) -> int | None:
        """Natal house of a planet, or None if absent from chart."""
        return self.planet_houses.get(planet)

    def sign_of(self, planet: str) -> int | None:
        """Sign of a planet, or None if absent."""
        return self.planet_signs.get(planet)
