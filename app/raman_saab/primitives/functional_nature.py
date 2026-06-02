from __future__ import annotations
from typing import Final, Literal
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.constants import SIGN_LORDS

Nature = Literal["benefic", "malefic", "neutral", "yogakaraka"]

NATURAL_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
NATURAL_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})

_VISIBLE: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONA: Final[frozenset[int]] = frozenset({1, 5, 9})

# B.V. Raman's per-Lagna functional classification — PRINTED TABLE is authoritative.
# Source: How to Judge a Horoscope Vol I, HTJAH-I:523-566 (overview §4).
# Verified against on-disk corpus chapter_001_full-text-unsplit.md lines 523-566.
# asc_sign 1..12 (Aries..Pisces) -> planet -> "benefic" | "malefic" | "neutral".
# 9 Lagnas print all 7 visible planets; 3 cells are HOLES Raman did not print
# (Aries-Moon, Gemini-Saturn, Aquarius-Saturn) — filled below via the generating
# rules (HTJAH-I:573-604) and MARKED for doctrine-reviewer scrutiny.
_FUNCTIONAL_TABLE: Final[dict[int, dict[str, str]]] = {
    # Aries: HTJAH-I:525-527. Jupiter best benefic, Mars benefic, Sun benefic.
    # Saturn, Mercury, Venus malefic. Moon NOT printed -> HOLE (REVIEW).
    1:  {"Jupiter": "benefic", "Mars": "benefic", "Sun": "benefic",
         "Mercury": "malefic", "Saturn": "malefic", "Venus": "malefic",
         "Moon": "neutral"},   # HOLE: Aries-Moon (4th lord, luminary) — REVIEW
    # Taurus: HTJAH-I:531-534. Saturn, Mercury, Mars, Sun benefic.
    # Jupiter, Moon evil. Venus neutral (lord of Lagna).
    2:  {"Saturn": "benefic", "Mercury": "benefic", "Mars": "benefic", "Sun": "benefic",
         "Jupiter": "malefic", "Moon": "malefic", "Venus": "neutral"},
    # Gemini: HTJAH-I:536-538. Venus benefic. Mars, Jupiter, Sun malefic.
    # Moon, Mercury neutral. Saturn NOT printed -> HOLE (REVIEW).
    3:  {"Venus": "benefic",
         "Mars": "malefic", "Jupiter": "malefic", "Sun": "malefic",
         "Moon": "neutral", "Mercury": "neutral",
         "Saturn": "neutral"},   # HOLE: Gemini-Saturn owns 8th(dusthana)+9th(trikona);
                                 # the 8th taint tempers the 9th -> neutral (Raman omitted). REVIEW.
    # Cancer: HTJAH-I:540-541. Jupiter, Mars benefic (Mars better as 5th+10th lord).
    # Venus, Mercury evil. Saturn, Moon, Sun neutrals.
    4:  {"Mars": "benefic", "Jupiter": "benefic",
         "Venus": "malefic", "Mercury": "malefic",
         "Saturn": "neutral", "Moon": "neutral", "Sun": "neutral"},
    # Leo: HTJAH-I:543-544. Mars, Sun benefic (Mars most auspicious).
    # Mercury, Venus malefic. Jupiter, Moon, Saturn neutrals.
    5:  {"Mars": "benefic", "Sun": "benefic",
         "Mercury": "malefic", "Venus": "malefic",
         "Jupiter": "neutral", "Moon": "neutral", "Saturn": "neutral"},
    # Virgo: HTJAH-I:546-547. Venus alone best benefic.
    # Moon, Mars, Jupiter evil. Saturn, Sun, Mercury neutrals.
    6:  {"Venus": "benefic",
         "Moon": "malefic", "Mars": "malefic", "Jupiter": "malefic",
         "Saturn": "neutral", "Sun": "neutral", "Mercury": "neutral"},
    # Libra: HTJAH-I:549-550. Saturn, Mercury, Venus benefic (Saturn best).
    # Sun, Jupiter, Moon malefic. Mars "feeble benefic" -> NEUTRAL.
    7:  {"Saturn": "benefic", "Mercury": "benefic", "Venus": "benefic",
         "Sun": "malefic", "Jupiter": "malefic", "Moon": "malefic",
         "Mars": "neutral"},   # Libra-Mars "feeble benefic" -> NEUTRAL (HTJAH-I:550)
    # Scorpio: HTJAH-I:552-553. Moon best benefic, Jupiter, Sun benefic.
    # Mercury, Venus evil. Mars, Saturn neutrals.
    8:  {"Moon": "benefic", "Jupiter": "benefic", "Sun": "benefic",
         "Mercury": "malefic", "Venus": "malefic",
         "Mars": "neutral", "Saturn": "neutral"},
    # Sagittarius: HTJAH-I:555-556. Mars, Sun benefic.
    # Venus, Saturn, Mercury evil. Jupiter, Moon neutrals.
    9:  {"Mars": "benefic", "Sun": "benefic",
         "Venus": "malefic", "Saturn": "malefic", "Mercury": "malefic",
         "Jupiter": "neutral", "Moon": "neutral"},
    # Capricorn: HTJAH-I:558-560. Venus most powerful benefic, Mercury, Saturn benefic.
    # Mars, Jupiter, Moon evil. Sun neutral (despite being 8th lord).
    10: {"Venus": "benefic", "Mercury": "benefic", "Saturn": "benefic",
         "Mars": "malefic", "Jupiter": "malefic", "Moon": "malefic",
         "Sun": "neutral"},
    # Aquarius: HTJAH-I:562-563. Venus, Sun, Mars benefic.
    # Jupiter, Moon malefic. Mercury neutral. Saturn NOT printed -> HOLE (REVIEW).
    11: {"Venus": "benefic", "Sun": "benefic", "Mars": "benefic",
         "Jupiter": "malefic", "Moon": "malefic", "Mercury": "neutral",
         "Saturn": "benefic"},  # HOLE: Aquarius-Saturn (lagna lord, owns 1st+12th) — REVIEW
    # Pisces: HTJAH-I:565-566. Moon, Mars benefic.
    # Saturn, Sun, Venus, Mercury malefic. Jupiter neutral.
    12: {"Moon": "benefic", "Mars": "benefic",
         "Saturn": "malefic", "Sun": "malefic", "Venus": "malefic", "Mercury": "malefic",
         "Jupiter": "neutral"},
}


def houses_owned(planet: str, asc_sign: int) -> list[int]:
    """Rasi-houses (1..12 from the Lagna) lorded by `planet`. Empty for Rahu/Ketu."""
    return sorted(((sign - asc_sign) % 12) + 1
                  for sign, lord in SIGN_LORDS.items() if lord == planet)


def is_yogakaraka(planet: str, asc_sign: int) -> bool:
    """A Raja-Yoga Karaka owns BOTH a kendra and a trikona other than the 1st
    (only Mars/Saturn/Venus can, for specific Lagnas). HTJAH-I:606."""
    hs = set(houses_owned(planet, asc_sign))
    return bool((hs & (_KENDRA - {1})) and (hs & (_TRIKONA - {1})))


def kendradhipati_dosha(planet: str, asc_sign: int) -> bool:
    """A NATURAL BENEFIC owning a kendra (4/7/10, not the 1st) acquires malefic
    tendency — Kendradhipati Dosha. HTJAH-I:582."""
    if planet not in NATURAL_BENEFICS:
        return False
    return bool(set(houses_owned(planet, asc_sign)) & {4, 7, 10})


def functional_nature(planet: str, chart: RamanChart) -> Nature:
    """Per-Lagna functional nature in {benefic, malefic, neutral, yogakaraka}.
    Yoga-karaka overlays the printed table. Rahu/Ketu have no functional ownership
    nature (they act per dispositor/conjunction) -> 'neutral'."""
    if planet in ("Rahu", "Ketu"):
        return "neutral"
    if is_yogakaraka(planet, chart.asc_sign):
        return "yogakaraka"
    return _FUNCTIONAL_TABLE[chart.asc_sign][planet]  # type: ignore[return-value]
