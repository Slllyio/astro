"""Text renderer for the derivative-house relative reading (`judges/relative_reading.py`).

REPORT-ONLY, descriptive (occupancy + aspect), not a verdict on the relative. Emits UTF-8.

Usage:
    from app.raman_saab.render_relative import to_text
    print(to_text(build_family_derivative_reading(chart)))
"""
from __future__ import annotations

from app.raman_saab.judges.relative_reading import (
    DerivedMatter, FamilyDerivativeReading, RelativeReading)
from app.raman_saab.judges.saptamsa_reading import Tagged

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def _matter_line(m: DerivedMatter) -> str:
    who = f"{m.matter} (the {m.offset}th from their lagna = your {m.native_house}th, "
    who += f"{_sign(m.sign)}, lord {m.lord})"
    tail = f" — occupied by {', '.join(m.occupants)}" if m.occupants else ""
    if m.aspecting:
        tail += f"; aspected by {', '.join(m.aspecting)}"
    return f"      {who}{tail}"


def _relative_block(r: RelativeReading) -> list[str]:
    out = [f"  [{r.role}]  read from the {r.base_house}th ({_sign(r.base_sign)}) — kāraka {r.karaka}"]
    for n in r.notes:
        out.append(f"      * {_tag(n)}")
    for m in r.matters:
        out.append(_matter_line(m))
        if m.affliction is not None:
            out.append(f"          - {_tag(m.affliction)}")
    return out


def to_text(fr: FamilyDerivativeReading) -> str:
    L: list[str] = []
    L.append("=" * 76)
    L.append("DERIVATIVE-HOUSE FAMILY READING  —  each relative read from YOUR chart")
    L.append("=" * 76)
    for n in fr.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    for r in fr.relatives:
        L.extend(_relative_block(r))
        L.append("")
    L.append("=" * 76)
    return "\n".join(L)
