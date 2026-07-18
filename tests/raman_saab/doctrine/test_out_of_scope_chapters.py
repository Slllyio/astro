"""Out-of-scope-CHAPTER firewall (doctrine-gate hardening, 2026-07-18).

The book registry admits whole BOOKS; but two live Raman books contain chapters in
other systems: AFB ch.11 (horary) / ch.12 (gochara), HPA ch.27 (prasna) / ch.31
(mundane) / ch.33 (annual) / ch.34 (gochara). The registry's "strictly Parashari
natal" guarantee is enforced here at the CITATION level: no live rule / yoga /
signification / rectification-event citation may reference those chapters. (The
preferred structural fix — per-chapter scoping on BookEntry — is recorded in the
doctrine gate's P1 review; this pinned test is the agreed minimum.)
"""
from __future__ import annotations

from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.doctrine.significations import SIGNIFICATIONS
from app.raman_saab.doctrine.yogas import YOGAS
from app.raman_saab.rectification.events import EVENT_TAXONOMY

_BANNED_WORKS: frozenset[str] = frozenset({
    "AFB-11", "AFB-12",                      # horary, gochara
    "HPA-27", "HPA-31", "HPA-33", "HPA-34",  # prasna, mundane, annual, gochara
})


def _all_citations():
    for rule in ALL_RULES:
        yield f"rule {rule.id}", rule.source
    for yoga in YOGAS:
        yield f"yoga {yoga.id}", yoga.source
    for sigs in SIGNIFICATIONS.values():
        for sig in sigs:
            yield f"signification {sig.key}", sig.source
    for spec in EVENT_TAXONOMY.values():
        yield f"event {spec.key}", spec.source


def test_no_live_citation_uses_an_out_of_scope_chapter() -> None:
    """Every citation across rules, yogas, significations and the rectification event
    taxonomy stays off the horary/gochara/mundane/annual chapters of the live books."""
    offenders = [(who, c.work, c.line) for who, c in _all_citations()
                 if c.work in _BANNED_WORKS]
    assert not offenders, f"out-of-scope-chapter citations: {offenders}"
