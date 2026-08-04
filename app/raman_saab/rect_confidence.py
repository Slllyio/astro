"""Rectification confidence (v31) — how far the birth time can move before each pillar breaks.

The chapter answers "why is this birth time trusted?" the only honest way the engine can: by
MEASURING sensitivity. The chart is re-cast minute-by-minute outward from the stated birth
time, in BOTH directions, and the report's load-bearing pillars are compared at every step:
the Lagna sign (every whole-sign house verdict keys off it), the Navamsa Lagna (the
nature-stamp and vargottama reads), the Moon's nakshatra (the entire Vimshottari sequence
anchors there), and each planet's whole-sign house. For every pillar this yields a STABLE
RANGE in minutes — how far back and how far forward it can move before it flips — never a
fixed pass/fail at one offset. The combined range where EVERY pillar holds simultaneously is
reported too; that is the honest answer to "how much birth-time error can this reading
tolerate." Confidence stays a measured count/range, never an invented percentage.

Event-based rectification proper (matching dated life events against the timeline) is a
separate instrument the app already carries (`app/raman_saab/rectification/`, the
/rectification routes) — this chapter states input sensitivity only, and says so.

Usage:
    from app.raman_saab.rect_confidence import build_rect_confidence
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Final, Optional

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

# ponytail: a linear 1-minute scan out to +-SCAN_WINDOW minutes — one chart cast is checked
# against ALL pillars at once, so cost is O(window), not O(window x pillars). 60 minutes
# comfortably covers realistic rectification ranges while keeping report-build cost bounded.
# If that proves too narrow or too slow: widen this constant, or replace the linear scan with
# a galloping+binary-search bracket per pillar — not a redesign.
SCAN_WINDOW: Final[int] = 60

#: minutes both load-bearing pillars (Lagna sign, Moon nakshatra) must hold, each direction,
#: for the "firm" label — a namable threshold, not a magic number buried in the logic below.
_FIRM_THRESHOLD: Final[int] = 10


@dataclass(frozen=True)
class PillarSensitivity:
    pillar: str
    base_value: str
    stable_minus: int                       # minutes stable moving the birth time earlier
    stable_plus: int                        # minutes stable moving the birth time later
    flip_minus: Optional[tuple[int, str]]   # (offset, new value) just past stable_minus
    flip_plus: Optional[tuple[int, str]]    # (offset, new value) just past stable_plus


@dataclass(frozen=True)
class RectConfidence:
    pillars: tuple[PillarSensitivity, ...]
    stable_count: int              # pillars that never flip inside the full scan window
    total_count: int
    overall_stable_minus: int      # the window, going earlier, where EVERY pillar holds
    overall_stable_plus: int       # the window, going later, where EVERY pillar holds
    scan_window: int
    label: str
    frame: str


_FRAME: Final[str] = (
    f"Input sensitivity, measured: the chart re-cast minute-by-minute, in both directions, "
    f"out to +-{SCAN_WINDOW} minutes from the stated birth time, and the load-bearing pillars "
    f"compared at every step. Each pillar's stable range is the widest window, in each "
    f"direction, where its value still matches the stated time — a measured boundary, never "
    f"an invented confidence percentage. Event-based rectification (matching dated life "
    f"events) is a separate instrument at /rectification; this chapter states input "
    f"sensitivity only.")

_SIGN: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _asc_nav_sign(ch) -> int:
    """Navamsa lagna sign via the standard (sign*9 + pada) % 12 identity."""
    lon = ch.asc_lon % 360.0
    sign = int(lon // 30.0)
    pada = int((lon % 30.0) // (30.0 / 9.0))
    return (sign * 9 + pada) % 12 + 1


def build_rect_confidence(r: "DetailedReport", *, ayanamsa: str = "lahiri"
                          ) -> Optional[RectConfidence]:
    """`ayanamsa` MUST match whatever cast `r.chart` (default lahiri, the project-wide
    default — see `build_detailed_report`). A mismatch here is not cosmetic: two ayanamsas
    differ by a fixed few tenths of a degree, enough to flip a pillar sitting near a cusp
    under one ayanamsa but not the other, which would report a false birth-time sensitivity
    that is actually just an ayanamsa disagreement between the base chart and the probes."""
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData

    b = r.birth
    base = r.chart

    probes: list[tuple[str, object]] = [
        ("Lagna sign", lambda ch: _SIGN[ch.asc_sign - 1]),
        ("Navamsa Lagna sign", lambda ch: _SIGN[_asc_nav_sign(ch) - 1]),
        ("Moon nakshatra (Vimshottari anchor)",
         lambda ch: ch.planets["Moon"].nakshatra if "Moon" in ch.planets else "-"),
    ]
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        probes.append((f"{p} whole-sign house",
                       lambda ch, _p=p: ch.planets[_p].rasi_house if _p in ch.planets else "-"))

    # datetime + timedelta (not JD arithmetic) is correct here: an exact, small, calendar
    # rollover-aware minute shift — not the multi-year additions the JD-arithmetic rule guards
    # against. The prior fixed-offset version used `hour*60+minute` divmod, which silently
    # produced an invalid negative hour for any offset that crossed midnight — unreachable at
    # +-5 min, very reachable now that the scan runs out to +-60.
    base_dt = datetime(b.year, b.month, b.day, b.hour, b.minute)

    def _cast_offset(off: int):
        dt = base_dt + timedelta(minutes=off)
        return cast_chart(
            BirthData(name=b.name, year=dt.year, month=dt.month, day=dt.day,
                      hour=dt.hour, minute=dt.minute, tz_offset=b.tz_offset,
                      latitude=b.latitude, longitude=b.longitude),
            ayanamsa=ayanamsa)

    try:
        base_values = {name: str(fn(base)) for name, fn in probes}
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        return None

    names = [name for name, _ in probes]
    open_minus, open_plus = set(names), set(names)
    stable_minus = {name: SCAN_WINDOW for name in names}
    stable_plus = {name: SCAN_WINDOW for name in names}
    flip_minus: dict[str, Optional[tuple[int, str]]] = {name: None for name in names}
    flip_plus: dict[str, Optional[tuple[int, str]]] = {name: None for name in names}

    try:
        for off in range(1, SCAN_WINDOW + 1):
            if open_minus:
                ch = _cast_offset(-off)
                for name, fn in probes:
                    if name not in open_minus:
                        continue
                    v = str(fn(ch))
                    if v != base_values[name]:
                        stable_minus[name] = off - 1
                        flip_minus[name] = (-off, v)
                        open_minus.discard(name)
            if open_plus:
                ch = _cast_offset(off)
                for name, fn in probes:
                    if name not in open_plus:
                        continue
                    v = str(fn(ch))
                    if v != base_values[name]:
                        stable_plus[name] = off - 1
                        flip_plus[name] = (off, v)
                        open_plus.discard(name)
            if not open_minus and not open_plus:
                break
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        return None

    pillars = tuple(
        PillarSensitivity(pillar=name, base_value=base_values[name],
                          stable_minus=stable_minus[name], stable_plus=stable_plus[name],
                          flip_minus=flip_minus[name], flip_plus=flip_plus[name])
        for name in names)

    stable_count = sum(1 for pl in pillars if pl.flip_minus is None and pl.flip_plus is None)
    total = len(pillars)
    overall_minus = min(pl.stable_minus for pl in pillars)
    overall_plus = min(pl.stable_plus for pl in pillars)

    lagna, moon_nak = pillars[0], pillars[2]
    load_bearing_ok = (lagna.stable_minus >= _FIRM_THRESHOLD
                       and lagna.stable_plus >= _FIRM_THRESHOLD
                       and moon_nak.stable_minus >= _FIRM_THRESHOLD
                       and moon_nak.stable_plus >= _FIRM_THRESHOLD)
    if overall_minus >= SCAN_WINDOW and overall_plus >= SCAN_WINDOW:
        label = f"rock-solid — every pillar holds across the full +-{SCAN_WINDOW}-minute scan"
    elif load_bearing_ok:
        label = (f"firm — the Lagna and Vimshottari anchor hold at least "
                 f"+-{_FIRM_THRESHOLD} minutes; every pillar holds together from "
                 f"-{overall_minus} to +{overall_plus} minutes")
    else:
        label = (f"sensitive — a load-bearing pillar flips within +-{_FIRM_THRESHOLD} "
                 f"minutes; every pillar holds together from -{overall_minus} to "
                 f"+{overall_plus} minutes — read the lagna-keyed sections with care")

    return RectConfidence(pillars=pillars, stable_count=stable_count, total_count=total,
                          overall_stable_minus=overall_minus, overall_stable_plus=overall_plus,
                          scan_window=SCAN_WINDOW, label=label, frame=_FRAME)
