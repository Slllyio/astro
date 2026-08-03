"""Tarabala + Chandrabala — the two universal election factors (MUHURTHA-3).

Raman: "there are three factors which are common to almost all elections ... (a) Tarabala or
strength of constellation, (b) Chandrabala or Lunar strength and (c) Panchaka or five-source
energy. These three should be satisfactorily disposed. Otherwise an election chart will lose
its significance." (MUHURTHA-3:25-32.)

Tarabala (MUHURTHA-3:34-63): count from the Janma nakshatra to the day's nakshatra
(inclusive), divide by 9; the remainder names the tara — 1 Janma (danger to body), 2 Sampat
(wealth), 3 Vipat (dangers/losses), 4 Kshema (prosperity), 5 Pratyak (obstacles), 6 Sadhana
(realisation of ambitions), 7 Naidhana (dangers), 8 Mitra (good), 9/0 Parama Mitra (very
favourable). Worked example: Aswini -> Sravana counts 22, remainder 4 = Kshema, "Tarabala is
good" (MUHURTHA-3:57-63).

Ghati exceptions (MUHURTHA-3:179-195): when the day is otherwise favourable, only the
negative opening ghatis of the four bad taras need avoiding — Janma 1, Vipat 7, Pratyak 3,
Naidhana 8 ghatis "respectively" (as printed).

Janma-nakshatra activity split (MUHURTHA-3:197-206): a day ruled by one's own star is
ordinarily unfavourable, BUT favourable without exception for nuptials, sacrifices, first
feeding, agriculture, upanayanam, coronation, buying lands, learning the alphabet — and
inauspicious for war, sexual union, shaving, medical treatment, travel, marriage ("for a
woman, Janma Nakshatra would be quite favourable for marriage").

Chandrabala (MUHURTHA-3:66-71): the election Moon "should not occupy ... the 6th, 8th or
12th from the person's Janma Rasi". Double-failure worked example (Mrigasira native,
Bharani day): "neither Tarabala ... nor Chandrabala ... the day is most inauspicious"
(MUHURTHA-3:72-79).

Usage:
    from app.raman_saab.electional.tarabala import tarabala, chandrabala
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.doctrine.sources import Citation

#: MUHURTHA-3:41-52 — the nine taras, index 1..9, with Raman's quality words.
TARA_NAMES: Final[tuple[str, ...]] = (
    "Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhana", "Naidhana", "Mitra",
    "Parama Mitra")
_FAVOURABLE: Final[frozenset[int]] = frozenset({2, 4, 6, 8, 9})

#: MUHURTHA-3:179-195 — negative opening ghatis of the four bad taras (as printed:
#: "the first, 7, 3 and 8 ghaties respectively" for Janma, Vipat, Pratyak, Naidhana).
NEGATIVE_OPENING_GHATIS: Final[dict[int, int]] = {1: 1, 3: 7, 5: 3, 7: 8}

#: MUHURTHA-3:197-206 — the Janma-nakshatra activity split.
JANMA_STAR_FAVOURABLE_ACTS: Final[frozenset[str]] = frozenset({
    "nuptials", "sacrifices", "first_feeding", "agriculture", "upanayanam", "coronation",
    "buying_lands", "learning_alphabet"})
JANMA_STAR_INAUSPICIOUS_ACTS: Final[frozenset[str]] = frozenset({
    "war", "sexual_union", "shaving", "medical_treatment", "travel", "marriage"})

#: MUHURTHA-3:66-71 — houses from Janma Rasi the election Moon must avoid.
CHANDRABALA_BAD_HOUSES: Final[frozenset[int]] = frozenset({6, 8, 12})


@dataclass(frozen=True)
class Tarabala:
    tara: int                 # 1..9
    name: str
    favourable: bool
    negative_opening_ghatis: int   # 0 when none; else the printed ghati count to avoid
    source: Citation


def tarabala(janma_nakshatra: int, day_nakshatra: int) -> Tarabala:
    """Raman's Tarabala count (MUHURTHA-3:34-63): inclusive count % 9, remainder -> tara."""
    if not (1 <= janma_nakshatra <= 27 and 1 <= day_nakshatra <= 27):
        raise ValueError("nakshatra numbers must be 1..27")
    count = (day_nakshatra - janma_nakshatra) % 27 + 1
    tara = (count - 1) % 9 + 1
    return Tarabala(
        tara=tara, name=TARA_NAMES[tara - 1], favourable=tara in _FAVOURABLE,
        negative_opening_ghatis=NEGATIVE_OPENING_GHATIS.get(tara, 0),
        source=Citation("MUHURTHA-3", 41))


def chandrabala(janma_rasi: int, election_moon_rasi: int) -> bool:
    """True when the election Moon is NOT 6th/8th/12th from the Janma Rasi
    (MUHURTHA-3:66-71)."""
    if not (1 <= janma_rasi <= 12 and 1 <= election_moon_rasi <= 12):
        raise ValueError("rasi numbers must be 1..12")
    house = (election_moon_rasi - janma_rasi) % 12 + 1
    return house not in CHANDRABALA_BAD_HOUSES
