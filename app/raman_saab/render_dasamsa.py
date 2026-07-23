"""Text renderer for the Daśāṁśa (D-10) career reading (`judges/dasamsa_career_reading.py`).

REPORT-ONLY. The core is Raman's authoritative profession method; the D-10 block corroborates. UTF-8.
"""
from __future__ import annotations

from app.raman_saab.judges.dasamsa_career_reading import DasamsaCareerReading
from app.raman_saab.judges.saptamsa_reading import Tagged

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(r: DasamsaCareerReading) -> str:
    c = r.core
    ov = r.overlay
    L: list[str] = []
    L.append("=" * 72)
    L.append("DASAMSA (D-10) CAREER READING")
    L.append("=" * 72)
    for n in r.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- RAMAN CORE (authoritative - his real profession method decides) --")
    L.append(f"  10th house : {_sign(c.tenth_sign)} (lord {c.tenth_lord} in house "
             f"{c.tenth_lord_house}, {c.tenth_lord_dignity} rasi / "
             f"{c.tenth_lord_navamsa_dignity} navamsa)")
    if c.tenth_occupants:
        L.append(f"  10th occupants : {', '.join(c.tenth_occupants)}")
    if c.tenth_aspecting:
        L.append(f"  10th aspected by: {', '.join(c.tenth_aspecting)}")
    L.append("  career karakas :")
    for k, house, dig in c.karakas:
        L.append(f"        {k}: house {house}, {dig}")
    L.append(f"  >>> CAREER: {c.career_verdict.upper()}   HONOUR/STANDING: "
             f"{c.honour_verdict.upper()} <<<")
    L.append("")
    L.append("-- D-10 OVERLAY (report-only corroboration) --")
    L.append(f"  D-10 lagna : {_sign(ov.lagna_sign)} (lord {ov.lagna_lord})"
             + (f", occupied by {', '.join(ov.lagna_occupants)}" if ov.lagna_occupants else ""))
    L.append(f"  D-10 10th  : {_sign(ov.tenth_sign)}"
             + (f", occupied by {', '.join(ov.tenth_occupants)}" if ov.tenth_occupants else ""))
    L.append(f"  10th lord in D-10: {ov.tenth_lord_d10_dignity}")
    L.append("=" * 72)
    return "\n".join(L)
