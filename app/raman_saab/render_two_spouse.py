"""Text renderer for the two-spouse children synthesis (`judges/two_spouse_children.py`).

ASCII-safe (sign names, no diacritics). Keeps the doctrinal posture explicit in the header:
this surface REPORTS both parents' testimonies + their concordances and redemptive threads and
nets NO combined verdict (Raman gives no netting formula — HTJAH-I:5436/5968 are qualitative).

Usage:
    from app.raman_saab.render_two_spouse import to_text
    print(to_text(build_two_spouse_children_synthesis(father, mother, "father", "mother")))
"""
from __future__ import annotations

from app.raman_saab.judges.saptamsa_reading import Tagged
from app.raman_saab.judges.two_spouse_children import (
    SpouseChildTestimony, TwoSpouseChildrenSynthesis)

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def _testimony_lines(t: SpouseChildTestimony) -> list[str]:
    out = [
        f"  [{t.role}]  CHILDREN VERDICT: {t.verdict.upper()}",
        f"     Rasi 5th : {_sign(t.fifth_sign)} (lord {t.fifth_lord} in house "
        f"{t.fifth_lord_house}, {t.fifth_lord_dignity})",
        f"     Putrakaraka Jupiter: house {t.putrakaraka_house} "
        f"({t.putrakaraka_rasi_dignity} rasi / {t.putrakaraka_navamsa_dignity} navamsa)",
        f"     Beeja strong: {t.beeja_strong}   Kshetra strong: {t.kshetra_strong}",
    ]
    if t.d7_eldest_afflictions:
        out.append("     eldest-seat (D-7 lagna) afflictions:")
        out.extend(f"        - {_tag(a)}" for a in t.d7_eldest_afflictions)
    return out


def to_text(syn: TwoSpouseChildrenSynthesis) -> str:
    L: list[str] = []
    L.append("=" * 72)
    L.append("TWO-SPOUSE CHILDREN SYNTHESIS (report-only - nets no verdict)")
    L.append("=" * 72)
    for n in syn.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- PER-PARENT TESTIMONY (each from Raman's real method) --")
    for t in syn.testimonies:
        L.extend(_testimony_lines(t))
    L.append("")
    L.append("-- CONCORDANCES (structural afflictions true in BOTH charts) --")
    if syn.concordances:
        L.extend(f"  - {_tag(c)}" for c in syn.concordances)
    else:
        L.append("  (no shared affliction across the two charts)")
    L.append("")
    L.append("-- REDEMPTIVE THREAD (offsetting significators - HTJAH-I:5968) --")
    if syn.redemptive_thread:
        L.extend(f"  - {_tag(r)}" for r in syn.redemptive_thread)
    else:
        L.append("  (no offsetting significator surfaced)")
    L.append("=" * 72)
    return "\n".join(L)
