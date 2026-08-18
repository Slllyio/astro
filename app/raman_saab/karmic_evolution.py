"""Karmic evolution (v30) — the walled Jaimini layer the 2026-08-04 lift enabled.

STRICTLY CLASSICAL, per the user's spec: the Atmakaraka (the locked 7-karaka scheme),
the Karakamsa (the AK's navamsa sign — already computed in the chart signature), the
Upapada, Raman's own Jaimini doctrine QUOTED VERBATIM by frozen range (JAIMINI-9:799-847
— character and mind from Karakamsa, predispositions, education, profession, the nature
of death generally, charities/devotion/moksha), and the D-20 (Vimsamsa, spiritual) and
D-60 (Shashtiamsa, totality) deep-read cores the report already builds. No modern
spirituality; every line quoted or re-read.

WALLED (the firewall-lift scope rule): natal verdict code never imports this module; a
test pins the wall. The death-nature sentence inside the verbatim block stays a labeled
quote under the method-not-prediction frame — nothing is composed atop it.

Usage:
    from app.raman_saab.karmic_evolution import build_karmic_evolution
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

from app.raman_saab.doctrine.sources import Citation, passage

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

#: JAIMINI-9's karakamsa doctrine summary — frozen range (mined 2026-08-04).
KARAKAMSA_DOCTRINE: Final[tuple[int, int]] = (799, 847)

CITED_ANCHORS: Final[tuple[Citation, ...]] = (Citation("JAIMINI-9", 799),)


@dataclass(frozen=True)
class KarmicEvolution:
    atmakaraka: str
    karakamsa: str                      # the AK's navamsa sign (chart signature value)
    upapada: str
    doctrine_quote: str                 # JAIMINI-9 verbatim
    doctrine_cite: str
    d20_core: Optional[str]             # one-sentence D-20 domain re-read (Wave-2, 2026-08-18)
    d60_core: Optional[str]             # one-sentence D-60 domain re-read (Wave-2, 2026-08-18)
    frame: str


_FRAME: Final[str] = (
    "The Jaimini frame, quoted from Raman's own Studies in Jaimini Astrology — a walled "
    "layer: nothing here feeds or alters the Parashari natal verdicts, and as everywhere "
    "in this report it is a statement of the method, never a validated prediction.")


def _d20_reread(body: Optional[str]) -> Optional[str]:
    """One-sentence domain re-read of the D-20 (Vimsamsa, spiritual) deep-read — the verdict
    banner the body itself prints, restated for this layer. Wave-2 (2026-08-18), per the
    report critique: the karmic chapter previously EMBEDDED the full D-20 ASCII block
    verbatim (duplicative, unsynthesized). REPORT COMPLETENESS is preserved by construction:
    nothing is hidden — the full D-20 block still renders, untrimmed, at its own home in the
    Divisional deep-reads section; this sentence is a pointer-re-read, not a replacement of
    any rendered data."""
    if body is None:
        return None
    m = re.search(r">>>\s*SPIRITUAL:\s*([A-Za-z-]+)", body)
    if m is None:
        return ("the spiritual thread reads in the D-20 Vimsamsa block, rendered in full "
                "in the Divisional deep-reads section")
    return (f"the spiritual thread (9th-house method, D-20 corroborating) reads "
            f"{m.group(1)} - the full Vimsamsa block renders, untrimmed, in the "
            f"Divisional deep-reads section")


def _d60_reread(body: Optional[str]) -> Optional[str]:
    """One-sentence domain re-read of the D-60 (Shashtiamsa, accumulated karma) deep-read —
    its varga-lagna seat and strong/weak lists, restated. Same REPORT COMPLETENESS note as
    `_d20_reread`: the full D-60 block still renders at its home section; nothing hidden."""
    if body is None:
        return None
    lagna = re.search(r"lagna\s*:\s*(\w+)\s*\(lord\s+(\w+),\s*([\w-]+) in\s*\n?\s*this varga\)",
                      body)
    strong = re.search(r"strong here \(exalt/own\):\s*([^\n]+)", body)
    weak = re.search(r"weak here \(debilitated\):\s*([^\n]+)", body)
    if lagna is None:
        return ("the accumulated-karma lens reads in the D-60 Shashtiamsa block, rendered "
                "in full in the Divisional deep-reads section")
    s = (f"the accumulated-karma lens (D-60) seats its lagna in {lagna.group(1)} under "
         f"{lagna.group(2)} ({lagna.group(3)} in this varga)")
    if strong:
        s += f"; standing strong here: {strong.group(1).strip()}"
    if weak:
        s += f"; debilitated: {weak.group(1).strip()}"
    return s + " - the full Shashtiamsa block renders, untrimmed, in the Divisional deep-reads section"


def build_karmic_evolution(r: "DetailedReport") -> Optional[KarmicEvolution]:
    from app.raman_saab.primitives.chara_karakas import chara_karakas

    try:
        ak = chara_karakas(r.chart).get("AK")
    except Exception:  # noqa: BLE001 — sparse/Track-B
        ak = None
    if ak is None:
        return None
    p = passage(f"JAIMINI-9:{KARAKAMSA_DOCTRINE[0]}-{KARAKAMSA_DOCTRINE[1]}")
    quote = ""
    if isinstance(p, dict):
        quote = re.sub(r"\s*\n\s*", " ", p.get("text", "")).strip()
    if not quote:
        # REPORT COMPLETENESS: the AK, Karakamsa, Upapada and the D-20/D-60 cores below
        # are COMPUTED — a missing verbatim pull (corpus not vendored on this machine)
        # must never hide them. The honest-absence line flows through the existing quote
        # field, so every renderer shows the section unchanged.
        quote = (f"Raman's Jaimini doctrine at JAIMINI-9:{KARAKAMSA_DOCTRINE[0]}-"
                 f"{KARAKAMSA_DOCTRINE[1]} - corpus not mounted on this machine")
    d20 = next((body for label, body in r.divisional if label.startswith("D-20")), None)
    d60 = next((body for label, body in r.divisional if label.startswith("D-60")), None)
    return KarmicEvolution(
        atmakaraka=ak,
        karakamsa=getattr(r.synthesis, "karakamsa", "") or "",
        upapada=getattr(r.synthesis, "upapada", "") or "",
        doctrine_quote=quote,
        doctrine_cite=f"JAIMINI-9:{KARAKAMSA_DOCTRINE[0]}",
        d20_core=_d20_reread(d20), d60_core=_d60_reread(d60), frame=_FRAME)
