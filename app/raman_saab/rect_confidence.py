"""Rectification confidence (v31) — what holds and what flips under birth-time error.

The chapter answers "why is this birth time trusted?" the only honest way the engine can:
by MEASURING sensitivity. The chart is re-cast at -5, -2, +2 and +5 minutes and the
report's load-bearing pillars are compared: the Lagna sign (every whole-sign house
verdict keys off it), the Navamsa Lagna (the nature-stamp and vargottama reads), the
Moon's nakshatra (the entire Vimshottari sequence anchors there), and each planet's
whole-sign house. What flips is listed with the offset that flips it; what holds is the
confidence — a COUNT of stable pillars, labeled, never an invented percentage.

Event-based rectification proper (matching dated life events against the timeline) is a
separate instrument the app already carries (`app/raman_saab/rectification/`, the
/rectification routes) — this chapter states input sensitivity only, and says so.

Usage:
    from app.raman_saab.rect_confidence import build_rect_confidence
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

_OFFSETS: Final[tuple[int, ...]] = (-5, -2, 2, 5)


@dataclass(frozen=True)
class PillarSensitivity:
    pillar: str
    base_value: str
    flips: tuple[tuple[int, str], ...]     # (offset minutes, new value) — empty = stable


@dataclass(frozen=True)
class RectConfidence:
    pillars: tuple[PillarSensitivity, ...]
    stable_count: int
    total_count: int
    label: str                             # rock-solid | firm | sensitive — count bands
    frame: str


_FRAME: Final[str] = (
    "Input sensitivity, measured: the chart re-cast at -5, -2, +2 and +5 minutes and the "
    "load-bearing pillars compared. The confidence is a count of stable pillars — never "
    "an invented percentage. Event-based rectification (matching dated life events) is a "
    "separate instrument at /rectification; this chapter states sensitivity only.")

_SIGN: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def build_rect_confidence(r: "DetailedReport") -> Optional[RectConfidence]:
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.primitives.dispositor import navamsa_lord_of  # noqa: F401 (probe)

    b = r.birth
    try:
        base = r.chart
        variants: dict[int, object] = {}
        for off in _OFFSETS:
            total = b.hour * 60 + b.minute + off
            variants[off] = cast_chart(
                BirthData(name=b.name, year=b.year, month=b.month, day=b.day,
                          hour=total // 60, minute=total % 60, tz_offset=b.tz_offset,
                          latitude=b.latitude, longitude=b.longitude),
                ayanamsa="raman")
    except Exception:  # noqa: BLE001 — Track-B / sparse
        return None

    pillars: list[PillarSensitivity] = []

    def _asc_nav_sign(ch) -> int:
        """Navamsa lagna sign via the standard (sign*9 + pada) % 12 identity."""
        lon = ch.asc_lon % 360.0
        sign = int(lon // 30.0)
        pada = int((lon % 30.0) // (30.0 / 9.0))
        return (sign * 9 + pada) % 12 + 1

    def probe(pillar: str, fn) -> None:
        base_v = fn(base)
        flips = tuple((off, str(fn(ch))) for off, ch in variants.items()
                      if fn(ch) != base_v)
        pillars.append(PillarSensitivity(pillar, str(base_v), flips))

    probe("Lagna sign", lambda ch: _SIGN[ch.asc_sign - 1])
    probe("Navamsa Lagna sign", lambda ch: _SIGN[_asc_nav_sign(ch) - 1])
    probe("Moon nakshatra (Vimshottari anchor)",
          lambda ch: ch.planets["Moon"].nakshatra if "Moon" in ch.planets else "-")
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        probe(f"{p} whole-sign house",
              lambda ch, _p=p: ch.planets[_p].rasi_house if _p in ch.planets else "-")

    stable = sum(1 for pl in pillars if not pl.flips)
    total = len(pillars)
    label = ("rock-solid (every pillar holds at ±5 minutes)" if stable == total else
             "firm (the Lagna and Vimshottari anchor hold; minor pillars shift)"
             if not pillars[0].flips and not pillars[2].flips else
             "sensitive (a load-bearing pillar flips within ±5 minutes — read the "
             "lagna-keyed sections with care)")
    return RectConfidence(pillars=tuple(pillars), stable_count=stable,
                          total_count=total, label=label, frame=_FRAME)
