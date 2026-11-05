"""Text renderer for the generalized matter-varga reading (`judges/matter_varga_reading.py`).

REPORT-ONLY. The core is Raman's authoritative house-method; the varga block corroborates. UTF-8.
"""
from __future__ import annotations

from app.raman_saab.judges.matter_varga_reading import MatterVargaReading
from app.raman_saab.judges.saptamsa_reading import Tagged
from app.raman_saab.ordinals import ordinal

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(r: MatterVargaReading) -> str:
    c = r.core
    ov = r.overlay
    L: list[str] = []
    L.append("=" * 72)
    L.append(f"{c.matter.upper()}  —  D-{ov.varga} {ov.varga_name} reading")
    L.append("=" * 72)
    for n in r.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- RAMAN CORE (authoritative - his real house-method decides) --")
    L.append(f"  {ordinal(c.house)} house : {_sign(c.house_sign)} (lord {c.house_lord} in house "
             f"{c.house_lord_house}, {c.house_lord_dignity})")
    if c.house_occupants:
        L.append(f"  occupants : {', '.join(c.house_occupants)}")
    if c.house_aspecting:
        L.append(f"  aspected by: {', '.join(c.house_aspecting)}")
    if c.karakas:
        L.append("  karakas :")
        for k, house, dig in c.karakas:
            L.append(f"        {k}: house {house}, {dig}")
    L.append(f"  >>> {c.matter.upper()}: {c.verdict.upper()} <<<")
    L.append("")
    L.append(f"-- D-{ov.varga} OVERLAY (report-only corroboration) --")
    L.append(f"  lagna : {_sign(ov.lagna_sign)} (lord {ov.lagna_lord})"
             + (f", occupied by {', '.join(ov.lagna_occupants)}" if ov.lagna_occupants else ""))
    L.append(f"  the {ordinal(c.house)} in D-{ov.varga}: {_sign(ov.house_sign_in_varga)}"
             + (f", occupied by {', '.join(ov.house_occupants_in_varga)}"
                if ov.house_occupants_in_varga else ""))
    L.append("=" * 72)
    return "\n".join(L)
