"""Birth-time rectification & time discovery for the raman_saab engine.

Encodes Raman's own rectification method — "birth times can be rectified only by men of
experience by a consideration of pronounced life incidents" (HPA ch.12) — as a scored
search over (ayanamsa x birth-time equivalence class) candidates, with dated life events
(Time-of-Fructification doctrine, HTJAH-I/II) and non-dated natal facts as evidence.

Usage:
    from app.raman_saab.rectification import LifeEvent, NatalFact, resolve_fact
"""
from __future__ import annotations

from app.raman_saab.rectification.events import (
    EVENT_TAXONOMY, EventSpec, LifeEvent, NatalFact, resolve_fact)
from app.raman_saab.rectification.report import RectificationReport, to_markdown, to_text
from app.raman_saab.rectification.session import RectificationSession

__all__ = ["EVENT_TAXONOMY", "EventSpec", "LifeEvent", "NatalFact", "resolve_fact",
           "RectificationReport", "RectificationSession", "to_markdown", "to_text"]
