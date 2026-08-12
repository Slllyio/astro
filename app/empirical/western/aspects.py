"""Western aspects with a configurable, pre-registrable orb table.

Two things distinguish this from the Vedic drishti in ``app/core``: Western
aspects are *degree-orb gated* (Vedic whole-sign drishti fires by sign
membership and uses orb only to mark exactness), and they carry an
**applying/separating** polarity derived from relative speed.

The orb table is data, not code, because orb width is a live researcher degree
of freedom — widen it and more pairs qualify, which quietly inflates any
"chart has aspect X" feature. :meth:`OrbTable.fingerprint` produces the hash
that a pre-registration row carries, so a screening run and its confirmatory
re-run can be proven to have used the same orbs.

Applying/separating is computed analytically from ``d|separation|/dt`` rather
than by re-casting the chart a few hours later — no second ephemeris call, and
no risk of stepping *past* exactness and reporting the flip.

Usage:
    from app.empirical.western.aspects import find_aspects, DEFAULT_ORBS
    hits = find_aspects(positions, orbs=DEFAULT_ORBS)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Final, Iterable, Mapping, Sequence

from app.empirical.western.angles import signed_delta
from app.empirical.western.tropical import Position

__all__ = [
    "AspectDef",
    "PTOLEMAIC",
    "MINOR",
    "ALL_ASPECTS",
    "OrbTable",
    "DEFAULT_ORBS",
    "Aspect",
    "find_aspects",
]


@dataclass(frozen=True, slots=True)
class AspectDef:
    """A named angular relationship."""

    name: str
    angle: float


#: The five classical (Ptolemaic) aspects.
PTOLEMAIC: Final[tuple[AspectDef, ...]] = (
    AspectDef("conjunction", 0.0),
    AspectDef("sextile", 60.0),
    AspectDef("square", 90.0),
    AspectDef("trine", 120.0),
    AspectDef("opposition", 180.0),
)

#: Common minor aspects. Off by default — each one added is another test in the
#: family, and the tournament corrects for multiplicity at q=0.10.
MINOR: Final[tuple[AspectDef, ...]] = (
    AspectDef("semisextile", 30.0),
    AspectDef("semisquare", 45.0),
    AspectDef("quintile", 72.0),
    AspectDef("sesquiquadrate", 135.0),
    AspectDef("quincunx", 150.0),
)

ALL_ASPECTS: Final[tuple[AspectDef, ...]] = PTOLEMAIC + MINOR

_LUMINARIES: Final[frozenset[str]] = frozenset({"Sun", "Moon"})


@dataclass(frozen=True, slots=True)
class OrbTable:
    """Per-aspect orb allowances, with an optional luminary widening.

    Attributes:
      per_aspect: Aspect name → maximum orb in degrees.
      luminary_bonus: Extra degrees allowed when the Sun or Moon is one of the
        two bodies — the standard Western convention that the lights carry
        wider orbs. Set to 0.0 to disable.
    """

    per_aspect: Mapping[str, float] = field(default_factory=dict)
    luminary_bonus: float = 0.0

    def orb_for(self, aspect_name: str, body_a: str, body_b: str) -> float | None:
        """Allowed orb for this aspect between these bodies, or ``None`` if the
        aspect is not in the table (meaning: do not test it)."""
        base = self.per_aspect.get(aspect_name)
        if base is None:
            return None
        if self.luminary_bonus and (body_a in _LUMINARIES or body_b in _LUMINARIES):
            return base + self.luminary_bonus
        return base

    def fingerprint(self) -> str:
        """Stable SHA-256 of the table's canonical form.

        This is the value a pre-registration row records. Two runs with the
        same fingerprint provably used the same orbs; a changed fingerprint
        invalidates the registration.
        """
        canonical = json.dumps(
            {
                "per_aspect": {k: float(v) for k, v in sorted(self.per_aspect.items())},
                "luminary_bonus": float(self.luminary_bonus),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


#: A mainstream default. Deliberately conservative; the tournament may register
#: alternatives as separate pre-registered arms rather than tuning this in place.
DEFAULT_ORBS: Final[OrbTable] = OrbTable(
    per_aspect={
        "conjunction": 8.0,
        "opposition": 8.0,
        "trine": 7.0,
        "square": 7.0,
        "sextile": 5.0,
    },
    luminary_bonus=2.0,
)


@dataclass(frozen=True, slots=True)
class Aspect:
    """One aspect hit between two bodies.

    Attributes:
      body_a, body_b: Body names, ordered as supplied.
      aspect: Aspect name.
      angle: The exact angle the aspect is defined at.
      separation: Actual angular separation, ``[0, 180]``.
      orb: Absolute deviation from exactness, degrees.
      allowed_orb: The table's allowance this hit passed under.
      applying: ``True`` if closing toward exactness, ``False`` if separating,
        ``None`` when exact or when both bodies share a velocity.
    """

    body_a: str
    body_b: str
    aspect: str
    angle: float
    separation: float
    orb: float
    allowed_orb: float
    applying: bool | None


def _applying(
    signed_separation: float,
    speed_a: float,
    speed_b: float,
    angle: float,
) -> bool | None:
    """Is the pair closing toward exactness?

    ``signed_separation`` is ``signed_delta(a, b)`` in ``[-180, 180)``. The
    separation magnitude changes at ``sign(d) * (v_b - v_a)``; the aspect
    deviation ``|d| - angle`` closes when that rate points toward zero.
    """
    sep = abs(signed_separation)
    deviation = sep - angle
    if deviation == 0.0:
        return None  # exact right now
    relative = speed_b - speed_a
    if signed_separation > 0.0:
        rate = relative
    elif signed_separation < 0.0:
        rate = -relative
    else:
        # Exactly conjunct in longitude: separation can only grow, at |v_b - v_a|.
        rate = abs(relative)
    if rate == 0.0:
        return None  # locked together; neither applying nor separating
    return rate < 0.0 if deviation > 0.0 else rate > 0.0


def find_aspects(
    positions: Mapping[str, Position],
    *,
    orbs: OrbTable = DEFAULT_ORBS,
    aspects: Sequence[AspectDef] = PTOLEMAIC,
    bodies: Iterable[str] | None = None,
) -> list[Aspect]:
    """All aspect hits among the given positions.

    Each unordered pair is reported at most once per aspect, in the iteration
    order of ``bodies`` (or of ``positions`` when ``bodies`` is None). When a
    pair qualifies for more than one aspect — possible only with overlapping
    orbs — every qualifying aspect is returned; the caller decides.

    Returns:
      Hits sorted by orb ascending, so the tightest aspect comes first.
    """
    names = list(bodies) if bodies is not None else list(positions)
    missing = [n for n in names if n not in positions]
    if missing:
        raise KeyError(f"bodies not in positions: {missing}")

    hits: list[Aspect] = []
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            pos_a, pos_b = positions[name_a], positions[name_b]
            d = signed_delta(pos_a.longitude, pos_b.longitude)
            sep = abs(d)
            for adef in aspects:
                allowed = orbs.orb_for(adef.name, name_a, name_b)
                if allowed is None:
                    continue
                orb = abs(sep - adef.angle)
                if orb > allowed:
                    continue
                hits.append(
                    Aspect(
                        body_a=name_a,
                        body_b=name_b,
                        aspect=adef.name,
                        angle=adef.angle,
                        separation=sep,
                        orb=orb,
                        allowed_orb=allowed,
                        applying=_applying(d, pos_a.speed_longitude, pos_b.speed_longitude, adef.angle),
                    )
                )
    hits.sort(key=lambda h: (h.orb, h.body_a, h.body_b, h.aspect))
    return hits
