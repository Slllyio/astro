"""Text renderer for the matter-varga dashboard (`judges/matter_varga_dashboard.py`).

A one-glance matter-by-matter divisional snapshot (each verdict = the deep reader's Raman core).
REPORT-ONLY. UTF-8.
"""
from __future__ import annotations

from app.raman_saab.judges.matter_varga_dashboard import MatterVargaDashboard
from app.raman_saab.judges.saptamsa_reading import Tagged


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(d: MatterVargaDashboard) -> str:
    L: list[str] = []
    L.append("=" * 72)
    L.append("MATTER-VARGA DASHBOARD  —  deep divisional verdict per life-matter")
    L.append("=" * 72)
    for n in d.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append(f"  {'matter':<10} {'varga':<16} {'verdict':<20} deep reader")
    L.append(f"  {'-'*10} {'-'*16} {'-'*20} {'-'*24}")
    for e in d.entries:
        varga = f"D-{e.varga} {e.varga_name}"
        L.append(f"  {e.matter:<10} {varga:<16} {e.verdict.upper():<20} {e.reader}")
    L.append("=" * 72)
    return "\n".join(L)
