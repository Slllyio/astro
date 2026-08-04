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
    d20_core: Optional[str]             # the Vimsamsa deep-read body (existing)
    d60_core: Optional[str]             # the Shashtiamsa deep-read body (existing)
    frame: str


_FRAME: Final[str] = (
    "The Jaimini frame, quoted from Raman's own Studies in Jaimini Astrology — a walled "
    "layer: nothing here feeds or alters the Parashari natal verdicts, and as everywhere "
    "in this report it is a statement of the method, never a validated prediction.")


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
        return None
    d20 = next((body for label, body in r.divisional if label.startswith("D-20")), None)
    d60 = next((body for label, body in r.divisional if label.startswith("D-60")), None)
    return KarmicEvolution(
        atmakaraka=ak,
        karakamsa=getattr(r.synthesis, "karakamsa", "") or "",
        upapada=getattr(r.synthesis, "upapada", "") or "",
        doctrine_quote=quote,
        doctrine_cite=f"JAIMINI-9:{KARAKAMSA_DOCTRINE[0]}",
        d20_core=d20, d60_core=d60, frame=_FRAME)
