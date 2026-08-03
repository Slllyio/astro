"""Horary (Prasna) subsystem — WALLED, per the 2026-08-03 firewall-lift scope rule.

Encodes Neelakantha's *Prasna Tantra* as translated and annotated by B. V. Raman (tag
PRASNA), with the Tajika machinery Raman himself defers to his *Varshaphal* for (tag VARSHA,
lifted same day) and the Raman-authored horary chapters inside live books (HPA-27, AFB-11).
May import natal primitives; NATAL VERDICT CODE MUST NEVER IMPORT THIS PACKAGE. Death/
lifespan/serious-illness/self-harm queries are excluded IN CODE (the /ai-interpret
precedent). Outputs are statements of the Prasna Tantra method — never validated
predictions. Full record: docs/raman_saab/DOCTRINE_BACKLOG.md "PRASNA + MUHURTHA firewall
LIFT".
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.sources import Citation

#: Every doctrine anchor this package cites — enumerated for `source_lock.iter_citations`.
CITED_ANCHORS: Final[tuple[Citation, ...]] = (
    Citation("PRASNA-2", 258),      # Tajika aspect set + Deeptamsa orb table
    Citation("PRASNA-4", 1068),     # Ithasala (stanzas 54-55) + Poorna within 1 degree
    Citation("PRASNA-4", 1085),     # the speed order, Saturn slowest -> Moon fastest
    Citation("PRASNA-4", 1122),     # Easarapha/Musaripha (stanza 56)
    Citation("PRASNA-4", 1151),     # Naktha (stanza 57)
    Citation("PRASNA-4", 1218),     # Yamaya (stanza 60)
    Citation("PRASNA-4", 1255),     # Kamboola (stanza 61) + grade ladder
    Citation("VARSHA-7", 43),       # Iddasala orb rule: the deeptamsas must mutually mingle
    Citation("VARSHA-7", 84),       # Sahams: the general rule (+30 no-lagna-between)
    Citation("VARSHA-7", 100),      # Punya Saham day/night formula + worked 30-30 example
    Citation("VARSHA-7", 190),      # Lords of sahams: the rasi lord where the saham falls
    Citation("PRASNA-49", 107),     # Karyasiddhi stanzas 3-4: the four full-success configs
    Citation("PRASNA-49", 119),     # Karyesa = lord of the query's house
    Citation("PRASNA-49", 137),     # stanzas 5-8: the 25/50/75/100 ladder
)
