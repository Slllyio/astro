"""Graha chapters — Raman's own words per planet, by frozen line range (HPA).

Every table below stores LINE RANGES into the live corpus, rendered verbatim at build
time via ``sources.passage`` — zero transcription risk, every word Raman's own, every
range under the source lock. Mined 2026-08-03 by anchor derivation over the chapter
texts (the 81 Bhukti pairs verified to walk the Vimshottari order with zero breaks; the
per-sign Dasa sections delimited by the printed "X's Dasa—N Years" headers).

Tables:
- ``AD_RESULTS[(md, ad)]`` — HPA-24's sub-period paragraphs, all 81 Vimshottari pairs.
- ``MD_SIGN_RESULTS[md]`` — HPA-24's per-sign Dasa sections ("The Dasa of the Sun in
  Aries..."); the extractor pulls the native's sign paragraph out of the block.
- ``HOUSE_BLOCKS[planet]`` — HPA-21 "Planets in Different Bhavas": the planet's whole
  block; the extractor pulls the native's house paragraph (OCR-fuzzed ordinals).
- ``SIGN_BLOCKS[planet]`` — HPA-22 "Planets in Different Rasis" (seven grahas; Rahu/Ketu
  carry HPA-22:522's aprakasha note instead — an honest absence, nothing invented).
- ``TRANSIT_BLOCKS[planet]`` — HPA-34 Gocharaphala per-planet transit-results sections
  (the text behind the already-encoded favourable-house table in ``primitives/transits``;
  Rahu/Ketu have no HPA-34 paragraphs — recorded absence).

Usage:
    from app.raman_saab.doctrine.lookups.graha_chapters import (
        ad_result, house_result, md_sign_result, sign_result, transit_result)
"""
from __future__ import annotations

import re
from typing import Final, Optional

from app.raman_saab.doctrine.sources import Citation, passage

_HPA21: Final[str] = "HPA-21"
_HPA22: Final[str] = "HPA-22"
_HPA24: Final[str] = "HPA-24"
_HPA34: Final[str] = "HPA-34"

#: HPA-24 — every Vimshottari (Mahadasha lord, Bhukti lord) sub-period paragraph.
AD_RESULTS: Final[dict[tuple[str, str], tuple[int, int]]] = {
    ("Sun", "Sun"): (222, 232), ("Sun", "Moon"): (233, 242), ("Sun", "Mars"): (243, 255),
    ("Sun", "Rahu"): (256, 264), ("Sun", "Jupiter"): (265, 275),
    ("Sun", "Saturn"): (276, 286), ("Sun", "Mercury"): (287, 298),
    ("Sun", "Ketu"): (299, 310), ("Sun", "Venus"): (311, 319),
    ("Moon", "Moon"): (368, 378), ("Moon", "Mars"): (379, 389),
    ("Moon", "Rahu"): (390, 401), ("Moon", "Jupiter"): (402, 410),
    ("Moon", "Saturn"): (411, 418), ("Moon", "Mercury"): (419, 432),
    ("Moon", "Ketu"): (433, 444), ("Moon", "Venus"): (445, 454),
    ("Moon", "Sun"): (455, 467),
    ("Mars", "Mars"): (512, 528), ("Mars", "Rahu"): (529, 541),
    ("Mars", "Jupiter"): (542, 553), ("Mars", "Saturn"): (554, 561),
    ("Mars", "Mercury"): (562, 572), ("Mars", "Ketu"): (573, 583),
    ("Mars", "Venus"): (584, 595), ("Mars", "Sun"): (596, 608),
    ("Mars", "Moon"): (609, 615),
    ("Rahu", "Rahu"): (680, 691), ("Rahu", "Jupiter"): (692, 701),
    ("Rahu", "Saturn"): (702, 710), ("Rahu", "Mercury"): (711, 725),
    ("Rahu", "Ketu"): (726, 735), ("Rahu", "Venus"): (736, 745),
    ("Rahu", "Sun"): (746, 758), ("Rahu", "Moon"): (759, 768),
    ("Rahu", "Mars"): (769, 781),
    ("Jupiter", "Jupiter"): (843, 851), ("Jupiter", "Saturn"): (852, 864),
    ("Jupiter", "Mercury"): (865, 874), ("Jupiter", "Ketu"): (875, 883),
    ("Jupiter", "Venus"): (884, 898), ("Jupiter", "Sun"): (899, 905),
    ("Jupiter", "Moon"): (906, 914), ("Jupiter", "Mars"): (915, 924),
    ("Jupiter", "Rahu"): (925, 930),
    ("Saturn", "Saturn"): (983, 994), ("Saturn", "Mercury"): (995, 1005),
    ("Saturn", "Ketu"): (1006, 1015), ("Saturn", "Venus"): (1016, 1023),
    ("Saturn", "Sun"): (1024, 1033), ("Saturn", "Moon"): (1034, 1045),
    ("Saturn", "Mars"): (1046, 1053), ("Saturn", "Rahu"): (1054, 1060),
    ("Saturn", "Jupiter"): (1061, 1067),
    ("Mercury", "Mercury"): (1127, 1136), ("Mercury", "Ketu"): (1137, 1145),
    ("Mercury", "Venus"): (1146, 1155), ("Mercury", "Sun"): (1156, 1164),
    ("Mercury", "Moon"): (1165, 1173), ("Mercury", "Mars"): (1174, 1185),
    ("Mercury", "Rahu"): (1186, 1199), ("Mercury", "Jupiter"): (1200, 1207),
    ("Mercury", "Saturn"): (1208, 1220),
    ("Ketu", "Ketu"): (1294, 1302), ("Ketu", "Venus"): (1303, 1309),
    ("Ketu", "Sun"): (1310, 1317), ("Ketu", "Moon"): (1318, 1324),
    ("Ketu", "Mars"): (1325, 1338), ("Ketu", "Rahu"): (1339, 1346),
    ("Ketu", "Jupiter"): (1347, 1354), ("Ketu", "Saturn"): (1355, 1366),
    ("Ketu", "Mercury"): (1367, 1374),
    ("Venus", "Venus"): (1445, 1452), ("Venus", "Sun"): (1453, 1459),
    ("Venus", "Moon"): (1460, 1469), ("Venus", "Mars"): (1470, 1481),
    ("Venus", "Rahu"): (1482, 1489), ("Venus", "Jupiter"): (1490, 1501),
    ("Venus", "Saturn"): (1502, 1514), ("Venus", "Mercury"): (1515, 1524),
    ("Venus", "Ketu"): (1525, 1539),
}

#: HPA-24 — the per-sign Dasa sections, delimited by the printed Dasa headers.
MD_SIGN_RESULTS: Final[dict[str, tuple[int, int]]] = {
    "Sun": (160, 219), "Moon": (321, 366), "Mars": (469, 510), "Rahu": (617, 678),
    "Jupiter": (783, 840), "Saturn": (932, 980), "Mercury": (1069, 1125),
    "Ketu": (1222, 1291), "Venus": (1376, 1443),
}

#: HPA-21 — the planet blocks of "Planets in Different Bhavas or Houses".
HOUSE_BLOCKS: Final[dict[str, tuple[int, int]]] = {
    "Sun": (23, 104), "Moon": (105, 184), "Mars": (185, 247), "Mercury": (248, 322),
    "Jupiter": (323, 392), "Venus": (393, 459), "Saturn": (460, 527),
    "Rahu": (528, 614),
}

#: HPA-22 — the planet blocks of "Planets in Different Rasis or Signs" (7 grahas; the
#: nodes are aprakasha, HPA-22:522 — no per-sign results are stated).
SIGN_BLOCKS: Final[dict[str, tuple[int, int]]] = {
    "Sun": (23, 80), "Moon": (81, 186), "Mars": (187, 267), "Mercury": (268, 337),
    "Jupiter": (338, 402), "Venus": (403, 460), "Saturn": (461, 521),
}

#: HPA-34 — the per-planet Gocharaphala sections (no node paragraphs are printed).
TRANSIT_BLOCKS: Final[dict[str, tuple[int, int]]] = {
    "Sun": (46, 95), "Moon": (96, 124), "Mars": (383, 420), "Mercury": (421, 460),
    "Jupiter": (461, 505), "Venus": (506, 545), "Saturn": (546, 596),
}

#: OCR-fuzzed ordinal words per house, for sub-extraction inside a planet block.
_HOUSE_WORDS: Final[dict[int, tuple[str, ...]]] = {
    1: ("First house", "First House", "Ascendant"), 2: ("Second",), 3: ("Third",),
    4: ("Fourth",), 5: ("Fifth",), 6: ("Sixth",), 7: ("Seventh",), 8: ("Eighth", "Eighth"),
    9: ("Ninth",), 10: ("Tenth",), 11: ("Eleventh",), 12: ("Twelfth", "Twelth"),
}

_SIGN_WORDS: Final[dict[int, tuple[str, ...]]] = {
    1: ("Aries",), 2: ("Taurus", "Tauras"), 3: ("Gemini",), 4: ("Cancer",),
    5: ("Leo",), 6: ("Virgo",), 7: ("Libra",), 8: ("Scorpio",),
    9: ("Sagittarius", "Sagittarins", "Sagit"), 10: ("Capricorn",),
    11: ("Aquarius", "Aqnarius", "Aqua"), 12: ("Pisces",),
}

#: How many houses from the Moon count favourable per transit — already encoded with its
#: own citation in primitives/transits; the HPA-34 blocks above carry the result TEXT.

_ALL_ANCHORS: Final[tuple[tuple[str, int], ...]] = tuple(
    [(f"{_HPA24}", s) for s, _ in AD_RESULTS.values()]
    + [(f"{_HPA24}", s) for s, _ in MD_SIGN_RESULTS.values()]
    + [(f"{_HPA21}", s) for s, _ in HOUSE_BLOCKS.values()]
    + [(f"{_HPA22}", s) for s, _ in SIGN_BLOCKS.values()]
    + [(f"{_HPA34}", s) for s, _ in TRANSIT_BLOCKS.values()])

#: For source_lock enumeration — one Citation per table entry start line.
CITED_ANCHORS: Final[tuple[Citation, ...]] = tuple(
    Citation(work, line) for work, line in _ALL_ANCHORS)


def _clean(text: str) -> str:
    """Join OCR hyphenation and collapse whitespace; the words stay Raman's."""
    text = re.sub(r"[¬­-]\s*\n\s*", "", text)      # hyphen-break joins
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _pull(work: str, start: int, end: int) -> Optional[str]:
    p = passage(f"{work}:{start}-{end}")
    if isinstance(p, dict):
        return _clean(p.get("text", "")) or None
    return None


def _sub_extract(work: str, block: tuple[int, int], words: tuple[str, ...],
                 stop_words: tuple[tuple[str, ...], ...]) -> Optional[str]:
    """Pull the paragraph starting at the first line containing any of `words`, ending
    before the next line that starts any OTHER entry (`stop_words`). None when the OCR
    defeated the anchor — an honest absence, never a guess."""
    p = passage(f"{work}:{block[0]}-{block[1]}")
    if not isinstance(p, dict):
        return None
    lines = p.get("text", "").split("\n")
    lo = None
    for i, ln in enumerate(lines):
        if any(w in ln for w in words):
            lo = i
            break
    if lo is None:
        return None
    hi = len(lines)
    flat_stops = [w for grp in stop_words for w in grp if w not in words]
    for j in range(lo + 1, len(lines)):
        if any(s in lines[j] for s in flat_stops):
            hi = j
            break
    return _clean("\n".join(lines[lo:hi])) or None


def ad_result(md: str, ad: str) -> Optional[tuple[str, str]]:
    """(verbatim HPA-24 sub-period paragraph, 'HPA-24:start') for a Vimshottari pair."""
    rng = AD_RESULTS.get((md, ad))
    if rng is None:
        return None
    text = _pull(_HPA24, *rng)
    return (text, f"{_HPA24}:{rng[0]}") if text else None


def md_sign_result(md: str, sign: int) -> Optional[tuple[str, str]]:
    """The Dasa-lord-in-the-native's-sign paragraph out of the MD's per-sign section."""
    rng = MD_SIGN_RESULTS.get(md)
    if rng is None:
        return None
    text = _sub_extract(_HPA24, rng, _SIGN_WORDS[sign], tuple(_SIGN_WORDS.values()))
    return (text, f"{_HPA24}:{rng[0]}") if text else None


def house_result(planet: str, house: int) -> Optional[tuple[str, str]]:
    """HPA-21's planet-in-house paragraph for the native's placement."""
    rng = HOUSE_BLOCKS.get(planet)
    if rng is None:
        return None
    text = _sub_extract(_HPA21, rng, _HOUSE_WORDS[house], tuple(_HOUSE_WORDS.values()))
    return (text, f"{_HPA21}:{rng[0]}") if text else None


def sign_result(planet: str, sign: int) -> Optional[tuple[str, str]]:
    """HPA-22's planet-in-sign paragraph; None for the nodes (aprakasha, HPA-22:522)."""
    rng = SIGN_BLOCKS.get(planet)
    if rng is None:
        return None
    text = _sub_extract(_HPA22, rng, _SIGN_WORDS[sign], tuple(_SIGN_WORDS.values()))
    return (text, f"{_HPA22}:{rng[0]}") if text else None


def transit_result(planet: str) -> Optional[tuple[str, str]]:
    """HPA-34's whole per-planet Gocharaphala section (the house-by-house transit text)."""
    rng = TRANSIT_BLOCKS.get(planet)
    if rng is None:
        return None
    text = _pull(_HPA34, *rng)
    return (text, f"{_HPA34}:{rng[0]}") if text else None
