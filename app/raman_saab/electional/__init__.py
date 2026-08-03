"""Electional (Muhurtha) subsystem — WALLED, per the 2026-08-03 firewall-lift scope rule.

This package encodes B. V. Raman's *Muhurtha — Electional Astrology* (tag MUHURTHA) plus the
electional rules of ASP ch.XV. It may import natal primitives; NATAL VERDICT CODE MUST NEVER
IMPORT THIS PACKAGE (the VERDICT-AUTHORITY invariant, extended). Outputs are statements of
Raman's electional method — never validated predictions — and carry the Measured-Truth
framing wherever surfaced. Full decision record: docs/raman_saab/DOCTRINE_BACKLOG.md
"PRASNA + MUHURTHA firewall LIFT".
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.sources import Citation

#: Every doctrine anchor this package cites — enumerated here so `source_lock.iter_citations`
#: can pin the underlying corpus lines exactly like the natal registries' citations.
CITED_ANCHORS: Final[tuple[Citation, ...]] = (
    Citation("MUHURTHA-3", 41), Citation("MUHURTHA-3", 66), Citation("MUHURTHA-3", 88),
    Citation("MUHURTHA-3", 104), Citation("MUHURTHA-3", 157),
    Citation("MUHURTHA-2", 170), Citation("MUHURTHA-2", 194), Citation("MUHURTHA-2", 202),
    Citation("MUHURTHA-2", 205),
    Citation("MUHURTHA-4", 290),
    Citation("MUHURTHA-8", 1171),
    Citation("MUHURTHA-10", 226),
    Citation("MUHURTHA-18", 767), Citation("MUHURTHA-18", 861),
    Citation("ASP-15", 21), Citation("ASP-15", 55), Citation("ASP-15", 82),
    Citation("ASP-15", 101), Citation("ASP-15", 116), Citation("ASP-15", 145),
    Citation("ASP-15", 155),
)
