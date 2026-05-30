"""Nakshatra deep layer — Gap H.

Beyond simple name + lord, classical Vedic astrology attaches ~10
attributes to each of the 27 nakshatras. The base ``app/core/nakshatra.py``
exposes ``NAKSHATRAS`` (names) and ``NAKSHATRA_LORDS`` (Vimshottari
lord mapping). This module adds the full classical taxonomy:

## Attributes per nakshatra (BPHS Ch.3 + Brihat Samhita Ch.8 + Manu Smriti)

- **Pada (1-4)**: each nakshatra spans 13°20', divided into 4 padas of
  3°20' each. Each pada maps to a specific Navamsha sign.
- **Devata** (presiding deity): used in mantra prescription + spiritual
  domain reading.
- **Gana** (Deva / Manushya / Rakshasa): temperament classification.
  Used in marriage compatibility (Gana Koota).
- **Yoni** (animal symbol — 14 yonis): used in marriage compatibility
  (Yoni Koota).
- **Nadi** (Adya / Madhya / Antya): used in marriage compatibility
  (Nadi Koota — major dosha if same Nadi).
- **Varna** (Brahmin / Kshatriya / Vaishya / Shudra): caste-like
  classification, used in compatibility + occupation hints.
- **Tatva** (Pancha Mahabhuta): Earth / Water / Fire / Air / Ether.
- **Guna** (Sattva / Rajas / Tamas): quality affinity.
- **Direction** (8 cardinal/intercardinal): geographic affinity, used
  in muhurta and lost-item prashna.
- **Body part**: limb of Kalapurusha mapped to the nakshatra (used in
  health diagnosis).

## Tara Chakra (9-fold birth-star to transit-star scoring)

Given Moon's nakshatra at birth (Janma Tara), every nakshatra is
classified into one of 9 Tara types by its distance from Janma:
Janma / Sampat / Vipat / Kshema / Pratyari / Sadhaka / Vadha /
Maitra / Ati-Maitra. Transit of a planet to a "good" Tara nakshatra
yields favorable results; transit to "bad" Tara yields difficulty.

Tara Chakra is the primary basis for **muhurta** (electional astrology)
and **daily fortune predictions** in traditional practice.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.nakshatra import NAKSHATRAS, nakshatra_for_longitude


@dataclass(frozen=True)
class NakshatraAttributes:
    """Complete attribute bundle for one nakshatra."""
    name: str
    index: int                  # 0..26
    lord: str                   # Vimshottari lord (Ketu, Venus, ..., Mercury)
    devata: str                 # presiding deity
    gana: str                   # Deva / Manushya / Rakshasa
    yoni: str                   # animal symbol
    nadi: str                   # Adya / Madhya / Antya
    varna: str                  # Brahmin / Kshatriya / Vaishya / Shudra
    tatva: str                  # Prithvi / Jala / Agni / Vayu / Akasha
    guna: str                   # Sattva / Rajas / Tamas
    direction: str              # E / SE / S / SW / W / NW / N / NE
    body_part: str              # limb of Kalapurusha
    symbol: str                 # iconographic symbol


# Complete 27-nakshatra attribute table per Brihat Samhita Ch.8 +
# Mansagari Ch.4 + Phaladeepika Ch.27. Standard south-Indian school
# convention (some texts diverge on Yoni for 1-2 nakshatras; we use
# the most widely-cited variant).
_NAKSHATRA_TABLE: Final[tuple[NakshatraAttributes, ...]] = (
    NakshatraAttributes("Ashwini", 0, "Ketu", "Ashwini Kumaras", "Deva", "Horse", "Adya",
                         "Vaishya", "Prithvi", "Tamas", "S", "Knees", "Horse-head"),
    NakshatraAttributes("Bharani", 1, "Venus", "Yama", "Manushya", "Elephant", "Madhya",
                         "Mleccha", "Prithvi", "Rajas", "W", "Head", "Yoni"),
    NakshatraAttributes("Krittika", 2, "Sun", "Agni", "Rakshasa", "Sheep", "Antya",
                         "Brahmin", "Prithvi", "Rajas", "N", "Hips", "Razor / Flame"),
    NakshatraAttributes("Rohini", 3, "Moon", "Brahma", "Manushya", "Serpent", "Antya",
                         "Shudra", "Prithvi", "Rajas", "E", "Forehead", "Chariot"),
    NakshatraAttributes("Mrigashira", 4, "Mars", "Soma (Chandra)", "Deva", "Serpent",
                         "Madhya", "Servant", "Prithvi", "Tamas", "S", "Eyes", "Deer-head"),
    NakshatraAttributes("Ardra", 5, "Rahu", "Rudra", "Manushya", "Dog", "Adya",
                         "Butcher", "Jala", "Tamas", "N", "Hair", "Teardrop"),
    NakshatraAttributes("Punarvasu", 6, "Jupiter", "Aditi", "Deva", "Cat", "Adya",
                         "Vaishya", "Jala", "Sattva", "N", "Fingers", "Quiver of arrows"),
    NakshatraAttributes("Pushya", 7, "Saturn", "Brihaspati", "Deva", "Sheep", "Madhya",
                         "Kshatriya", "Jala", "Tamas", "E", "Mouth/Face", "Cow's udder"),
    NakshatraAttributes("Ashlesha", 8, "Mercury", "Naga (Serpent)", "Rakshasa", "Cat",
                         "Antya", "Mleccha", "Jala", "Sattva", "S", "Ears", "Coiled serpent"),
    NakshatraAttributes("Magha", 9, "Ketu", "Pitrs (Ancestors)", "Rakshasa", "Rat",
                         "Antya", "Shudra", "Jala", "Tamas", "W", "Nose", "Royal throne"),
    NakshatraAttributes("Purva Phalguni", 10, "Venus", "Bhaga", "Manushya", "Rat",
                         "Madhya", "Brahmin", "Jala", "Rajas", "N", "Lips/Genitals", "Front legs of cot"),
    NakshatraAttributes("Uttara Phalguni", 11, "Sun", "Aryaman", "Manushya", "Cow",
                         "Adya", "Kshatriya", "Agni", "Rajas", "E", "Hands", "Rear legs of cot"),
    NakshatraAttributes("Hasta", 12, "Moon", "Savitar (Surya)", "Deva", "Buffalo",
                         "Adya", "Vaishya", "Agni", "Rajas", "W", "Fingers", "Hand / Fist"),
    NakshatraAttributes("Chitra", 13, "Mars", "Tvashtar", "Rakshasa", "Tiger", "Madhya",
                         "Servant", "Agni", "Tamas", "S", "Forehead/Neck", "Bright jewel"),
    NakshatraAttributes("Swati", 14, "Rahu", "Vayu", "Deva", "Buffalo", "Antya",
                         "Butcher", "Agni", "Tamas", "N", "Chest", "Coral / Sapling"),
    NakshatraAttributes("Vishakha", 15, "Jupiter", "Indra-Agni", "Rakshasa", "Tiger",
                         "Antya", "Mleccha", "Agni", "Sattva", "E", "Arms", "Triumphal arch"),
    NakshatraAttributes("Anuradha", 16, "Saturn", "Mitra", "Deva", "Deer", "Madhya",
                         "Shudra", "Vayu", "Tamas", "S", "Breasts/Stomach", "Lotus"),
    NakshatraAttributes("Jyeshtha", 17, "Mercury", "Indra", "Rakshasa", "Deer", "Adya",
                         "Servant", "Vayu", "Sattva", "W", "Neck", "Earring / Umbrella"),
    NakshatraAttributes("Mula", 18, "Ketu", "Nirriti", "Rakshasa", "Dog", "Adya",
                         "Butcher", "Vayu", "Tamas", "N", "Feet", "Bunch of roots"),
    NakshatraAttributes("Purva Ashadha", 19, "Venus", "Apas (Waters)", "Manushya",
                         "Monkey", "Madhya", "Brahmin", "Vayu", "Rajas", "E", "Thighs",
                         "Fan / Winnowing basket"),
    NakshatraAttributes("Uttara Ashadha", 20, "Sun", "Vishve Devas", "Manushya",
                         "Mongoose", "Antya", "Kshatriya", "Akasha", "Sattva", "S",
                         "Thighs", "Elephant tusk"),
    NakshatraAttributes("Shravana", 21, "Moon", "Vishnu", "Deva", "Monkey", "Antya",
                         "Mleccha", "Akasha", "Rajas", "W", "Ears", "Three footsteps"),
    NakshatraAttributes("Dhanishta", 22, "Mars", "Vasus (Eight Vasus)", "Rakshasa",
                         "Lion", "Madhya", "Servant", "Akasha", "Tamas", "N", "Back",
                         "Drum / Flute"),
    NakshatraAttributes("Shatabhisha", 23, "Rahu", "Varuna", "Rakshasa", "Horse",
                         "Adya", "Butcher", "Akasha", "Tamas", "E", "Chin/Jaw",
                         "Empty circle / 100 healers"),
    NakshatraAttributes("Purva Bhadrapada", 24, "Jupiter", "Aja Ekapada", "Manushya",
                         "Lion", "Adya", "Brahmin", "Akasha", "Sattva", "S", "Sides",
                         "Front legs of cot / Two-faced man"),
    NakshatraAttributes("Uttara Bhadrapada", 25, "Saturn", "Ahir Budhnya", "Manushya",
                         "Cow", "Madhya", "Kshatriya", "Prithvi", "Tamas", "W",
                         "Sides/Shins", "Rear legs of cot / Twins"),
    NakshatraAttributes("Revati", 26, "Mercury", "Pushan", "Deva", "Elephant", "Antya",
                         "Shudra", "Prithvi", "Sattva", "N", "Feet", "Drum / Fish"),
)


def attributes_for_nakshatra(index: int) -> NakshatraAttributes:
    """Lookup attributes by 0-indexed nakshatra position (Ashwini=0)."""
    if not 0 <= index <= 26:
        raise ValueError(f"nakshatra index must be 0..26, got {index}")
    return _NAKSHATRA_TABLE[index]


def attributes_for_longitude(longitude: float) -> NakshatraAttributes:
    """Convenience: get full attributes for a sidereal longitude."""
    info = nakshatra_for_longitude(longitude)
    return attributes_for_nakshatra(info["index"])


# ─── Tara Chakra ────────────────────────────────────────────────────


_TARA_LABELS: Final[tuple[str, ...]] = (
    "Janma",    # 1 — self/birth — neutral
    "Sampat",   # 2 — wealth — auspicious
    "Vipat",    # 3 — danger — inauspicious
    "Kshema",   # 4 — prosperity — auspicious
    "Pratyari", # 5 — obstacle — inauspicious
    "Sadhaka",  # 6 — achievement — auspicious
    "Vadha",    # 7 — death — most inauspicious
    "Maitra",   # 8 — friend — auspicious
    "Ati-Maitra", # 9 — best friend — most auspicious
)

# Auspiciousness: True = favorable for new starts/travel/muhurta
_TARA_AUSPICIOUS: Final[Mapping[str, bool]] = {
    "Janma": False,      # one's own birth nakshatra is neutral/slight caution
    "Sampat": True,
    "Vipat": False,
    "Kshema": True,
    "Pratyari": False,
    "Sadhaka": True,
    "Vadha": False,
    "Maitra": True,
    "Ati-Maitra": True,
}


@dataclass(frozen=True)
class TaraVerdict:
    """Tara Chakra reading for a target nakshatra against a Janma nakshatra."""
    janma_nakshatra_index: int    # Moon's nakshatra at birth
    target_nakshatra_index: int   # the nakshatra being evaluated
    distance: int                 # 1..9 (inclusive count)
    tara_label: str               # Janma / Sampat / ... / Ati-Maitra
    is_auspicious: bool


def tara_chakra(janma_index: int, target_index: int) -> TaraVerdict:
    """Compute Tara Chakra verdict for a target nakshatra given the
    native's Janma nakshatra (Moon's nakshatra at birth).

    Standard rule (BPHS + Mansagari + practical muhurta):
      1. Count nakshatras forward from Janma to target (inclusive).
      2. Take that count modulo 9 (with 0 → 9, since 9-cycle is repeating).
      3. The 9-modulo position maps to: 1=Janma, 2=Sampat, 3=Vipat,
         4=Kshema, 5=Pratyari, 6=Sadhaka, 7=Vadha, 8=Maitra, 9=Ati-Maitra.

    Args:
        janma_index: 0..26 — native's Moon nakshatra at birth.
        target_index: 0..26 — nakshatra being evaluated (e.g., transit
            nakshatra of a planet, or muhurta star).

    Returns:
        TaraVerdict with the label + auspicious flag.
    """
    if not 0 <= janma_index <= 26:
        raise ValueError(f"janma_index must be 0..26, got {janma_index}")
    if not 0 <= target_index <= 26:
        raise ValueError(f"target_index must be 0..26, got {target_index}")
    # Inclusive count: distance 1 = same nakshatra
    distance = ((target_index - janma_index) % 27) + 1
    # Cycle 9 — but distance 1..9 maps directly, 10..18 also maps to 1..9, etc.
    tara_position = ((distance - 1) % 9) + 1
    tara_label = _TARA_LABELS[tara_position - 1]
    return TaraVerdict(
        janma_nakshatra_index=janma_index,
        target_nakshatra_index=target_index,
        distance=distance,
        tara_label=tara_label,
        is_auspicious=_TARA_AUSPICIOUS[tara_label],
    )


# ─── Pada → Navamsha mapping ────────────────────────────────────────


def pada_to_navamsha_sign(nakshatra_index: int, pada: int) -> int:
    """Map (nakshatra, pada) to the resulting Navamsha sign (1..12).

    Each nakshatra has 4 padas of 3°20' each. The 108 padas (27 × 4)
    map cyclically to 108 navamsha cells (12 signs × 9 navamshas).
    Starting nakshatra: Ashwini pada 1 = Aries navamsha (sign 1).

    Args:
        nakshatra_index: 0..26
        pada: 1..4

    Returns:
        Navamsha sign (1..12) for that pada.
    """
    if not 0 <= nakshatra_index <= 26:
        raise ValueError(f"nakshatra index must be 0..26, got {nakshatra_index}")
    if not 1 <= pada <= 4:
        raise ValueError(f"pada must be 1..4, got {pada}")
    pada_global = nakshatra_index * 4 + (pada - 1)  # 0..107
    return (pada_global % 12) + 1


# ─── Gana compatibility (marriage Koota) ────────────────────────────


_GANA_COMPATIBILITY: Final[Mapping[tuple[str, str], int]] = {
    # Score 0-6 for Gana Koota (max 6 points)
    ("Deva", "Deva"): 6,
    ("Manushya", "Manushya"): 6,
    ("Rakshasa", "Rakshasa"): 6,
    ("Deva", "Manushya"): 5,
    ("Manushya", "Deva"): 5,
    ("Manushya", "Rakshasa"): 0,    # major incompatibility
    ("Rakshasa", "Manushya"): 0,
    ("Deva", "Rakshasa"): 1,        # tolerable
    ("Rakshasa", "Deva"): 1,
}


def gana_koota_score(boy_nakshatra_index: int, girl_nakshatra_index: int) -> int:
    """Marriage Gana Koota — temperament compatibility score (0-6).

    Used in Ashtakoota matching (one of the 8 traditional koota
    components). Deva-Deva or Manushya-Manushya = perfect;
    Manushya-Rakshasa = doctrinally severe incompatibility.
    """
    boy = attributes_for_nakshatra(boy_nakshatra_index).gana
    girl = attributes_for_nakshatra(girl_nakshatra_index).gana
    return _GANA_COMPATIBILITY.get((boy, girl), 3)


def nadi_koota_dosha(boy_nakshatra_index: int, girl_nakshatra_index: int) -> bool:
    """Check Nadi Dosha — same Nadi between partners is doctrinally
    severe (genetic/health concerns; classical: progeny risk).

    Returns True if SAME nadi (Dosha present).
    """
    boy = attributes_for_nakshatra(boy_nakshatra_index).nadi
    girl = attributes_for_nakshatra(girl_nakshatra_index).nadi
    return boy == girl


def yoni_koota_score(boy_nakshatra_index: int, girl_nakshatra_index: int) -> int:
    """Yoni Koota — sexual/animal compatibility score (0-4).

    Simplified: same Yoni = 4 (perfect), friendly pair = 3, neutral = 2,
    natural-enemy pair = 0 or 1. Classical pairs (per BPHS + Mansagari):

      Friendly: Horse-Buffalo, Sheep-Monkey, etc.
      Enemy: Cat-Rat, Cow-Tiger, Snake-Mongoose, etc.

    This implementation gives same-yoni=4, otherwise a coarse 2 (neutral).
    Full enemy-pair table is large; production version should expand.
    """
    boy = attributes_for_nakshatra(boy_nakshatra_index).yoni
    girl = attributes_for_nakshatra(girl_nakshatra_index).yoni
    # Coarse: same yoni = perfect; different = neutral
    # Production should add the 14×14 enemy/friend matrix.
    return 4 if boy == girl else 2
