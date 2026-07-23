"""Text renderer for the family soul-group synthesis (`judges/family_soul_group.py`).

REPORT-ONLY, nets nothing — the header says so. Emits UTF-8.

Usage:
    from app.raman_saab.render_family_soul import to_text
    print(to_text(build_family_soul_group([("father", chart_a), ...])))
"""
from __future__ import annotations

from app.raman_saab.judges.family_soul_group import FamilySoulGroup, SoulSignature
from app.raman_saab.judges.soul_reading import SoulTagged

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: SoulTagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def _sig_line(s: SoulSignature) -> str:
    return (f"  [{s.role}]  Atmakaraka {s.ak_planet} in {_sign(s.ak_sign)}  |  "
            f"Karakamsa {_sign(s.karakamsa_sign)}  |  Ketu {_sign(s.ketu_sign)}  |  "
            f"Arudha {_sign(s.arudha_sign)}")


def _section(title: str, items: tuple[SoulTagged, ...], empty: str) -> list[str]:
    out = [f"-- {title} --"]
    out.extend(f"  - {_tag(t)}" for t in items) if items else out.append(f"  ({empty})")
    return out


def to_text(g: FamilySoulGroup) -> str:
    L: list[str] = []
    L.append("=" * 76)
    L.append("FAMILY SOUL-GROUP SYNTHESIS  —  report-only, nets no verdict")
    L.append("=" * 76)
    for n in g.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- THE GROUP STORY --")
    L.append(f"  {g.narrative}")
    L.append("")
    L.append("-- SOUL SIGNATURES --")
    for s in g.signatures:
        L.append(_sig_line(s))
    L.append("")
    L.extend(_section("SHARED SOUL-FRAMES", g.shared_soul_frames, "no shared soul-frame"))
    L.append("")
    L.extend(_section("KARMIC ROLE-INTERLOCKS", g.role_swaps, "no role-interlock"))
    L.append("")
    L.extend(_section("KETU-AXIS RESONANCE", g.ketu_axis, "no ketu-axis resonance"))
    L.append("")
    L.extend(_section("RECURRING SOUL-MOTIF", g.recurring_motif, "no dominant recurring motif"))
    L.append("=" * 76)
    return "\n".join(L)
