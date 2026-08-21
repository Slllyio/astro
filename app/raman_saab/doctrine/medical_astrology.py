"""Raman's medical-astrology tables — sign -> anatomy, sign -> disease, planet -> both.

Encoded 2026-08-19 from **HPA-29 "Medical Astrology"**, the chapter the report-critique
audit named as the single largest genuine content gap: the health section asks "which body
areas does the chart mark" and, until now, answered with house numbers, because no
sign-to-body-region or planet-to-disease table existed anywhere in `app/raman_saab`.

Four tables and one application rule, each with its own anchor:

  HPA-29:315-337   §6  the anatomical structures represented by each sign
  HPA-29:339-356   §7  "Diseases and signs"
  HPA-29:376-392   §8  the organs each planet holds dominion over
  HPA-29:394-430   §9  each planet's anatomical structures AND its diseases
  HPA-29:433-440   §10 how to apply them (see `APPLICATION` below)

§10 is what makes this doctrine rather than a lookup table, and it is Raman's own
sentence: *"The house of diseases is the sixth from the ascendant. The planets therein,
the lord of the sixth, the aspects on the 6th and the navamsa the lord of the 6th
occupies, should all be considered for predicting diseases. The planet in the 6th house
affect the particular part of the body governed by the sign, and the diseases will be
those that are indicated by its rulers."* (HPA-29:433-440). The sign supplies the body
PART; the planet supplies the DISEASE.

TRANSCRIPTION POLICY. The corpus is OCR'd, and this chapter carries visible damage. The
rule followed here is the PRIME DIRECTIVE's: transcribe what the text says, never what it
probably meant. Where a token is corrupt it is EXCLUDED from the data and recorded in
`OCR_NOTES` with the literal reading — no silent repair, no guessed word. Obvious
scanner artefacts that are not content (a soft hyphen splitting one word across a line
break, the running page header) are rejoined, since that changes no reading.

Raman's own caution travels with the tables and is not optional (HPA-29:353-362): he
anticipates the objection that the ancient Hindus could not have known these disease
names, and answers that the Ayurvedic texts describe many of them, that the astrological
works hint at the governing signs, and that the rest was "collected" from examining
horoscopes. That is a provenance statement about a compiled table, not a claim of
revelation, and the report must not present it as more.

NOT A MEDICAL STATEMENT. Nothing here diagnoses, and no consumer of this module may
present it as diagnosis. It reports which body regions and complaints the classical
tables associate with a chart's own 6th-house testimony.

VERDICT-AUTHORITY INVARIANT: this module is imported by NOTHING in the D1 verdict path;
it is pure lookup data with no judging logic, and the golden ratchet cannot see it.

Usage:
    from app.raman_saab.doctrine.medical_astrology import (
        SIGN_ANATOMY, SIGN_DISEASES, PLANET_ORGANS, PLANET_DISEASES)
    SIGN_ANATOMY[1]        # Aries -> ("cranium", "cerebrum", ...)
    PLANET_DISEASES["Mars"]
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.sources import Citation

# --------------------------------------------------------------------------- #
# Citations — one per table, so a consumer quotes the block it actually used    #
# --------------------------------------------------------------------------- #

CITE_SIGN_ANATOMY: Final[Citation] = Citation("HPA-29", 315)
CITE_SIGN_DISEASES: Final[Citation] = Citation("HPA-29", 339)
CITE_PLANET_ORGANS: Final[Citation] = Citation("HPA-29", 376)
CITE_PLANET_RULERSHIP: Final[Citation] = Citation("HPA-29", 394)
CITE_APPLICATION: Final[Citation] = Citation("HPA-29", 433)
CITE_PROVENANCE_CAUTION: Final[Citation] = Citation("HPA-29", 353)

#: Every anchor this module cites, enumerated so `source_lock` can pin HPA-29's body and line
#: count. Without this the lock cannot see the chapter at all: a citation into a file no
#: registry enumerates is exactly the drift the lock exists to catch, and it was silently
#: uncovered here.
CITED_ANCHORS: Final[tuple] = (
    CITE_SIGN_ANATOMY, CITE_SIGN_DISEASES, CITE_PLANET_ORGANS, CITE_PLANET_RULERSHIP,
    CITE_APPLICATION, CITE_PROVENANCE_CAUTION)

#: Raman's own application rule, verbatim (HPA-29:433-440). The sign gives the body PART,
#: the planet gives the DISEASE — that division of labour is his, not an inference.
APPLICATION: Final[str] = (
    "The house of diseases is the sixth from the ascendant. The planets therein, the lord "
    "of the sixth, the aspects on the 6th and the navamsa the lord of the 6th occupies, "
    "should all be considered for predicting diseases. The planet in the 6th house affect "
    "the particular part of the body governed by the sign, and the diseases will be those "
    "that are indicated by its rulers."
)

#: Raman's provenance note for these tables, paraphrased from HPA-29:353-362. Travels with
#: every rendering: this is a compiled table with a stated mixed pedigree, not revelation.
PROVENANCE_NOTE: Final[str] = (
    "Raman states the pedigree of these tables himself: the Ayurvedic texts describe many "
    "of the diseases, the astrological works hint at which signs govern them, and the "
    "remainder was collected from examining horoscopes (HPA-29:353-362). It is a compiled "
    "correspondence table, and is reported as one."
)

# --------------------------------------------------------------------------- #
# §6 — the anatomical structures represented by each sign (HPA-29:315-337)      #
# --------------------------------------------------------------------------- #

SIGN_ANATOMY: Final[dict[int, tuple[str, ...]]] = {
    1: ("cranium", "cerebrum", "cerebellum", "facial bones", "upper jaw",
        "pituitary glands"),
    2: ("cervical vertebrae", "ears", "lower jaw", "larynx", "thyroid gland",
        "oesophagus"),
    3: ("humerus", "clavicles", "shoulders", "capillaries", "lungs and tracheae",
        "scapula", "upper ribs"),
    4: ("diaphragm", "sternum", "elbow joint", "epigastric region", "thoracic duct",
        "ribs in general"),
    5: ("radius", "ulna", "spinal column", "heart", "spinal cord", "vertebrae"),
    6: ("carpus", "alimentary canal", "meta-carpus", "duodenum", "phalanges", "abdomen"),
    7: ("ovaries and seminal vesicles", "ureters", "epidermis", "lumbar vertebrae"),
    8: ("pelvic bones", "testicles", "rectum", "sacrum", "colon", "bladder"),
    9: ("femur", "hips", "sacral region"),
    10: ("knee joint", "hairs", "nails", "skeleton in general", "patella"),
    11: ("fibula", "bones and muscles of the feet and teeth", "tibia", "ankles",
         "astragalus"),
    # Pisces' FIRST item is corrupt in the OCR — see OCR_NOTES. The two legible items
    # are kept; the corrupt token is dropped rather than guessed at.
    12: ("blood circulation", "meta-tarsus"),
}

# --------------------------------------------------------------------------- #
# §7 — "Diseases and signs" (HPA-29:339-356)                                    #
# --------------------------------------------------------------------------- #

SIGN_DISEASES: Final[dict[int, tuple[str, ...]]] = {
    1: ("brain derangement", "headache", "fevers like ague", "malaria",
        "sleeping sickness", "apoplexy", "insomnia", "eye troubles", "pyorrhea"),
    2: ("obesity", "abscesses", "swellings in the neck", "goitre"),
    3: ("consumption", "pneumonia", "rheumatism", "asthma"),
    4: ("dropsy", "smallpox", "flatulency", "cancer"),
    5: ("digestive troubles", "dyspepsia", "diabetes", "loco-motor ataxia", "swoons",
        "faintings"),
    6: ("constipation", "masturbation", "arthritis", "anus troubles",
        "venereal complaints"),
    7: ("Bright's disease", "lumbago", "nephritis", "renal calculi"),
    8: ("fistula", "ulcers", "nervous troubles", "hemorrhoids", "rectal affection"),
    9: ("gout", "paralysis", "sudden fits", "troubles in the hip"),
    10: ("cutaneous troubles", "leprosy", "leucoderma", "tooth ache", "elephantiasis"),
    11: ("nervous diseases", "spasmodic eruptions"),
    12: ("consumption", "tuberculosis", "mucous troubles", "tumours"),
}

# --------------------------------------------------------------------------- #
# §8 — organs each planet holds dominion over (HPA-29:376-392)                  #
# --------------------------------------------------------------------------- #

PLANET_ORGANS: Final[dict[str, tuple[str, ...]]] = {
    "Sun": ("bile", "heart", "brain", "head", "eye", "bone"),
    "Moon": ("breast", "saliva", "womb", "water", "blood",
             "lymphatic and glandular systems"),
    "Mars": ("bile", "ears", "nose", "forehead", "sinews", "fibre",
             "muscular tissues"),
    "Mercury": ("abdomen", "tongue", "lungs", "bowels", "nerve centres", "bile",
                "muscular tissues"),
    "Jupiter": ("phlegm", "blood", "thighs", "kidneys", "flesh and fat",
                "arterial system"),
    "Venus": ("ovaries", "eyes", "generative system", "water", "semen", "phlegm"),
    "Saturn": ("feet", "wind", "acids", "knees", "marrow", "secretive system"),
}

# --------------------------------------------------------------------------- #
# §9 — each planet's structures AND diseases (HPA-29:394-430)                   #
# --------------------------------------------------------------------------- #
# Raman separates the two halves with an em-dash for five of the seven planets
# ("...membrane—genito and urinary derangements..."). For the Sun and Saturn the OCR
# runs them together with a comma, so the boundary there is EDITORIAL, not his — it is
# recorded in OCR_NOTES and the split point named, rather than presented as the text's.

PLANET_STRUCTURES: Final[dict[str, tuple[str, ...]]] = {
    "Sun": ("cerebellum", "brain", "blood", "lungs", "heart", "stomach", "breasts",
            "ovaries", "seminal vesicles"),
    "Moon": ("pericardium", "veins", "lymphatic vessels", "intestinal functions", "eye",
             "alimentary canal", "membrane"),
    "Mars": ("muscular tissue", "muscles", "cerebral hemispheres"),
    "Mercury": ("nerves", "breath", "air cells", "sense perception", "hair", "tongue",
                "mouth"),
    "Jupiter": ("arteries", "veins", "auricle and ventricle", "the pleura", "ear",
                "blood"),
    "Venus": ("kidneys", "aorta", "fleshy marrow", "skin", "cheeks", "complexion"),
    "Saturn": ("spleen", "upper stomach", "endocardium", "ribs", "bones", "hair",
               "nails"),
}

PLANET_DISEASES: Final[dict[str, tuple[str, ...]]] = {
    "Sun": ("diseases of the heart", "appendicitis", "fistula",
            "inflammatory complaints"),
    "Moon": ("genito and urinary derangements", "testicle troubles", "wind and colic",
             "bronchial catarrh", "dropsy", "tumours", "insanity", "defective eyesight"),
    "Mars": ("inflammation of the lungs", "haemoptysis", "haemorrhage from the lungs",
             "spitting of blood", "consumption", "hypertrophy",
             "typhoid and enteric fever", "infectious and contagious diseases"),
    "Mercury": ("nasal disorders", "impediments of speech", "brain and nervous disorders",
                "asthma", "bronchitis", "delirium", "neurasthenia", "headaches",
                "neuralgia", "palpitation", "worms", "genito-urinary troubles"),
    "Jupiter": ("apoplexy", "pleurisy", "degeneration", "piles", "tumours", "diabetes"),
    "Venus": ("suppression of urine", "discharge from eyes", "cutaneous eruptions",
              "throat diseases", "digestive troubles", "venereal complaints"),
    "Saturn": ("cold", "catarrh", "diseases incidental to exposure", "rheumatism",
               "consumption", "bronchitis", "asthma", "gout", "constipation",
               "Bright's disease"),
}

# --------------------------------------------------------------------------- #
# OCR damage register — what was NOT transcribed, and why                       #
# --------------------------------------------------------------------------- #
#: Every place the encoding departs from a literal reading of the corpus, with the literal
#: reading recorded so a future session with a cleaner scan can settle it. Rejoining a
#: soft-hyphenated word ("clavi cles" -> "clavicles") is not listed: it restores one word
#: the scanner split and changes no reading.
OCR_NOTES: Final[tuple[tuple[str, str], ...]] = (
    ("SIGN_ANATOMY[12] (Pisces)",
     "the corpus reads 'Pisces.—Taurus, blood circulation, meta-tarsus.' (HPA-29:337). "
     "'Taurus' is a sign name standing where a body part belongs and cannot be what "
     "Raman wrote. It is DROPPED, not repaired — the intended word is not recoverable "
     "from this scan and guessing it would mint doctrine. The two legible items are kept, "
     "and 'meta-tarsus' is itself of the foot, so the entry is thin rather than wrong."),
    ("PLANET_STRUCTURES / PLANET_DISEASES, Sun and Saturn",
     "§9 separates structures from diseases with an em-dash for the Moon, Mars, Mercury, "
     "Jupiter and Venus. For the Sun ('...seminal vesicles, diseases of the heart...') "
     "and Saturn ('...hair, nails, cold, catarrah...') the OCR shows a comma, so the "
     "split used here is EDITORIAL: it is placed at the first item that is plainly a "
     "complaint rather than a structure. The union of the two tuples is faithful; the "
     "boundary between them is the encoder's, and is flagged here for that reason."),
    ("spelling",
     "obvious scanner misspellings are normalised where the intended word is unambiguous "
     "and medical ('humerous'->'humerus', 'patela'->'patella', 'duode num'->'duodenum', "
     "'uriters'->'ureters', 'nephrities'->'nephritis', 'hacemoptsis'->'haemoptysis', "
     "'neurasthania'->'neurasthenia', 'catarrah'->'catarrh', 'hyper trophy'->"
     "'hypertrophy'). These change no reading; the corpus line is cited alongside so the "
     "original is always one lookup away."),
)

#: The one caveat sentence that must travel with any rendering of these tables.
CAVEAT: Final[str] = (
    "Classical correspondence tables, not a medical statement: they report which body "
    "regions and complaints Raman's own tables associate with this chart's 6th-house "
    "testimony. Nothing here diagnoses, and nothing here is a prediction of illness."
)


def sign_anatomy(sign: int) -> tuple[str, ...]:
    """The anatomical structures HPA-29 §6 gives for a rasi (1=Aries .. 12=Pisces)."""
    return SIGN_ANATOMY.get(sign, ())


def sign_diseases(sign: int) -> tuple[str, ...]:
    """The complaints HPA-29 §7 gives for a rasi (1=Aries .. 12=Pisces)."""
    return SIGN_DISEASES.get(sign, ())


def planet_diseases(planet: str) -> tuple[str, ...]:
    """The complaints HPA-29 §9 gives for one of the seven grahas.

    The nodes return () — Raman's tables cover the seven visible planets only, and
    inventing a node row would be exactly the mint-from-memory the directive forbids.
    """
    return PLANET_DISEASES.get(planet, ())


def planet_organs(planet: str) -> tuple[str, ...]:
    """The organs HPA-29 §8 gives dominion over, for one of the seven grahas."""
    return PLANET_ORGANS.get(planet, ())
