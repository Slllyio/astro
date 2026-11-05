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


def finding(r: PitruDoshaReading) -> str:
    """The screen's own result in one line — what a reader opens this section to learn.
    Wave-3 (2026-08-18): the finding used to sit below five caveat bullets, so the
    section led with provenance and buried its answer. Pure re-read of `curse_yogas`;
    the full labelled list below is unchanged and every caveat is retained."""
    n = len(r.curse_yogas)
    if not n:
        return ("FINDING: no classical ancestral-curse yoga fires in this chart "
                "(Raman's own children verdict, below, reads "
                f"{r.raman_children_verdict.upper()}).")
    return (f"FINDING: {n} classical ancestral-curse yoga{'s' if n != 1 else ''} "
            f"fire{'' if n != 1 else 's'} - each is listed in full, with its provenance "
            f"tag and citation, below (Raman's own children verdict, also below, reads "
            f"{r.raman_children_verdict.upper()}).")


def to_text(r: PitruDoshaReading) -> str:
    L: list[str] = []
    L.append("=" * 76)
    L.append("PITṚ-DOṢA / ANCESTRAL-KARMA READING  —  classical lens, NOT a decree")
    L.append("=" * 76)
    # The finding leads; the five caveat bullets follow it unchanged (move only).
    L.append(finding(r))
    L.append("")
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
