"""Chara Karakas — the 7 Jaimini soul/relationship significators (strict 7-karaka).

The chara ("movable") karakas rank the seven visible planets by degree-within-sign, descending:
the highest is the **Atmakaraka (AK)** — the significator of the soul itself — then Amatyakaraka
(mind/counsel), Bhratrukaraka, Matrukaraka, Putrakaraka, Gnatikaraka, and Darakaraka (spouse).

Strict 7-karaka scheme (CLAUDE.md locked decision): Rahu/Ketu are chayagrahas and CANNOT signify
the soul or any karaka role — AK can NEVER be a node. The 8-karaka Rahu-inverted extension is
doctrinally rejected. AK here is identical by construction to ``special_points.atmakaraka`` (same
``lon % 30.0`` keying over the same ``_SEVEN``).

This is a pure primitive; it is consumed by the report-only ``judges/soul_reading.py`` surface and
never feeds the D1 verdict path.
"""
from __future__ import annotations

from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart

_SEVEN: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

#: The 7 chara-karaka roles in rank order (highest degree-in-sign first).
CHARA_KARAKA_ROLES: Final[tuple[str, ...]] = ("AK", "AmK", "BK", "MK", "PK", "GK", "DK")

_ROLE_NAMES: Final[dict[str, str]] = {
    "AK": "Atmakaraka (soul)",
    "AmK": "Amatyakaraka (mind / counsel)",
    "BK": "Bhratrukaraka (siblings)",
    "MK": "Matrukaraka (mother)",
    "PK": "Putrakaraka (children)",
    "GK": "Gnatikaraka (kin)",
    "DK": "Darakaraka (spouse)",
}


def _ranked(chart: RamanChart) -> list[str]:
    """The present visible planets, highest degree-within-sign first. Ties break by ``_SEVEN``
    order (ascending), so the rank-1 planet matches ``special_points.atmakaraka``'s ``max``."""
    present = [p for p in _SEVEN if p in chart.planets]
    return sorted(present, key=lambda p: (-(chart.planets[p].lon % 30.0), _SEVEN.index(p)))


def chara_karakas(chart: RamanChart) -> dict[str, str]:
    """Role → planet for the strict 7-karaka Jaimini scheme.

    Ranked by degree-within-sign descending (AK = highest). On a sparse chart carrying fewer than
    the seven visible planets, only the filled roles appear — unfilled roles are omitted
    (None-safe). Rahu/Ketu are never assigned (excluded from ``_SEVEN``)."""
    return {CHARA_KARAKA_ROLES[i]: p for i, p in enumerate(_ranked(chart))
            if i < len(CHARA_KARAKA_ROLES)}


def karaka_planet(chart: RamanChart, role: str) -> Optional[str]:
    """The planet holding ``role`` (e.g. ``"AK"``, ``"DK"``), or ``None`` if the role is unfilled
    (sparse chart) or unknown."""
    return chara_karakas(chart).get(role)


def role_name(role: str) -> str:
    """Human-readable name for a role code, e.g. ``"AK"`` → ``"Atmakaraka (soul)"``."""
    return _ROLE_NAMES.get(role, role)
