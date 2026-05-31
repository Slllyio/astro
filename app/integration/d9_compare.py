"""D9 Navamsha internal-consistency check.

Track A's pipeline calls ``app.core.ephemeris_engine.calculate_all_charts``
to build the D9 chart embedded in its reading. Track B's
``app.core.shodashavarga.compute_divisional_charts`` is an INDEPENDENT
implementation of the same divisional math. Both should produce
identical D9 signs for each planet.

This comparator anchors on the D9 sign field and surfaces any divergence
between the two Track-B implementations. While both modules live in
Track B, they were developed at different times and could drift —
catching drift before downstream consumers hit it is the point.

(There is no Track-A independent D9 implementation to compare against —
Track A consumes Track B's ephemeris output. This comparator is therefore
a Track-B-internal consistency check labeled "D9" rather than a true
cross-engine diff. Still surfaces real bugs when either implementation
drifts.)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.ephemeris_engine import calculate_divisional_longitude
from app.core.shodashavarga import compute_divisional_charts


_CLASSICAL_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


class PlanetD9Diff(BaseModel):
    """Per-planet D9 sign agreement record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    planet: str
    longitude: float
    d1_sign: int = Field(ge=1, le=12)
    ephemeris_d9_sign: int = Field(ge=1, le=12)
    shodashavarga_d9_sign: int = Field(ge=1, le=12)
    agrees: bool


class D9ComparisonReport(BaseModel):
    """Aggregate D9 internal-consistency output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    impl_a: str = "app.core.ephemeris_engine.calculate_divisional_longitude"
    impl_b: str = "app.core.shodashavarga.compute_divisional_charts"

    per_planet: list[PlanetD9Diff]
    full_agreement: bool
    agreement_count: int
    disagreement_count: int
    verdict_summary: str


def _d9_sign_from_longitude_via_ephemeris(longitude: float) -> int:
    """Compute D9 sign for one planet via ephemeris_engine math."""
    d9_lon = calculate_divisional_longitude(longitude, divisor=9)
    return int(d9_lon // 30) + 1


def compare_d9_signs(reading: dict[str, Any]) -> D9ComparisonReport:
    """Diff D9 signs between Track B's two divisional implementations.

    The reading's chart.planets supplies the D1 longitudes. We then
    compute D9 via both Track B paths and compare per-planet.
    """
    planets = (reading.get("chart") or {}).get("planets") or {}

    # Path A: per-planet via calculate_divisional_longitude.
    a_d9: dict[str, int] = {}
    for planet, body in planets.items():
        if not isinstance(body, dict):
            continue
        lon = body.get("longitude")
        if isinstance(lon, (int, float)):
            a_d9[planet] = _d9_sign_from_longitude_via_ephemeris(float(lon))

    # Path B: bulk via compute_divisional_charts.
    b_divisional = compute_divisional_charts(planets)
    b_d9_block = b_divisional.get("D9_Navamsa") or b_divisional.get("D9") or {}
    b_d9 = {
        planet: int(body["sign"])
        for planet, body in b_d9_block.items()
        if isinstance(body, dict) and "sign" in body
    }

    per_planet: list[PlanetD9Diff] = []
    agreements = 0
    disagreements = 0

    for planet in _CLASSICAL_PLANETS:
        body = planets.get(planet)
        if not isinstance(body, dict):
            continue
        lon = body.get("longitude")
        d1_sign = body.get("sign")
        a_sign = a_d9.get(planet)
        b_sign = b_d9.get(planet)
        if a_sign is None or b_sign is None or lon is None or d1_sign is None:
            continue
        agrees = a_sign == b_sign
        if agrees:
            agreements += 1
        else:
            disagreements += 1
        per_planet.append(PlanetD9Diff(
            planet=planet,
            longitude=float(lon),
            d1_sign=int(d1_sign),
            ephemeris_d9_sign=a_sign,
            shodashavarga_d9_sign=b_sign,
            agrees=agrees,
        ))

    full_agreement = disagreements == 0 and agreements > 0

    summary = (
        f"FULL AGREEMENT on D9 signs ({agreements}/{len(per_planet)} planets)"
        if full_agreement
        else f"agreements={agreements}, disagreements={disagreements}"
    )

    return D9ComparisonReport(
        per_planet=per_planet,
        full_agreement=full_agreement,
        agreement_count=agreements,
        disagreement_count=disagreements,
        verdict_summary=summary,
    )
