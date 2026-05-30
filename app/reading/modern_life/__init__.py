"""V1.5 modern-life interpretive layer over V1 domain readings.

This package adds *advisory* (classification="primitive") modern-life signals
on top of the classical V1 domain readings. It does NOT modify any V1 domain
file or sequence — the existing architectural-purity tests therefore continue
to pass unchanged.

Discipline (per v1.5 spec):

- Every Finding emitted from this package uses ``classification="primitive"``
  to mark it as **advisory context, not prediction**. The V1 promise/trigger
  pipeline retains full authority over "this will happen" claims.
- Mental-health framing is NOT reduced to a "graha-peeda" verdict: detectors
  check Moon-Mercury (anxiety), Moon-Saturn (depression), Moon-Rahu
  (dissociation), the 4H (emotional foundation) and the nakshatra-lord of
  the Moon. The verdict labels these as "modern psychological context",
  not as fated illness.
- Queer / non-binary partnership signals carry a mandatory disclaimer in
  ``evidence``: ``"note=mainstream_practice_reads_partnership_gender_agnostically"``.
  The intent is to *surface* — not assume — identity fluidity markers
  practitioners flag.
- Every finding has ``direction="positive"``, ``"negative"`` or ``"neutral"``;
  none claim certainty.

The synthesizer attaches detected findings to each domain's existing
``cross_checks`` list (preserves the V1 schema; adds context not predictions).
"""
from __future__ import annotations

from app.reading.modern_life.career import detect_modern_career
from app.reading.modern_life.children import detect_modern_children
from app.reading.modern_life.education import detect_modern_education
from app.reading.modern_life.health import detect_modern_health
from app.reading.modern_life.marriage import detect_modern_marriage
from app.reading.modern_life.synthesizer import enrich_with_modern_signals
from app.reading.modern_life.wealth import detect_modern_wealth

__all__ = [
    "detect_modern_career",
    "detect_modern_marriage",
    "detect_modern_health",
    "detect_modern_wealth",
    "detect_modern_children",
    "detect_modern_education",
    "enrich_with_modern_signals",
]
