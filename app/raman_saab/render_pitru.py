"""Text renderer for the pitṛ-doṣa / ancestral-karma reading (`judges/pitru_dosha_reading.py`).

REPORT-ONLY, CLASSICAL — Raman's own children verdict decides; the curse-yogas corroborate. Emits
UTF-8. NOT a decree, never medical advice — the caveats print with the reading.

Usage:
    from app.raman_saab.render_pitru import to_text
    print(to_text(build_pitru_dosha_reading(chart)))
"""
from __future__ import annotations

from app.raman_saab.judges.pitru_dosha_reading import PitruDoshaReading
from app.raman_saab.judges.saptamsa_reading import Tagged


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(r: PitruDoshaReading) -> str:
    L: list[str] = []
    L.append("=" * 76)
    L.append("PITṚ-DOṢA / ANCESTRAL-KARMA READING  —  classical lens, NOT a decree")
    L.append("=" * 76)
    for n in r.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append(f"-- RAMAN'S CHILDREN VERDICT (authoritative): {r.raman_children_verdict.upper()} --")
    L.append("")
    L.append("-- ANCESTRAL-CURSE YOGAS (classical; corroborating, not deciding) --")
    if r.curse_yogas:
        for y in r.curse_yogas:
            L.append(f"  - {_tag(y)}")
    else:
        L.append("  (no classical ancestral-curse yoga fires)")
    L.append("")
    L.append("-- PITṚ-STHĀNA (the 9th — ancestral / past-life seat) --")
    for p in r.pitru_bhava:
        L.append(f"  - {_tag(p)}")
    L.append("=" * 76)
    return "\n".join(L)
