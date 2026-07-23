"""Text renderer for the Dvādaśāṁśa (D-12) parents reading (`judges/dwadasamsa_parents_reading.py`).

REPORT-ONLY. The core is Raman's authoritative parents method; the D-12 block corroborates. UTF-8.
"""
from __future__ import annotations

from app.raman_saab.judges.dwadasamsa_parents_reading import (
    DwadasamsaParentsReading, ParentPicture)
from app.raman_saab.judges.saptamsa_reading import Tagged

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def _parent_lines(p: ParentPicture) -> list[str]:
    out = [f"  [{p.parent}]  {p.house}th : {_sign(p.house_sign)} (lord {p.house_lord} in house "
           f"{p.house_lord_house}, {p.house_lord_dignity}); kāraka {p.karaka} in house "
           f"{p.karaka_house} ({p.karaka_dignity})"]
    if p.house_occupants:
        out.append(f"        occupants : {', '.join(p.house_occupants)}")
    if p.house_aspecting:
        out.append(f"        aspected by: {', '.join(p.house_aspecting)}")
    out.append(f"        >>> {p.parent.upper()}: {p.verdict.upper()} <<<")
    return out


def to_text(r: DwadasamsaParentsReading) -> str:
    ov = r.overlay
    L: list[str] = []
    L.append("=" * 72)
    L.append("DWADASAMSA (D-12) PARENTS READING")
    L.append("=" * 72)
    for n in r.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- RAMAN CORE (authoritative - his real parents method decides) --")
    L.extend(_parent_lines(r.mother))
    L.extend(_parent_lines(r.father))
    L.append("")
    L.append("-- D-12 OVERLAY (report-only corroboration) --")
    L.append(f"  D-12 lagna : {_sign(ov.lagna_sign)} (lord {ov.lagna_lord})")
    L.append(f"  D-12 4th (mother): {_sign(ov.fourth_sign)}"
             + (f", occupied by {', '.join(ov.fourth_occupants)}" if ov.fourth_occupants else ""))
    L.append(f"  D-12 9th (father): {_sign(ov.ninth_sign)}"
             + (f", occupied by {', '.join(ov.ninth_occupants)}" if ov.ninth_occupants else ""))
    L.append("=" * 72)
    return "\n".join(L)
