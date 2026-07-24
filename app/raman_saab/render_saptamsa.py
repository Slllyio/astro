"""Text renderer for the Saptamsa (D-7) children reading (`judges/saptamsa_reading.py`).

ASCII-safe output (sign abbreviations, no diacritics) so it prints on any console. The
render keeps the doctrinal split explicit: the Raman-core block is the VERDICT; the D-7
block is a provenance-tagged corroboration.

Usage:
    from app.raman_saab.render_saptamsa import to_text
    print(to_text(build_saptamsa_children_reading(chart)))
"""
from __future__ import annotations

from app.raman_saab.judges.saptamsa_reading import (
    ChildLocus, SaptamsaChildrenReading, Tagged)

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _yn(v: object) -> str:
    """Render a flag for a human reader, never as a Python boolean."""
    return "yes" if v is True else "no" if v is False else "unknown"


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def _locus_lines(loc: ChildLocus) -> list[str]:
    out = [f"  [{loc.ordinal}] {loc.label} - seat: {loc.frame} = {_sign(loc.sign)} "
           f"(lord {loc.lord}) [{loc.scheme}]"]
    if loc.occupants:
        out.append(f"        occupied by: {', '.join(loc.occupants)}")
    if loc.aspecting:
        out.append(f"        aspected by: {', '.join(loc.aspecting)}")
    for a in loc.afflictions:
        out.append(f"        - {_tag(a)}")
    if not loc.afflictions:
        out.append("        (no malefic affliction on this seat)")
    return out


def to_text(reading: SaptamsaChildrenReading) -> str:
    rc = reading.raman_core
    ov = reading.d7_overlay
    L: list[str] = []
    L.append("=" * 72)
    L.append("SAPTAMSA (D-7) CHILDREN READING")
    L.append("=" * 72)
    for n in reading.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- RAMAN CORE (authoritative - his real method decides the verdict) --")
    L.append(f"  Rasi 5th house : {_sign(rc.rasi_fifth_sign)}  (lord {rc.rasi_fifth_lord} "
             f"in house {rc.rasi_fifth_lord_house}, {rc.rasi_fifth_lord_dignity})")
    if rc.rasi_fifth_occupants:
        L.append(f"  5th occupants  : {', '.join(rc.rasi_fifth_occupants)}")
    if rc.rasi_fifth_aspecting:
        L.append(f"  5th aspected by: {', '.join(rc.rasi_fifth_aspecting)}")
    L.append(f"  Putrakaraka {rc.putrakaraka}: house {rc.putrakaraka_house}, "
             f"{rc.putrakaraka_dignity} in Rasi / {rc.putrakaraka_navamsa_dignity} in Navamsa")
    L.append(f"  Beeja (male fertility point) strong: {_yn(rc.beeja_strong)}    "
             f"Kshetra (female) strong: {_yn(rc.kshetra_strong)}")
    L.append(f"  >>> CHILDREN VERDICT: {rc.children_verdict.upper()} <<<")
    if rc.verdict_metadata:
        for _k, _v in rc.verdict_metadata:          # never dump a raw dict repr at a reader
            if _k == "active_periods":             # shown (birth-clipped) in the house section
                continue
            L.append(f"  - {_k.replace('_', ' ')}: {_v}")
    L.append("")
    L.append("-- D-7 OVERLAY (report-only corroboration) --")
    L.append(f"  D-7 lagna : {_sign(ov.lagna_sign)} (lord {ov.lagna_lord})"
             + (f", occupied by {', '.join(ov.lagna_occupants)}" if ov.lagna_occupants else ""))
    L.append(f"  D-7 5th   : {_sign(ov.fifth_sign)} (lord {ov.fifth_lord})"
             + (f", occupied by {', '.join(ov.fifth_occupants)}" if ov.fifth_occupants else ""))
    L.append(f"  Jupiter   : {_sign(ov.jupiter_sign)} house {ov.jupiter_house} "
             f"({ov.jupiter_dignity})")
    L.append("  child loci:")
    for loc in ov.child_loci:
        L.extend(_locus_lines(loc))
    if ov.gender_indicators:
        L.append("  gender indicators (Rasi 5th, Raman-explicit):")
        for g in ov.gender_indicators:
            L.append(f"        - {_tag(g)}")
    L.append("=" * 72)
    return "\n".join(L)
