"""Transit hits against a natal point: exact instants, orb entry and exit.

For event-timing work the useful object is not "is there a transit today" but
the *interval* a transit is in orb and the instant it perfects. Both are found
here by scanning for sign changes in the signed angle to the aspect target and
bisecting.

Two correctness points that are easy to get wrong:

* **Every aspect except conjunction and opposition has two targets.** A
  transiting body squares a natal point at ``natal + 90`` *and* ``natal - 90``.
  Testing only the forward target silently halves the hit rate for sextiles,
  squares, and trines.
* **Retrograde bodies perfect the same aspect three times.** The scan accepts
  sign changes in *both* directions, so the direct-retrograde-direct triple is
  returned as three hits rather than one.

Known limitation, stated rather than hidden: a body that stations almost
exactly on the target can graze it without a sign change, and a purely
sign-change scan will miss that tangency. Such grazes are rare and are, by
construction, the weakest hits in any orb window.

Usage:
    from app.empirical.western.transits import transit_hits
    hits = transit_hits(natal_lon=123.45, body="Saturn",
                        jd_start=jd0, jd_end=jd0 + 365.25, orb=1.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence

from app.empirical.western.angles import norm360, signed_delta
from app.empirical.western.aspects import PTOLEMAIC, AspectDef
from app.empirical.western.tropical import tropical_position

__all__ = ["TransitHit", "transit_hits", "aspect_targets"]

# Coarse-scan step per body, in days. Chosen so the fastest mover advances well
# under 180° per step, which is what keeps sign-change detection sound.
_DEFAULT_STEP: Final[dict[str, float]] = {
    "Moon": 0.25,
    "Mercury": 0.5,
    "Venus": 0.5,
    "Sun": 0.5,
    "Mars": 1.0,
}
_FALLBACK_STEP: Final[float] = 1.0

_TOL_DEG: Final[float] = 1e-6
_MAX_BISECT: Final[int] = 200


@dataclass(frozen=True, slots=True)
class TransitHit:
    """One perfection of one aspect, with its orb window.

    Attributes:
      body: Transiting body.
      natal_longitude: The natal point aspected.
      aspect: Aspect name.
      angle: Aspect angle.
      target_longitude: Which of the (up to two) target degrees was hit.
      exact_jd: Instant of perfection.
      enter_jd: When the body entered ``orb`` of the target, or ``None`` if it
        was already inside orb at ``jd_start``.
      exit_jd: When it left orb, or ``None`` if still inside at ``jd_end``.
      orb: The orb allowance the window was measured at.
      retrograde_at_exact: Whether the body was retrograde when it perfected.
    """

    body: str
    natal_longitude: float
    aspect: str
    angle: float
    target_longitude: float
    exact_jd: float
    enter_jd: float | None
    exit_jd: float | None
    orb: float
    retrograde_at_exact: bool


def aspect_targets(natal_longitude: float, angle: float) -> tuple[float, ...]:
    """The longitude(s) at which ``angle`` to ``natal_longitude`` perfects.

    Conjunction (0°) and opposition (180°) have a single target; every other
    aspect has two, one on each side of the natal point.
    """
    if angle == 0.0 or angle == 180.0:
        return (norm360(natal_longitude + angle),)
    return (norm360(natal_longitude + angle), norm360(natal_longitude - angle))


def _signed_to_target(jd: float, body: str, target: float) -> float:
    return signed_delta(target, tropical_position(jd, body).longitude)


def _bisect_zero(jd_lo: float, jd_hi: float, body: str, target: float) -> float:
    """Bisect a bracketed sign change of the signed angle to target."""
    f_lo = _signed_to_target(jd_lo, body, target)
    for _ in range(_MAX_BISECT):
        jd_mid = (jd_lo + jd_hi) / 2.0
        f_mid = _signed_to_target(jd_mid, body, target)
        if abs(f_mid) < _TOL_DEG:
            return jd_mid
        if (f_lo < 0.0) == (f_mid < 0.0):
            jd_lo, f_lo = jd_mid, f_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2.0


def _bisect_orb(
    jd_inside: float,
    jd_outside: float,
    body: str,
    target: float,
    orb: float,
) -> float:
    """Bisect the instant ``|signed angle|`` equals ``orb``."""
    for _ in range(_MAX_BISECT):
        jd_mid = (jd_inside + jd_outside) / 2.0
        dev = abs(_signed_to_target(jd_mid, body, target)) - orb
        if abs(dev) < _TOL_DEG:
            return jd_mid
        if dev < 0.0:
            jd_inside = jd_mid
        else:
            jd_outside = jd_mid
    return (jd_inside + jd_outside) / 2.0


def _orb_window(
    exact_jd: float,
    body: str,
    target: float,
    orb: float,
    jd_start: float,
    jd_end: float,
    step: float,
) -> tuple[float | None, float | None]:
    """Walk out from perfection to find orb entry and exit."""
    fine = min(step, 0.25)

    enter: float | None = None
    jd = exact_jd
    while jd > jd_start:
        prev = max(jd_start, jd - fine)
        if abs(_signed_to_target(prev, body, target)) > orb:
            enter = _bisect_orb(jd, prev, body, target, orb)
            break
        jd = prev

    exit_jd: float | None = None
    jd = exact_jd
    while jd < jd_end:
        nxt = min(jd_end, jd + fine)
        if abs(_signed_to_target(nxt, body, target)) > orb:
            exit_jd = _bisect_orb(jd, nxt, body, target, orb)
            break
        jd = nxt

    return enter, exit_jd


def transit_hits(
    natal_lon: float,
    body: str,
    jd_start: float,
    jd_end: float,
    *,
    aspects: Sequence[AspectDef] = PTOLEMAIC,
    orb: float = 1.0,
    step_days: float | None = None,
) -> list[TransitHit]:
    """Every perfection of every requested aspect in ``[jd_start, jd_end]``.

    Args:
      natal_lon: The natal longitude being transited.
      body: Transiting body name.
      jd_start, jd_end: Search window, Julian Days (UT).
      aspects: Which aspects to look for.
      orb: Orb width for the entry/exit window, degrees.
      step_days: Coarse scan step; defaults to a per-body value.

    Returns:
      Hits sorted by ``exact_jd``.
    """
    if jd_end <= jd_start:
        raise ValueError("jd_end must be after jd_start")
    if orb <= 0.0:
        raise ValueError(f"orb must be positive, got {orb}")
    step = step_days if step_days is not None else _DEFAULT_STEP.get(body, _FALLBACK_STEP)

    hits: list[TransitHit] = []
    for adef in aspects:
        for target in aspect_targets(natal_lon, adef.angle):
            jd_lo = jd_start
            f_lo = _signed_to_target(jd_lo, body, target)
            while jd_lo < jd_end:
                jd_hi = min(jd_lo + step, jd_end)
                f_hi = _signed_to_target(jd_hi, body, target)
                # Accept crossings in either direction (direct or retrograde),
                # rejecting the ±180 seam by its ~360° jump.
                crossed = (f_lo < 0.0) != (f_hi < 0.0)
                if crossed and abs(f_hi - f_lo) < 180.0:
                    exact = _bisect_zero(jd_lo, jd_hi, body, target)
                    enter, leave = _orb_window(exact, body, target, orb, jd_start, jd_end, step)
                    hits.append(
                        TransitHit(
                            body=body,
                            natal_longitude=norm360(natal_lon),
                            aspect=adef.name,
                            angle=adef.angle,
                            target_longitude=target,
                            exact_jd=exact,
                            enter_jd=enter,
                            exit_jd=leave,
                            orb=orb,
                            retrograde_at_exact=tropical_position(exact, body).is_retrograde,
                        )
                    )
                jd_lo, f_lo = jd_hi, f_hi

    hits.sort(key=lambda h: h.exact_jd)
    return hits
