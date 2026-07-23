"""Text renderer for the Siddhāṁśa (D-24) education reading (`judges/siddhamsa_education_reading.py`).

REPORT-ONLY. The core is Raman's authoritative education method; the D-24 block corroborates. UTF-8.
"""
from __future__ import annotations

from app.raman_saab.judges.saptamsa_reading import Tagged
from app.raman_saab.judges.siddhamsa_education_reading import SiddhamsaEducationReading

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(r: SiddhamsaEducationReading) -> str:
    c = r.core
    ov = r.overlay
    L: list[str] = []
    L.append("=" * 72)
    L.append("SIDDHAMSA (D-24) EDUCATION READING")
    L.append("=" * 72)
    for n in r.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- RAMAN CORE (authoritative - his real education method decides) --")
    L.append(f"  4th house (vidya): {_sign(c.fourth_sign)} (lord {c.fourth_lord} in house "
             f"{c.fourth_lord_house}, {c.fourth_lord_dignity})")
    if c.fourth_occupants:
        L.append(f"  4th occupants : {', '.join(c.fourth_occupants)}")
    if c.fourth_aspecting:
        L.append(f"  4th aspected by: {', '.join(c.fourth_aspecting)}")
    L.append("  education karakas :")
    for k, house, rdig, ndig in c.karakas:
        L.append(f"        {k}: house {house}, {rdig} rasi / {ndig} navamsa")
    L.append(f"  >>> EDUCATION: {c.education_verdict.upper()}   INTELLECT: "
             f"{c.intellect_verdict.upper()} <<<")
    L.append("")
    L.append("-- D-24 OVERLAY (report-only corroboration) --")
    L.append(f"  D-24 lagna : {_sign(ov.lagna_sign)} (lord {ov.lagna_lord})"
             + (f", occupied by {', '.join(ov.lagna_occupants)}" if ov.lagna_occupants else ""))
    L.append(f"  D-24 4th   : {_sign(ov.fourth_sign)}"
             + (f", occupied by {', '.join(ov.fourth_occupants)}" if ov.fourth_occupants else ""))
    L.append(f"  Jupiter D-24: {_sign(ov.jupiter_sign)} ({ov.jupiter_dignity})   "
             f"Mercury D-24: {_sign(ov.mercury_sign)} ({ov.mercury_dignity})")
    L.append("=" * 72)
    return "\n".join(L)
