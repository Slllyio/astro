"""Text renderer for the Navāṁśa (D-9) marriage reading (`judges/navamsa_marriage_reading.py`).

REPORT-ONLY. The core is Raman's authoritative marriage method; the D-9 block corroborates. UTF-8.
"""
from __future__ import annotations

from app.raman_saab.judges.navamsa_marriage_reading import NavamsaMarriageReading
from app.raman_saab.judges.saptamsa_reading import Tagged

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(r: NavamsaMarriageReading) -> str:
    c = r.core
    ov = r.overlay
    L: list[str] = []
    L.append("=" * 72)
    L.append("NAVAMSA (D-9) MARRIAGE READING")
    L.append("=" * 72)
    for n in r.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- RAMAN CORE (authoritative - his real marriage method decides) --")
    L.append(f"  7th house : {_sign(c.seventh_sign)} (lord {c.seventh_lord} in house "
             f"{c.seventh_lord_house}, {c.seventh_lord_dignity})")
    if c.seventh_occupants:
        L.append(f"  7th occupants : {', '.join(c.seventh_occupants)}")
    if c.seventh_aspecting:
        L.append(f"  7th aspected by: {', '.join(c.seventh_aspecting)}")
    L.append(f"  Venus (Kalatra): house {c.venus_house}, {c.venus_dignity} rasi / "
             f"{c.venus_navamsa_dignity} navamsa")
    L.append(f"  Navamsa lagna : {_sign(c.navamsa_lagna_sign)}; spouse significator "
             f"(7th-from-navamsa-lagna lord): {c.navamsa_seventh_lord}")
    L.append(f"  Kuja (Mangal) dosha: {'present' if c.kuja_dosha else 'absent'}"
             " [reckoned from the Lagna only]")
    if c.kuja_dosha:
        L.append("     NOTE: this project tested Kuja dosha directly on 2,322 real charts and it")
        L.append("     did NOT distinguish divorced from long-married (odds ratio 1.09, null).")
        L.append("     Reported for doctrinal completeness; it carries no demonstrated predictive")
        L.append("     weight. Raman also reckons it from the Moon and Venus, and gives per-sign")
        L.append("     exceptions and cancellations (HTJAH-II:2579-2622) not yet encoded here.")
    L.append(f"  >>> SPOUSE: {c.spouse_verdict.upper()}   MARITAL HAPPINESS: "
             f"{c.marital_verdict.upper()} <<<")
    L.append("")
    L.append("-- D-9 OVERLAY (report-only corroboration) --")
    L.append(f"  D-9 lagna : {_sign(ov.lagna_sign)} (lord {ov.lagna_lord})"
             + (f", occupied by {', '.join(ov.lagna_occupants)}" if ov.lagna_occupants else ""))
    L.append(f"  D-9 7th   : {_sign(ov.seventh_sign)}"
             + (f", occupied by {', '.join(ov.seventh_occupants)}" if ov.seventh_occupants else ""))
    L.append(f"  Venus D-9 : {_sign(ov.venus_sign)} ({ov.venus_dignity})")
    L.append(f"  Vargottama: {', '.join(ov.vargottama) if ov.vargottama else '(none)'}")
    L.append("=" * 72)
    return "\n".join(L)
