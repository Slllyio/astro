"""Tier-0 primitive: Jaimini Chara Karaka ranking (D-1 locked: 8-karaka mode).

Doctrine lock — D-1 (``docs/doctrine-decisions.md``)
====================================================

Use the **8-karaka Jaimini scheme** (PVR Narasimha Rao / jagannathahora.io
default). The seven non-nodal planets plus Rahu are ranked by their
sidereal-longitude-within-sign in *descending* order; the highest becomes
the Atmakaraka (AK), the second the Amatya Karaka (AmK), and so on:

    rank 1  -> Atmakaraka      (AK)  the soul
    rank 2  -> Amatyakaraka    (AmK) the minister / counsellor
    rank 3  -> Bhratrikaraka   (BK)  siblings
    rank 4  -> Matrikaraka     (MK)  mother
    rank 5  -> Pitrikaraka     (PK)  father
    rank 6  -> Gnatikaraka     (GK)  paternal kin
    rank 7  -> Darakaraka      (DK)  spouse
    rank 8  -> Strikaraka      (StriK) (only in 8-mode; the additional
                                      Stri / Putra Karaka)

Ketu is excluded entirely. Rahu participates in the 8-mode using its
*inverted* degree-within-sign (``30 - degree``) because Rahu is
conceptually retrograde; the same inversion is applied to any other
planet whose ``is_retrograde`` flag is true (matches jagannathahora.io's
default "use reverse longitudes for retrograde" behaviour).

A 7-karaka mode is offered for callers who need the strict-BPHS form
that drops the Stri Karaka slot.

Public API
==========

    compute_karakas(d1_chart, karaka_mode=8) -> dict[str, Finding]

The returned dict is keyed by canonical karaka name
(``"atmakaraka"`` ... ``"strikaraka"``). Each Finding carries the
assigned planet name in its ``evidence`` lines so downstream sequences
that need machine-readable lookup do not have to re-parse the verdict
string.

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> chart = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> from app.reading.computations.karakas import compute_karakas
    >>> karakas = compute_karakas(chart["d1"])
    >>> karakas["atmakaraka"].verdict
    'Atmakaraka is ...'
"""
from __future__ import annotations

import logging
from typing import Final, Literal

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# 8-karaka roster (D-1 default).
_KARAKA_NAMES_8: Final[tuple[str, ...]] = (
    "atmakaraka",
    "amatyakaraka",
    "bhratrikaraka",
    "matrikaraka",
    "pitrikaraka",
    "gnatikaraka",
    "darakaraka",
    "strikaraka",
)

# 7-karaka roster (classical BPHS — drops Stri Karaka).
_KARAKA_NAMES_7: Final[tuple[str, ...]] = _KARAKA_NAMES_8[:7]


# Human-readable labels paired with the canonical short forms used in
# verdict strings.
_KARAKA_LABELS: Final[dict[str, str]] = {
    "atmakaraka":   "Atmakaraka",
    "amatyakaraka": "Amatyakaraka",
    "bhratrikaraka": "Bhratrikaraka",
    "matrikaraka":  "Matrikaraka",
    "pitrikaraka":  "Pitrikaraka",
    "gnatikaraka":  "Gnatikaraka",
    "darakaraka":   "Darakaraka",
    "strikaraka":   "Strikaraka",
}


# 3-vote envelope — karaka identification is a single deterministic
# ranking, not a 3-pillar (house/lord/karaka) judgment. We set all votes
# False with band "indicative_only" so the score stays at 0.0, matching
# the "no doctrine interpretation applied" semantics other Tier-0
# primitives use.
_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# Planets that always rank with inverted (``30 - degree``) longitudes.
# Rahu's conceptual retrogression is inherent (it does not depend on
# the ``is_retrograde`` flag, which for True Node may transiently report
# direct motion); see D-1 doctrine note.
_ALWAYS_INVERTED: Final[frozenset[str]] = frozenset({"Rahu"})

# Planets that are never candidates for Chara karaka in either mode.
_NEVER_KARAKA: Final[frozenset[str]] = frozenset({"Ketu"})


def _effective_degree(planet: str, planet_entry: dict) -> float:
    """Return the degree-within-sign used for ranking.

    For retrograde planets (and always for Rahu), the degree is inverted:
    a planet at deg 5 retrograde ranks as ``30 - 5 = 25``. Matches
    jagannathahora.io's default karaka behaviour.

    The function reads ``degree_in_sign`` first (fast path); if absent,
    it falls back to ``longitude % 30``.
    """
    deg = planet_entry.get("degree_in_sign")
    if deg is None:
        lon = float(planet_entry["longitude"])
        deg = lon % 30.0
    deg = float(deg)

    invert = (
        planet in _ALWAYS_INVERTED
        or bool(planet_entry.get("is_retrograde", False))
    )
    if invert:
        return 30.0 - deg
    return deg


def _sign_name_for(planet_entry: dict) -> str | None:
    """Best-effort retrieval of the sign-name for verdict prettiness."""
    name = planet_entry.get("sign_name")
    if isinstance(name, str):
        return name
    return None


def _karaka_finding(
    karaka_key: str,
    planet: str,
    planet_entry: dict,
    effective_degree: float,
    is_inverted: bool,
    karaka_mode: int,
) -> Finding:
    """Build the Finding for a single karaka assignment."""
    label = _KARAKA_LABELS[karaka_key]
    sign = _sign_name_for(planet_entry)
    raw_deg = float(
        planet_entry.get("degree_in_sign", planet_entry["longitude"] % 30.0)
    )
    suffix = f" at {raw_deg:.2f}°"
    if sign is not None:
        suffix = f"{suffix} {sign}"
    if is_inverted:
        suffix = f"{suffix} (inv)"
    verdict = f"{label} is {planet}{suffix}"

    return Finding(
        id=f"primitive.karakas.{karaka_key}",
        rule="karakas",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"karaka_mode={karaka_mode}",
            f"raw_degree_in_sign={raw_deg:.4f}",
            f"effective_degree={effective_degree:.4f}",
            f"inverted={is_inverted}",
            "doctrine=D-1 (jaimini_8_karaka_pvr)",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def compute_karakas(
    d1_chart: dict,
    karaka_mode: Literal[7, 8] = 8,
) -> dict[str, Finding]:
    """Compute Jaimini Chara Karakas from a D1 chart.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each position
            must carry either ``degree_in_sign`` (preferred) or
            ``longitude``. ``is_retrograde`` may be absent (defaults
            False); Rahu always uses inverted longitudes regardless.
        karaka_mode: ``8`` (D-1 default) includes Rahu and yields the
            Stri-Karaka slot; ``7`` (classical BPHS) excludes Rahu and
            drops Stri-Karaka.

    Returns:
        A dict keyed by canonical karaka name (``"atmakaraka"`` ...
        ``"strikaraka"`` for mode 8; ... ``"darakaraka"`` for mode 7).
        Each value is a ``primitive.karakas.<karaka>`` Finding.

    Raises:
        ValueError: if ``karaka_mode`` is not 7 or 8.
        KeyError: if a candidate planet is missing both ``degree_in_sign``
            and ``longitude`` in its D1 entry.
    """
    if karaka_mode not in (7, 8):
        raise ValueError(
            f"karaka_mode must be 7 or 8 (D-1), got {karaka_mode!r}"
        )

    # Build the candidate list. Always exclude Ketu. In 7-mode also
    # exclude Rahu.
    excluded = set(_NEVER_KARAKA)
    if karaka_mode == 7:
        excluded.add("Rahu")

    candidates: list[tuple[str, float, bool, dict]] = []
    for planet, entry in d1_chart.items():
        if planet in excluded:
            continue
        # Only the 7 naturals + Rahu are candidates. Silently ignore any
        # exotic chart key (custom Upagrahas etc.) so the function stays
        # robust to chart-shape changes.
        if planet not in {
            "Sun", "Moon", "Mars", "Mercury",
            "Jupiter", "Venus", "Saturn", "Rahu",
        }:
            continue
        try:
            eff = _effective_degree(planet, entry)
        except KeyError as exc:
            raise KeyError(
                f"planet {planet!r} missing both 'degree_in_sign' and "
                f"'longitude' in D1 chart"
            ) from exc
        invert = (
            planet in _ALWAYS_INVERTED
            or bool(entry.get("is_retrograde", False))
        )
        candidates.append((planet, eff, invert, entry))

    # Sort descending by effective degree. Tie-break by planet name for
    # determinism (rare in practice given degree precision, but keeps the
    # function pure given identical inputs).
    candidates.sort(key=lambda t: (-t[1], t[0]))

    karaka_names = _KARAKA_NAMES_8 if karaka_mode == 8 else _KARAKA_NAMES_7
    if len(candidates) < len(karaka_names):
        raise ValueError(
            f"insufficient candidate planets ({len(candidates)}) for "
            f"karaka_mode={karaka_mode} (need {len(karaka_names)})"
        )

    findings: dict[str, Finding] = {}
    for karaka_key, (planet, eff, invert, entry) in zip(
        karaka_names, candidates[: len(karaka_names)]
    ):
        findings[karaka_key] = _karaka_finding(
            karaka_key, planet, entry, eff, invert, karaka_mode
        )
    return findings


__all__ = ["compute_karakas"]
