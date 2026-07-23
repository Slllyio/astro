"""Nakshatra soul-signature — the deep archetype of a chart-point's birth star.

The 27 nakshatras carry, in the classical Vedic tradition, a presiding **deity (devata)**, a
**symbol**, and a temperament class **(gana: deva/manushya/rakshasa)**. Reading the nakshatra of a
soul-point — the Atmakaraka, the Moon (manas), or the Lagna — gives its deepest mythic signature.

PROVENANCE (honesty is per-COLUMN, and the consumer must tag accordingly):
  * ``devata`` / ``symbol`` / ``gana`` — classical-Vedic, universally attested, but NOT part of
    Raman's Parashari-natal corpus → the consumer tags these ``CLASSICAL_NONCITABLE``.
  * ``soul_archetype`` / ``soul_keyword`` — a compact EDITORIAL SYNTHESIS of each nakshatra's
    classical essence, authored for this layer → the consumer tags these ``EDITORIAL_SYNTHESIS``.

This is a pure data primitive (no ``judges`` dependency); ``judges/soul_reading.py`` wraps its rows
into provenance-``Tagged`` lines. Never feeds the D1 verdict path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart import varga


@dataclass(frozen=True)
class NakshatraSignature:
    """One nakshatra's mythic + archetypal signature. See the module docstring for provenance."""
    index: int          # 1..27 (1 = Ashwini)
    name: str
    devata: str         # presiding deity  [CLASSICAL_NONCITABLE]
    symbol: str         # classical symbol [CLASSICAL_NONCITABLE]
    gana: str           # deva | manushya | rakshasa [CLASSICAL_NONCITABLE]
    soul_archetype: str  # [EDITORIAL_SYNTHESIS]
    soul_keyword: str    # [EDITORIAL_SYNTHESIS]


_TABLE: Final[tuple[NakshatraSignature, ...]] = (
    NakshatraSignature(1, "Ashwini", "Ashwini Kumaras", "horse's head", "deva",
                       "the healer-pioneer", "swift beginnings, healing, initiative"),
    NakshatraSignature(2, "Bharani", "Yama", "yoni / vessel", "manushya",
                       "the bearer at the threshold", "creation through restraint, life-death"),
    NakshatraSignature(3, "Krittika", "Agni", "razor / flame", "rakshasa",
                       "the purifying flame", "cutting, purification, nourishing fire"),
    NakshatraSignature(4, "Rohini", "Brahma (Prajapati)", "ox-cart / chariot", "manushya",
                       "the fertile creator", "growth, beauty, material abundance"),
    NakshatraSignature(5, "Mrigashira", "Soma (Chandra)", "deer's head", "deva",
                       "the gentle seeker", "searching, curiosity, tenderness"),
    NakshatraSignature(6, "Ardra", "Rudra", "teardrop / gem", "manushya",
                       "the storm-transformer", "breakthrough through crisis, renewal"),
    NakshatraSignature(7, "Punarvasu", "Aditi", "bow / quiver", "deva",
                       "the returning light", "renewal, safe return, boundless nurture"),
    NakshatraSignature(8, "Pushya", "Brihaspati", "cow's udder / lotus", "deva",
                       "the nourisher", "spiritual nourishment, protection, dharma"),
    NakshatraSignature(9, "Ashlesha", "Nagas (serpents)", "coiled serpent", "rakshasa",
                       "the coiled serpent", "kundalini depth, penetration, hypnotic force"),
    NakshatraSignature(10, "Magha", "Pitris (ancestors)", "throne", "rakshasa",
                       "the ancestral throne", "lineage, authority, honouring the forebears"),
    NakshatraSignature(11, "Purva Phalguni", "Bhaga", "front legs of the bed", "manushya",
                       "the pleasure-giver", "enjoyment, creativity, rest"),
    NakshatraSignature(12, "Uttara Phalguni", "Aryaman", "back legs of the bed", "manushya",
                       "the patron-friend", "generosity, contracts, steady support"),
    NakshatraSignature(13, "Hasta", "Savitr (Surya)", "hand / fist", "deva",
                       "the skilled hand", "craft, manifestation, cleverness"),
    NakshatraSignature(14, "Chitra", "Tvashtar (Vishwakarma)", "bright jewel / pearl", "rakshasa",
                       "the cosmic artisan", "brilliant design, form, radiant beauty"),
    NakshatraSignature(15, "Swati", "Vayu", "young shoot / coral", "deva",
                       "the free wind", "independence, movement, self-direction"),
    NakshatraSignature(16, "Vishakha", "Indra-Agni", "triumphal arch", "rakshasa",
                       "the goal-focused", "purposeful striving, dual paths, triumph"),
    NakshatraSignature(17, "Anuradha", "Mitra", "lotus / staff", "deva",
                       "the devoted friend", "friendship, devotion, bhakti"),
    NakshatraSignature(18, "Jyeshtha", "Indra", "earring / umbrella", "rakshasa",
                       "the elder chief", "seniority, protection, occult power"),
    NakshatraSignature(19, "Mula", "Nirriti", "bunch of roots", "rakshasa",
                       "the root-digger", "getting to the root, dissolution, radical inquiry"),
    NakshatraSignature(20, "Purva Ashadha", "Apas (the waters)", "fan / winnowing basket",
                       "manushya", "the invincible", "unbeaten conviction, purification"),
    NakshatraSignature(21, "Uttara Ashadha", "Vishwadevas", "elephant tusk / planks", "manushya",
                       "the later victor", "lasting victory, integrity, universal principle"),
    NakshatraSignature(22, "Shravana", "Vishnu", "ear / three footprints", "deva",
                       "the listener", "sacred hearing, learning, connection"),
    NakshatraSignature(23, "Dhanishta", "the Vasus", "drum / flute", "rakshasa",
                       "the drummer", "rhythm, wealth, resonant abundance"),
    NakshatraSignature(24, "Shatabhisha", "Varuna", "empty circle / hundred healers", "rakshasa",
                       "the veiled healer", "healing mysteries, seclusion, cosmic law"),
    NakshatraSignature(25, "Purva Bhadrapada", "Aja Ekapada", "sword / front of the funeral cot",
                       "manushya", "the fiery ascetic", "spiritual fire, intensity, penance"),
    NakshatraSignature(26, "Uttara Bhadrapada", "Ahir Budhnya", "back of the funeral cot",
                       "manushya", "the deep serpent", "depth, stillness, ancestral wisdom"),
    NakshatraSignature(27, "Revati", "Pushan", "fish / drum", "deva",
                       "the shepherd of souls", "safe passage, nourishment, completion"),
)


def signature_for(nak: int) -> NakshatraSignature:
    """The signature for nakshatra index ``nak`` (1..27, 1 = Ashwini)."""
    if not 1 <= nak <= 27:
        raise ValueError(f"nakshatra index must be 1..27, got {nak}")
    return _TABLE[nak - 1]


def signature_for_lon(lon: float) -> NakshatraSignature:
    """The signature for the nakshatra a sidereal longitude falls in."""
    nak, _pada = varga.nakshatra_pada(lon)
    return signature_for(nak)
