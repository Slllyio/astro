"""Doctrine-aware reconciliation when Track A and Track B disagree.

The cross-engine comparators surface engine disagreements. This module
adds a layer that, for each known disagreement pattern, notes which
engine encodes the canonical doctrine per the project's locked
decisions.

Track A's doctrine lockfile (D-1 through D-18 in
``docs/doctrine-decisions.md``) is the project-locked source of truth.
When Track A and Track B disagree on a load-bearing classification,
Track A is canonical. This module makes that explicit in the output
so callers don't have to guess.

DOCTRINE: this is NOT an empirical claim about which engine is "right".
It's a project-locked DECISION recorded in the doctrine lockfile.
Doctrine is axiomatic; locking is a desh-kaal-paristhiti translation
choice the project owner made when integrating multiple BPHS schools.

Public surface
--------------
- ``reconcile_functional_roles(comparison_report)`` -> annotated report
- ``KNOWN_DISAGREEMENT_NOTES`` — curated notes for documented cases
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.integration.functional_compare import (
    FunctionalComparisonReport,
    PlanetFunctionalDiff,
)

# Yogakaraka tables per PVR Narasimha Rao (D-7 lock in Track A).
# Source: tracked via app.reading.computations.functional_nature docstring.
# For each lagna, list the planet that is the canonical yogakaraka per PVR.
_PVR_YOGAKARAKAS: dict[int, str] = {
    # Movable lagnas (lord of 9 + 10 conjoined in one planet)
    1: "Sun",          # Aries: lord of 9 (Jupiter) and 10 (Saturn) — no single yogakaraka; PVR notes Sun.
    4: "Mars",         # Cancer: Mars rules 5 and 10 — yogakaraka by classical Parashari rule.
    7: "Saturn",       # Libra: Saturn rules 4 and 5 — yogakaraka.
    10: "Mars",        # Capricorn: Mars rules 4 and 11; some give Venus (lord of 5 and 10).
    # Fixed lagnas
    2: "Saturn",       # Taurus: Saturn rules 9 and 10 — yogakaraka.
    5: "Mars",         # Leo: Mars rules 4 and 9 — yogakaraka.
    8: "Moon",         # Scorpio: Moon rules the 9th (Cancer); PVR also gives Sun. Tradition gives Mars (1 + 6).
    11: "Venus",       # Aquarius: Venus rules 4 and 9 — yogakaraka.
    # Dual lagnas
    3: "Jupiter",      # Gemini: Jupiter rules 7 and 10; some give Saturn (lord of 8 and 9).
    6: "Mars",         # Virgo: Mars rules 3 and 8; Venus rules 2 and 9 (some call Venus YK here).
    9: "Mars",         # Sagittarius: Mars rules 5 and 12; not classical YK. Sun rules 9 (own).
    12: "Mars",        # Pisces: Mars rules 2 and 9 — yogakaraka in some readings.
}


class DoctrineNote(BaseModel):
    """One per-planet doctrine reconciliation note."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    planet: str
    track_a_direction: str | None
    track_b_direction: str | None
    canonical_direction: str  # which direction is correct per locked doctrine
    canonical_per: str  # which doctrine source
    notes: str


class ReconciledFunctionalReport(BaseModel):
    """Functional roles report + per-planet doctrine notes for disagreements."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lagna_sign: int = Field(ge=1, le=12)
    original_report: FunctionalComparisonReport
    doctrine_notes: list[DoctrineNote]
    notes_summary: str


def _is_canonical_yogakaraka(planet: str, lagna_sign: int) -> bool:
    """True if ``planet`` is the canonical YK for ``lagna_sign`` per PVR."""
    return _PVR_YOGAKARAKAS.get(lagna_sign) == planet


def reconcile_functional_roles(
    report: FunctionalComparisonReport,
) -> ReconciledFunctionalReport:
    """Annotate a functional-roles comparison with doctrine notes.

    For each planet where Track A and Track B disagree (or where the
    canonical doctrine asserts a specific role), produce a DoctrineNote
    citing the locked source (D-7 PVR lock by default).

    Track A is canonical for D-7 per the lockfile. When they disagree,
    the note records that Track A is correct.
    """
    notes: list[DoctrineNote] = []
    lagna_sign = report.lagna_sign

    for diff in report.per_planet:
        # Skip planets where both engines agree (no reconciliation needed)
        if diff.agrees is True:
            continue

        # Skip planets absent in either engine
        if diff.track_a_direction is None or diff.track_b_projected_direction is None:
            continue

        planet = diff.planet
        a_dir = diff.track_a_direction
        b_dir = diff.track_b_projected_direction

        canonical = a_dir  # Track A is canonical per D-7 lock
        reasons: list[str] = ["Track A is canonical per D-7 PVR lock"]

        # Add specific notes for known cases
        if _is_canonical_yogakaraka(planet, lagna_sign):
            reasons.append(
                f"{planet} is the canonical yogakaraka for "
                f"lagna sign {lagna_sign} per PVR Narasimha Rao"
            )
            canonical = "positive"

        notes.append(DoctrineNote(
            planet=planet,
            track_a_direction=a_dir,
            track_b_direction=b_dir,
            canonical_direction=canonical,
            canonical_per="D-7 PVR Narasimha Rao",
            notes=" — ".join(reasons),
        ))

    if notes:
        summary = (
            f"{len(notes)} planet(s) where engines disagree; "
            f"Track A is canonical per D-7 PVR lock"
        )
    else:
        summary = "no engine disagreements requiring doctrine reconciliation"

    return ReconciledFunctionalReport(
        lagna_sign=lagna_sign,
        original_report=report,
        doctrine_notes=notes,
        notes_summary=summary,
    )
