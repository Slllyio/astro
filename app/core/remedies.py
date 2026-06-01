"""Remedies (Upayas) library — Gap L.

Per BV Raman, KN Rao, Sanjay Rath: real readings ALWAYS end with
concrete upayas. This module structures the canonical per-planet
remedies + a prescription decision tree.

## Decision tree

Diagnose planet condition → prescribe accordingly:

  - weak_benefic         → gemstone + mantra (strengthen)
  - weak_malefic         → mantra + daana only (never strengthen malefic with gem)
  - strong_affliction    → daana + vrat + worship FIRST; gem only after trial
  - strong_benefic       → no remedy needed; channel via career
  - lord_of_dushtana     → mantra-only (never gemstone)
  - marana_karaka_sthana → never gemstone

## Lagna-specific gem safety

Each Lagna has SAFE / AVOID / CAUTIOUS gemstones based on the planet's
functional role. Wearing a "Maraka gem" can cause sudden harm —
classical safety rule.

## Reference

Per Mansagari (gemstones), Atharva Veda + Brihat Parashara (mantras),
Phaladeepika (daana + vrat), Lal Kitab (alternative tradition).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping


@dataclass(frozen=True)
class PlanetRemedy:
    """Complete remedy bundle for one planet."""
    planet: str
    gemstone_primary: str
    gemstone_carats: str            # e.g., "3-6 carats"
    gemstone_metal: str             # e.g., "gold setting"
    gemstone_finger: str            # which finger to wear
    gemstone_day: str               # day to start wearing
    gemstone_substitutes: tuple[str, ...]
    beej_mantra: str                # Sanskrit with Devanagari
    beej_mantra_count: str          # how many recitations
    vedic_mantra_name: str
    yantra_name: str
    daana_items: tuple[str, ...]
    daana_recipient: str
    daana_day: str
    vrat_day: str
    vrat_food: str
    pilgrimage: tuple[str, ...]
    lifestyle_color: str
    lifestyle_food: str
    lifestyle_career: str
    lal_kitab_remedy: str
    safety_caveat: str


# Per-planet complete remedy bundles (concise — full text in agent report).
_REMEDIES: Final[Mapping[str, PlanetRemedy]] = {
    "Sun": PlanetRemedy(
        planet="Sun",
        gemstone_primary="Ruby (Manik)",
        gemstone_carats="3-6 carats (min 3.25 ratti)",
        gemstone_metal="gold setting (panchadhatu acceptable)",
        gemstone_finger="ring finger (right hand)",
        gemstone_day="Sunday at sunrise, Shukla Paksha, Uttara Phalguni / Uttara Ashadha / Krittika nakshatra",
        gemstone_substitutes=("Red Garnet", "Red Spinel", "Red Tourmaline"),
        beej_mantra="ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः (Om Hraam Hreem Hraum Sah Suryaya Namah)",
        beej_mantra_count="7,000 times in 40 days (175/day)",
        vedic_mantra_name="Aditya Hridayam Stotram (Valmiki Ramayana)",
        yantra_name="Surya Yantra (octagonal, 1-6-8 magic square summing 15)",
        daana_items=("wheat", "jaggery (gur)", "copper vessel", "red sandalwood",
                     "red cloth", "masoor dal"),
        daana_recipient="father, paternal figures, or learned Brahmin",
        daana_day="Sunday morning, before noon",
        vrat_day="Sunday (Ravi Vrat)",
        vrat_food="one meal of wheat + jaggery + milk after sunset; no salt or oil",
        pilgrimage=("Konark Sun Temple", "Modhera (Gujarat)", "Suryanar Kovil (Tamil Nadu)"),
        lifestyle_color="red, orange, saffron, copper tones",
        lifestyle_food="wheat, citrus, red fruits, ghee",
        lifestyle_career="authority / governance / medicine / cardiology",
        lal_kitab_remedy="Offer arghya (water with red flowers) to rising Sun for 43 days",
        safety_caveat="Ruby contraindicated if Sun rules 8H (Capricorn/Aquarius Lagna) or in marana karaka sthana (12H)",
    ),
    "Moon": PlanetRemedy(
        planet="Moon",
        gemstone_primary="Natural Pearl (Moti)",
        gemstone_carats="3-7 carats",
        gemstone_metal="silver setting",
        gemstone_finger="little finger (right hand)",
        gemstone_day="Monday sunrise, Shukla Paksha, Rohini / Hasta / Shravana nakshatra",
        gemstone_substitutes=("Moonstone", "White Coral", "Cultured Pearl (last resort)"),
        beej_mantra="ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः (Om Shraam Shreem Shraum Sah Chandraya Namah)",
        beej_mantra_count="11,000 times in 40 days (275/day)",
        vedic_mantra_name="Chandra Stotra 'Dadhi Shankha Tushaarabham'",
        yantra_name="Chandra Yantra (9-celled magic square summing 18)",
        daana_items=("rice", "milk", "curd", "white sandalwood", "silver",
                     "conch shell", "white cloth", "sugar"),
        daana_recipient="mother, elderly women, Brahmin's wife",
        daana_day="Monday evening, after moonrise",
        vrat_day="Monday (Somvar Vrat — 16 consecutive Mondays)",
        vrat_food="rice + milk + fruit after moonrise; no salt or tamasic food",
        pilgrimage=("Somnath (Gujarat)", "Pushkar (full moon)", "any Shiva temple on Pradosh"),
        lifestyle_color="white, silver, pearl-grey",
        lifestyle_food="rice, milk, curd, sabudana, coconut; avoid alcohol",
        lifestyle_career="caretaker roles / motherhood / hospitality",
        lal_kitab_remedy="Fill silver vessel with water nightly for 43 nights, pour into tulsi at sunrise",
        safety_caveat="Pearl can deepen depression if Moon in marana karaka sthana (8H) or with Ketu — test with moonstone first",
    ),
    "Mars": PlanetRemedy(
        planet="Mars",
        gemstone_primary="Red Coral (Moonga)",
        gemstone_carats="6-10 carats",
        gemstone_metal="copper or gold (silver acceptable)",
        gemstone_finger="ring finger (right hand)",
        gemstone_day="Tuesday sunrise, Shukla Paksha, Mrigashira / Chitra / Dhanishta nakshatra",
        gemstone_substitutes=("Carnelian", "Red Jasper"),
        beej_mantra="ॐ क्रां क्रीं क्रौं सः भौमाय नमः (Om Kraam Kreem Kraum Sah Bhaumaya Namah)",
        beej_mantra_count="10,000 times in 40 days (250/day)",
        vedic_mantra_name="Mangal Stotra 'Dharanee garbha sambhutam'",
        yantra_name="Mangal Yantra (9-celled, total 21)",
        daana_items=("red lentils (masoor dal)", "wheat", "jaggery", "copper",
                     "red cloth", "sindoor", "saffron"),
        daana_recipient="younger brother, soldier, unmarried young man",
        daana_day="Tuesday after sunrise, before noon",
        vrat_day="Tuesday (Mangalvar Vrat — 21 Tuesdays)",
        vrat_food="wheat + jaggery + masoor at sunset; no salt/sour food",
        pilgrimage=("Mangalnatha Temple (Ujjain)", "Vaitheeswaran Koil",
                    "Palani"),
        lifestyle_color="red, maroon, deep coral",
        lifestyle_food="wheat, lentils, garlic, ginger; reduce excess chili",
        lifestyle_career="engineering / military / surgery / sports",
        lal_kitab_remedy="Sweet revadi/batashe thrown into flowing water on Tuesdays for 43 weeks",
        safety_caveat="Coral contraindicated for Taurus and Libra Lagna (Mars = 7L/12L or 2L/7L — maraka). Check Mangal Dosha before marriage.",
    ),
    "Mercury": PlanetRemedy(
        planet="Mercury",
        gemstone_primary="Emerald (Panna)",
        gemstone_carats="3-7 carats",
        gemstone_metal="gold setting",
        gemstone_finger="little finger (right hand)",
        gemstone_day="Wednesday sunrise, Shukla Paksha, Ashlesha / Jyeshtha / Revati nakshatra",
        gemstone_substitutes=("Green Tourmaline", "Peridot", "Green Onyx"),
        beej_mantra="ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः (Om Braam Breem Braum Sah Budhaya Namah)",
        beej_mantra_count="9,000 times in 40 days (225/day)",
        vedic_mantra_name="Budha Stotra 'Priyangu kalika shyamam'",
        yantra_name="Budha Yantra (9-celled, total 24)",
        daana_items=("green moong dal", "green vegetables", "emerald", "bronze",
                     "green cloth", "books", "betel leaves", "camphor"),
        daana_recipient="young scholar, schoolteacher, hijra community",
        daana_day="Wednesday morning",
        vrat_day="Wednesday (Budhvar Vrat — 7 Wednesdays)",
        vrat_food="green moong + vegetables + curd; no salt or onion/garlic",
        pilgrimage=("Thiruvenkadu (Tamil Nadu)", "any Vishnu temple", "Tirupati"),
        lifestyle_color="green, beige, lime",
        lifestyle_food="green leafy vegetables, moong, sprouts; reduce red meat",
        lifestyle_career="writing / teaching / commerce / IT / communication",
        lal_kitab_remedy="Feed a goat spinach for 43 days; pierce nose; throw holed copper coin in river",
        safety_caveat="Emerald is safest of the nine; rarely harmful even for debilitated Mercury.",
    ),
    "Jupiter": PlanetRemedy(
        planet="Jupiter",
        gemstone_primary="Yellow Sapphire (Pukhraj)",
        gemstone_carats="5-9 carats",
        gemstone_metal="gold setting",
        gemstone_finger="index finger (right hand)",
        gemstone_day="Thursday sunrise, Shukla Paksha, Punarvasu / Vishakha / Purvabhadrapada nakshatra",
        gemstone_substitutes=("Yellow Topaz (Sunhela — weaker)", "Citrine", "Yellow Beryl"),
        beej_mantra="ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः (Om Graam Greem Graum Sah Gurave Namah)",
        beej_mantra_count="19,000 times in 40 days (475/day)",
        vedic_mantra_name="Guru Stotra 'Devanam cha rishinam cha gurum'",
        yantra_name="Guru Yantra (9-celled, total 12)",
        daana_items=("chana dal", "turmeric", "yellow cloth", "gold", "ghee",
                     "sugar", "saffron", "banana", "religious books"),
        daana_recipient="Brahmin, guru, learned teacher, Vedic priest",
        daana_day="Thursday morning before noon",
        vrat_day="Thursday (Guruvar Vrat — 16 Thursdays)",
        vrat_food="chana dal + roti + curd (yellow theme); no salt or banana",
        pilgrimage=("Alangudi (Tamil Nadu)", "Kashi Vishwanath", "Tirupati"),
        lifestyle_color="yellow, gold, cream",
        lifestyle_food="turmeric, chana, banana, ghee; reduce alcohol",
        lifestyle_career="teaching / law / religion / finance / advisory",
        lal_kitab_remedy="Apply saffron tilak daily; plant peepal and water for 43 Thursdays",
        safety_caveat="Yellow sapphire AVOIDED for Taurus / Libra Lagna (Jupiter = 8L+11L or 3L+6L). Test with citrine first.",
    ),
    "Venus": PlanetRemedy(
        planet="Venus",
        gemstone_primary="Diamond (Heera)",
        gemstone_carats="0.5-1.5 carats (min VS clarity)",
        gemstone_metal="white gold or platinum",
        gemstone_finger="middle finger (right hand)",
        gemstone_day="Friday sunrise, Shukla Paksha, Bharani / Purvaphalguni / Purvashada nakshatra",
        gemstone_substitutes=("White Sapphire (Safed Pukhraj — safer)", "White Topaz", "Zircon", "Quartz"),
        beej_mantra="ॐ द्रां द्रीं द्रौं सः शुक्राय नमः (Om Draam Dreem Draum Sah Shukraya Namah)",
        beej_mantra_count="16,000 times in 40 days (400/day)",
        vedic_mantra_name="Shukra Stotra 'Hima kunda mrinalabham'",
        yantra_name="Shukra Yantra (9-celled, total 27)",
        daana_items=("rice", "sugar", "white cloth", "silver", "white flowers",
                     "perfume", "ghee", "white sandalwood"),
        daana_recipient="young woman, widow, unmarried girl, girls' school",
        daana_day="Friday evening after sunset",
        vrat_day="Friday (Shukravar Vrat — 16 Fridays)",
        vrat_food="kheer + rice + fruit; no sour food or salt",
        pilgrimage=("Kanjanur (Tamil Nadu)", "Vaishno Devi", "Mahalakshmi Temple Mumbai", "Mookambika"),
        lifestyle_color="white, pastel pink, silver, cream",
        lifestyle_food="dairy, rice, sweets, fruits",
        lifestyle_career="arts / music / dance / design / perfumery / fashion",
        lal_kitab_remedy="Feed cows green fodder for 43 Fridays; bury silver coin under tree",
        safety_caveat="Diamond AVOIDED for Aries / Cancer / Leo / Scorpio Lagnas. Flawed diamonds are RUINOUS; require VS clarity certification.",
    ),
    "Saturn": PlanetRemedy(
        planet="Saturn",
        gemstone_primary="Blue Sapphire (Neelam) — TRIAL 3 NIGHTS MANDATORY",
        gemstone_carats="3-5 carats (START SMALL — 2 ratti test)",
        gemstone_metal="silver or panchadhatu (NEVER gold)",
        gemstone_finger="middle finger (right hand)",
        gemstone_day="Saturday SUNSET, Shukla Paksha, Pushya / Anuradha / Uttarabhadrapada nakshatra",
        gemstone_substitutes=("Blue Spinel", "Lapis Lazuli", "Amethyst", "Iolite"),
        beej_mantra="ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः (Om Praam Preem Praum Sah Shanaischaraya Namah)",
        beej_mantra_count="23,000 times in 40 days (575/day)",
        vedic_mantra_name="Shani Stotra by Dasharatha + Hanuman Chalisa",
        yantra_name="Shani Yantra (9-celled, total 15)",
        daana_items=("black sesame", "urad dal", "mustard oil", "iron",
                     "black cloth", "leather shoes", "blanket", "salt"),
        daana_recipient="poor laborer, elderly disabled person, crow",
        daana_day="Saturday evening, after sunset",
        vrat_day="Saturday (Shanivar Vrat — 11+ Saturdays during Sade Sati)",
        vrat_food="urad khichdi + sesame after sunset; no salt or oil",
        pilgrimage=("Shani Shingnapur (Maharashtra)", "Tirunallar (Tamil Nadu)", "Kokilavan Dham"),
        lifestyle_color="black, dark blue, indigo",
        lifestyle_food="urad, sesame, ragi; reduce oily/heavy food",
        lifestyle_career="long-term disciplined service / labor / engineering / law",
        lal_kitab_remedy="Feed black crows with urad-dal on Saturdays for 43 weeks; serve mother",
        safety_caveat="MOST DANGEROUS GEMSTONE. 3-night trial mandatory. AVOID during Sade Sati without dasha confirmation. Best for Taurus / Libra / Capricorn / Aquarius Lagnas.",
    ),
    "Rahu": PlanetRemedy(
        planet="Rahu",
        gemstone_primary="Hessonite Garnet (Gomed)",
        gemstone_carats="6-13 carats",
        gemstone_metal="silver or panchadhatu",
        gemstone_finger="middle finger (right hand)",
        gemstone_day="Saturday evening, Shukla Paksha, Ardra / Swati / Shatabhisha nakshatra",
        gemstone_substitutes=("Spessartine Garnet", "Orange Zircon"),
        beej_mantra="ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः (Om Bhraam Bhreem Bhraum Sah Rahave Namah)",
        beej_mantra_count="18,000 times in 40 days (450/day)",
        vedic_mantra_name="Rahu Stotra 'Ardha-kayam mahaviryam'",
        yantra_name="Rahu Yantra (9-celled, total 72)",
        daana_items=("urad dal", "sesame", "lead", "blue or smoky cloth",
                     "mustard oil", "blanket", "electronics"),
        daana_recipient="leper, beggar, hijra community, snake-charmer",
        daana_day="Saturday evening twilight",
        vrat_day="No specific; observe Shanivar Vrat or Durga Ashtami",
        vrat_food="urad khichdi after sunset; AVOID non-veg + alcohol + intoxicants",
        pilgrimage=("Thirunageshwaram (Tamil Nadu)", "Kalahasti", "any Naga shrine"),
        lifestyle_color="smoky grey, midnight blue, dark brown",
        lifestyle_food="urad, sesame, dark grains; ABSOLUTELY no alcohol/intoxicants",
        lifestyle_career="tech / foreign markets / diplomacy / research / film",
        lal_kitab_remedy="Carry silver square in wallet; float coconut+barley in river on Saturdays for 43 weeks",
        safety_caveat="Second-most-dangerous gem after neelam. NEVER prescribe to addicts or psychiatric history.",
    ),
    "Ketu": PlanetRemedy(
        planet="Ketu",
        gemstone_primary="Cat's Eye (Lehsuniya)",
        gemstone_carats="3-7 carats",
        gemstone_metal="silver or panchadhatu",
        gemstone_finger="middle finger or ring finger (right hand)",
        gemstone_day="Tuesday or Saturday evening, Shukla Paksha, Ashwini / Magha / Mula nakshatra",
        gemstone_substitutes=("Tiger's Eye (weaker)", "Fibrolite Cat's Eye"),
        beej_mantra="ॐ स्रां स्रीं स्रौं सः केतवे नमः (Om Sraam Sreem Sraum Sah Ketave Namah)",
        beej_mantra_count="17,000 times in 40 days (425/day)",
        vedic_mantra_name="Ketu Stotra + Ganapati Atharvashirsha + Subrahmanya mantras",
        yantra_name="Ketu Yantra (9-celled, total 39)",
        daana_items=("multi-colored cloth (saptarangi)", "sesame", "blanket",
                     "iron", "mustard oil", "coconut"),
        daana_recipient="ascetic, sadhu, beggar without limbs, stray dog",
        daana_day="Tuesday twilight",
        vrat_day="No specific; Ganesh Chaturthi or Mangalvar Vrat",
        vrat_food="sesame-rice / til-laddu; no non-veg",
        pilgrimage=("Keezhperumpallam (Tamil Nadu)", "Rameshwaram", "any Ganesha or Subrahmanya temple"),
        lifestyle_color="earth tones, multi-color, ash/grey, saffron",
        lifestyle_food="sesame, urad, simple sattvic food",
        lifestyle_career="spirituality / research / mysticism / healing / IT / coding",
        lal_kitab_remedy="Keep or feed a black-and-white dog; bury 8 coconuts in river on Tuesdays",
        safety_caveat="MOST UNPREDICTABLE GEM. Effects are sudden — windfall or sudden loss. NEVER prescribe during active sadhana. 7-night trial mandatory.",
    ),
}


# Lagna-specific gemstone safety table (Mansagari + Phaladeepika
# functional-role rules)
LAGNA_GEM_SAFETY: Final[Mapping[int, Mapping[str, tuple[str, ...]]]] = {
    1: {"safe": ("Red Coral", "Yellow Sapphire"),
        "avoid": ("Blue Sapphire", "Diamond", "Hessonite")},
    2: {"safe": ("Diamond", "Blue Sapphire"),
        "avoid": ("Red Coral", "Yellow Sapphire")},
    3: {"safe": ("Emerald", "Diamond"),
        "cautious": ("Yellow Sapphire",)},
    4: {"safe": ("Pearl", "Red Coral", "Yellow Sapphire"),
        "avoid": ("Diamond", "Blue Sapphire")},
    5: {"safe": ("Ruby", "Red Coral"),
        "avoid": ("Diamond", "Blue Sapphire", "Hessonite")},
    6: {"safe": ("Emerald", "Diamond")},
    7: {"safe": ("Diamond", "Blue Sapphire"),
        "avoid": ("Red Coral", "Yellow Sapphire")},
    8: {"safe": ("Red Coral", "Yellow Sapphire"),
        "avoid": ("Emerald", "Diamond")},
    9: {"safe": ("Yellow Sapphire", "Red Coral")},
    10: {"safe": ("Blue Sapphire", "Diamond"),
         "cautious": ("Yellow Sapphire",)},
    11: {"safe": ("Blue Sapphire", "Emerald", "Diamond")},
    12: {"safe": ("Yellow Sapphire", "Red Coral", "Pearl")},
}


def get_remedy(planet: str) -> PlanetRemedy:
    """Look up the full remedy bundle for a planet."""
    if planet not in _REMEDIES:
        raise ValueError(f"no remedy for {planet}; valid: {list(_REMEDIES.keys())}")
    return _REMEDIES[planet]


def is_gem_safe_for_lagna(gem: str, lagna_sign: int) -> str:
    """Check gem safety for a Lagna.

    Args:
        gem: gemstone name (case-insensitive partial match).
        lagna_sign: 1..12.

    Returns:
        "safe" / "cautious" / "avoid" / "unrated".
    """
    if not 1 <= lagna_sign <= 12:
        raise ValueError(f"lagna_sign must be 1..12")
    table = LAGNA_GEM_SAFETY[lagna_sign]
    gem_lower = gem.lower()
    for category in ("safe", "avoid", "cautious"):
        if category not in table:
            continue
        for table_gem in table[category]:
            if gem_lower in table_gem.lower() or table_gem.lower() in gem_lower:
                return category
    return "unrated"


@dataclass(frozen=True)
class RemedyPrescription:
    """Prescribed remedy chain for a diagnosed planet condition."""
    planet: str
    condition: str        # "weak_benefic" / "weak_malefic" / "strong_affliction" / etc.
    recommended_remedies: tuple[str, ...]  # "gemstone" / "mantra" / "daana" / "vrat"
    gemstone_caveat: str  # "PROCEED" / "TRIAL_REQUIRED" / "AVOID"
    rationale: str


def prescribe(
    planet: str, condition: str, lagna_sign: int | None = None,
) -> RemedyPrescription:
    """Decision tree for prescribing remedies per diagnosis.

    Args:
        planet: name (Sun..Saturn or Rahu/Ketu).
        condition: one of "weak_benefic" / "weak_malefic" /
            "strong_affliction" / "strong_benefic" / "lord_of_dushtana"
            / "marana_karaka_sthana".
        lagna_sign: 1..12 for gem-safety overlay (optional).

    Returns:
        RemedyPrescription with the recommended remedy chain.
    """
    if planet not in _REMEDIES:
        raise ValueError(f"no remedy for {planet}")
    if condition == "weak_benefic":
        recommended = ("gemstone", "mantra")
        rationale = "Weak benefic — strengthen via gem + mantra."
        gem_caveat = "PROCEED"
    elif condition == "weak_malefic":
        recommended = ("mantra", "daana")
        rationale = (
            "Weak malefic — NEVER strengthen with gem; calm via mantra + daana."
        )
        gem_caveat = "AVOID"
    elif condition == "strong_affliction":
        recommended = ("daana", "vrat", "mantra")
        rationale = (
            "Strong affliction — pacify first via daana + vrat + worship. "
            "Gem only after 3-7 day trial."
        )
        gem_caveat = "TRIAL_REQUIRED"
    elif condition == "strong_benefic":
        recommended = ("lifestyle",)
        rationale = "Strong benefic — no remedy needed; channel via career/dharma."
        gem_caveat = "AVOID"
    elif condition == "lord_of_dushtana":
        recommended = ("mantra",)
        rationale = "Lord of dusthana — never gemstone (would amplify negativity)."
        gem_caveat = "AVOID"
    elif condition == "marana_karaka_sthana":
        recommended = ("mantra", "daana")
        rationale = "Karaka in destruction-of-karaka position — never gemstone."
        gem_caveat = "AVOID"
    else:
        recommended = ("mantra",)
        rationale = f"Unknown condition {condition} — default to mantra only."
        gem_caveat = "AVOID"

    # Apply Lagna safety overlay if requested
    if lagna_sign is not None and gem_caveat in ("PROCEED", "TRIAL_REQUIRED"):
        gem_name = _REMEDIES[planet].gemstone_primary
        safety = is_gem_safe_for_lagna(gem_name, lagna_sign)
        if safety == "avoid":
            gem_caveat = "AVOID"
            rationale += f" (Gem AVOIDED for Lagna {lagna_sign}.)"
        elif safety == "cautious":
            gem_caveat = "TRIAL_REQUIRED"
            rationale += f" (Gem CAUTIOUS for Lagna {lagna_sign}; mandate trial.)"

    return RemedyPrescription(
        planet=planet, condition=condition,
        recommended_remedies=recommended,
        gemstone_caveat=gem_caveat, rationale=rationale,
    )


def all_remedies() -> dict[str, PlanetRemedy]:
    """All 9-planet remedy bundles for diagnostic display."""
    return dict(_REMEDIES)
