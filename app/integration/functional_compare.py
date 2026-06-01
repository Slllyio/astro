"""Cross-engine functional benefic/malefic comparator.

Both Track A (``app.reading.computations.functional_nature``) and Track B
(``app.core.functional_roles``) classify each planet's functional nature
for a given Lagna (D-7 in Track A's doctrine lockfile). They use different
output schemas — Track A returns ``dict[planet, Finding]`` with a
``direction`` field (positive/negative/neutral); Track B returns
``dict[planet, FunctionalRoles]`` with boolean flags. This module
normalises both to a common label space and produces a per-planet
agreement matrix.

Public surface
--------------
- ``compare_functional_roles(lagna_sign)`` → ``FunctionalComparisonReport``
- ``FunctionalComparisonReport`` — Pydantic envelope with per-planet diff
  and aggregate verdict.

Methodology
-----------
Track A and Track B classify functional nature using different
doctrine systems:

- **Track A** (D-7 lockfile, PVR Narasimha Rao): three-way classification
  (functional benefic / malefic / neutral) per planet per Lagna. Includes
  Rahu and Ketu as shadow planets (typically neutral).
- **Track B**: flag-set classification (is_yogakaraka, is_maraka,
  is_badhakesh, is_functional_benefic, is_functional_malefic,
  is_lagna_lord). Only the 7 classical planets are inventoried (no
  Rahu/Ketu).

The comparator maps Track B's flags onto Track A's three-way label space:

- ``is_functional_benefic=True`` → ``"positive"``
- ``is_functional_malefic=True`` → ``"negative"``
- ``is_yogakaraka=True`` → ``"positive"`` (overrides above)
- ``is_lagna_lord=True`` with no other flag → ``"positive"`` (lagna lord
  defaults to functional benefic in classical doctrine)
- Otherwise → ``"neutral"``

Planets present in Track A but absent in Track B (Rahu, Ketu) are reported
as agreement=None.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.functional_roles import FunctionalRoles, functional_roles
from app.reading.computations.functional_nature import compute_functional_nature

# Direction labels used by Track A.
_DIRECTION = Literal["positive", "negative", "neutral"]

# All nine Vedic planets used by Track A.
_ALL_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TrackBRolesView(BaseModel):
    """Snapshot of Track B's ``FunctionalRoles`` flags, JSON-friendly."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    houses_ruled: tuple[int, ...]
    is_lagna_lord: bool
    is_yogakaraka: bool
    is_maraka: bool
    is_badhakesh: bool
    is_functional_benefic: bool
    is_functional_malefic: bool

    @classmethod
    def from_roles(cls, roles: FunctionalRoles) -> TrackBRolesView:
        return cls(
            houses_ruled=tuple(roles.houses_ruled),
            is_lagna_lord=roles.is_lagna_lord,
            is_yogakaraka=roles.is_yogakaraka,
            is_maraka=roles.is_maraka,
            is_badhakesh=roles.is_badhakesh,
            is_functional_benefic=roles.is_functional_benefic,
            is_functional_malefic=roles.is_functional_malefic,
        )

    def to_direction(self) -> str:
        """Project the flag-set down to Track A's positive/negative/neutral
        label. Yogakaraka overrides benefic/malefic; lagna lord without
        other flags is treated as positive (classical convention)."""
        if self.is_yogakaraka:
            return "positive"
        if self.is_functional_benefic and not self.is_functional_malefic:
            return "positive"
        if self.is_functional_malefic and not self.is_functional_benefic:
            return "negative"
        if self.is_lagna_lord and not (
            self.is_functional_malefic or self.is_maraka or self.is_badhakesh
        ):
            return "positive"
        return "neutral"


class PlanetFunctionalDiff(BaseModel):
    """Per-planet agreement record between the two engines.

    ``agrees`` is None when the planet is present in one engine but not
    the other (Rahu/Ketu, which Track B omits). Otherwise True if the
    projected Track-B direction equals Track-A's direction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    planet: str
    track_a_direction: str | None  # positive/negative/neutral, or None if absent
    track_a_verdict: str | None
    track_b_roles: TrackBRolesView | None
    track_b_projected_direction: str | None
    agrees: bool | None
    disagreement_note: str | None = None


class FunctionalComparisonReport(BaseModel):
    """Aggregate report from ``compare_functional_roles``.

    Doctrine context: Track A locks D-7 to PVR Narasimha Rao
    (3-way classification per Lagna). Track B uses a flag-set system that
    includes yogakaraka/maraka/badhakesh as orthogonal labels."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lagna_sign: int = Field(ge=1, le=12)
    track_a_engine: str = "app.reading.computations.functional_nature (D-7)"
    track_b_engine: str = "app.core.functional_roles"

    per_planet: list[PlanetFunctionalDiff]

    planets_only_in_a: list[str]
    planets_only_in_b: list[str]
    planets_in_both: list[str]

    agreement_count: int  # planets where projected directions match
    disagreement_count: int
    full_agreement_among_classical_7: bool

    verdict_summary: str


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def compare_functional_roles(lagna_sign: int) -> FunctionalComparisonReport:
    """Diff Track A and Track B functional nature for ``lagna_sign``.

    Both engines are deterministic given lagna_sign alone (no chart
    positions needed), so this comparator runs in microseconds.

    Parameters
    ----------
    lagna_sign
        1..12, the natal Lagna sign.

    Returns
    -------
    FunctionalComparisonReport
        Per-planet agreement + aggregate verdict.
    """
    a_results = compute_functional_nature(lagna_sign)
    b_results = functional_roles(lagna_sign)

    planets_a = set(a_results.keys())
    planets_b = set(b_results.keys())
    only_in_a = sorted(planets_a - planets_b)
    only_in_b = sorted(planets_b - planets_a)
    in_both = sorted(planets_a & planets_b)

    per_planet: list[PlanetFunctionalDiff] = []
    agreement_count = 0
    disagreement_count = 0
    classical_7 = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    full_classical_agreement = True

    for planet in _ALL_PLANETS:
        a_finding = a_results.get(planet)
        b_roles = b_results.get(planet)

        a_direction = a_finding.direction if a_finding is not None else None
        a_verdict = a_finding.verdict if a_finding is not None else None
        b_view = TrackBRolesView.from_roles(b_roles) if b_roles is not None else None
        b_projected = b_view.to_direction() if b_view is not None else None

        if a_direction is None or b_projected is None:
            agrees: bool | None = None
            note = "absent in " + ("Track B" if b_projected is None else "Track A")
        else:
            agrees = a_direction == b_projected
            note = None if agrees else (
                f"Track A says {a_direction}; Track B flags project to {b_projected}"
            )
            if agrees:
                agreement_count += 1
            else:
                disagreement_count += 1
                if planet in classical_7:
                    full_classical_agreement = False

        per_planet.append(PlanetFunctionalDiff(
            planet=planet,
            track_a_direction=a_direction,
            track_a_verdict=a_verdict,
            track_b_roles=b_view,
            track_b_projected_direction=b_projected,
            agrees=agrees,
            disagreement_note=note,
        ))

    if full_classical_agreement and not disagreement_count:
        summary = f"FULL AGREEMENT on classical 7 planets (Rahu/Ketu omitted by Track B)"
    elif disagreement_count == 0:
        summary = "all planets agree where comparable"
    else:
        summary = (
            f"{disagreement_count} planet disagreement(s) "
            f"among classical 7: doctrine divergence on D-7 functional nature"
        )

    return FunctionalComparisonReport(
        lagna_sign=lagna_sign,
        per_planet=per_planet,
        planets_only_in_a=only_in_a,
        planets_only_in_b=only_in_b,
        planets_in_both=in_both,
        agreement_count=agreement_count,
        disagreement_count=disagreement_count,
        full_agreement_among_classical_7=full_classical_agreement,
        verdict_summary=summary,
    )
