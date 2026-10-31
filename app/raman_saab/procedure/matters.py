"""The matters of each house, with the karaka Raman ACTUALLY uses (spec section 6).

One row per matter: the karaka the reader grades (``None`` where Raman uses none), the
decision rule that settles a split (spec 4.2), whether the star lord is read (spec 4.8:
longevity and the father), and the timing rules that apply to the matter's events (spec 5.2).

``SIGNIFICATION_MATTER`` maps the golden-ledger signification keys onto these matters, for the
measurement in ``tools/raman_saab/procedure_reader_measure.py``; a key not listed falls to the
house's first matter (pre-registered in ``docs/raman_saab/PROCEDURE_READER_2026-10-25.md``).

Usage:
    from app.raman_saab.procedure.matters import MATTERS, matter_for
    MATTERS[4]                     # the 4th house's matters
    matter_for(4, "mother")
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional


@dataclass(frozen=True)
class Event:
    """A timed event of a matter: its kind selects the timing rule (spec 5.2)."""
    kind: str               # good_event | rank | relative_death | marriage | native_death
    label: str


@dataclass(frozen=True)
class Matter:
    house: int
    key: str
    label: str
    karaka: Optional[str]
    karaka_cite: str        # citations.py key
    karaka_note: str
    decider: str            # tally | lord_over_house | mother | education | children | father
    #                         | longevity | gains | elder_brothers | profession
    star_lord: bool
    events: tuple[Event, ...]


_GOOD = "good_event"

MATTERS: Final[dict[int, tuple[Matter, ...]]] = {
    1: (Matter(1, "self", "the self, body and fortune", "Sun", "two_of_three",
               "Lagna karaka Sun, used in 21 of 29 charts (spec 3.1); the trinity of Lagna, "
               "Sun and Moon", "tally", False,
               (Event(_GOOD, "results of the first house"),)),),
    2: (Matter(2, "wealth", "wealth and family", "Jupiter", "two_of_three",
               "Dhana-karaka Jupiter (spec 6)", "tally", False,
               (Event(_GOOD, "financial results of the second house"),)),
        Matter(2, "eyes", "the eyes", "Sun", "two_of_three",
               "Netra-karaka Sun, as in Chart 39 (spec 6)", "tally", False,
               (Event(_GOOD, "results of the second house for the eyes"),))),
    3: (Matter(3, "brothers", "younger brothers and sisters", "Mars",
               "debility_combustion_destroys", "Mars, the karaka for brothers (spec 6)",
               "lord_over_house", False,
               (Event("relative_death", "death of a brother"),)),),
    4: (Matter(4, "mother", "the mother", "Moon", "karakas_fourth",
               "Matru-karaka Moon (spec 6)", "mother", False,
               (Event("relative_death", "death of the mother"),)),
        Matter(4, "education", "education", "Jupiter", "karakas_fourth",
               "Vidya-karaka Jupiter (spec 6)", "education", False,
               (Event(_GOOD, "results of the fourth house for learning"),)),
        Matter(4, "vehicles", "vehicles", "Venus", "karakas_fourth",
               "Vahana-karaka Venus (spec 6)", "tally", False,
               (Event(_GOOD, "acquisition of a vehicle"),)),
        Matter(4, "property", "house and property", "Mars", "karaka_griha",
               "Griha-karaka Mars (spec 6)", "tally", False,
               (Event(_GOOD, "acquisition of a house"),)),
        Matter(4, "happiness", "happiness", "Jupiter", "karakas_fourth",
               "Jupiter for happiness, after Vaidyanatha (HTJAH:4386-4388)", "tally", False,
               (Event(_GOOD, "results of the fourth house"),))),
    5: (Matter(5, "children", "children", "Jupiter", "children_dasa_in_span",
               "Putra-karaka Jupiter (spec 6)", "children", False,
               (Event(_GOOD, "birth of a child"),)),),
    6: (Matter(6, "disease_enemies", "disease, enemies and debts", "Mars", "two_of_three",
               "Roga-karaka Mars (spec 6). Raman reads the 6th backwards from the known disease; "
               "applying the forward template here is the reader's convention", "tally", False,
               (Event(_GOOD, "episodes of the sixth house (disease, enemies, debts)"),)),),
    7: (Matter(7, "marriage", "marriage and the partner", "Venus", "two_of_three",
               "Kalatra-karaka Venus (spec 6)", "tally", False,
               (Event("marriage", "marriage"), Event("relative_death", "death of the partner"))),),
    8: (Matter(8, "longevity", "longevity", "Saturn", "longevity_saturn",
               "Ayush-karaka Saturn (spec 6)", "longevity", True,
               (Event("native_death", "end of life"),)),),
    9: (Matter(9, "father", "the father", "Sun", "karaka_father_timing",
               "Pitru-karaka Sun (spec 6)", "father", True,
               (Event("relative_death", "death of the father"),)),
        Matter(9, "fortune", "fortune, dharma and travel", None, "two_of_three",
               "No karaka: Raman's travel and fortune readings use none (spec 6); the view "
               "from the Moon takes the third vote (convention)", "tally", False,
               (Event(_GOOD, "results of the ninth house"),))),
    10: (Matter(10, "profession", "profession and rank", None, "two_of_three",
                "No timing karaka: the Sun appears in 2 of 78 charts, descriptively (spec 6); "
                "the view from the Moon takes the third vote (convention)", "profession", False,
                (Event("rank", "rise and fall in rank"),
                 Event(_GOOD, "results of the tenth house"))),),
    11: (Matter(11, "gains", "gains", "Jupiter", "karaka_gains",
                "Jupiter, Dhana-karaka, for gains (spec 6)", "gains", False,
                (Event(_GOOD, "gains"),)),
         Matter(11, "elder_brothers", "elder brothers and sisters", "Mars",
                "karaka_elder_brothers", "Mars for elder brothers (spec 6)", "elder_brothers",
                False, (Event("relative_death", "death of an elder brother"),))),
    12: (Matter(12, "losses", "losses, expenditure, the bed, the left eye, confinement, moksha",
                "Saturn", "karaka_twelfth_printed",
                "Saturn is the karaka Raman PRINTS for the 12th (HTJAH:17733-17735), and it is "
                "graded here; FLAG: his worked charts never use it (0 of 26) and use Venus "
                "(bed, eyes), Jupiter (spirituality), Rahu (moksha) and Ketu (kaivalya) instead "
                "(spec 6, 7.4)", "tally", False,
                (Event(_GOOD, "results of the twelfth house"),)),),
}

#: The relative's house for a relative-death event (bhavat bhavam, spec 5.2).
RELATIVE_HOUSE: Final[dict[str, int]] = {
    "brothers": 3, "mother": 4, "marriage": 7, "father": 9, "elder_brothers": 11}

#: Golden-ledger signification -> matter key (measurement only).
SIGNIFICATION_MATTER: Final[dict[str, str]] = {
    "self": "self", "body": "self", "health": "self",
    "wealth": "wealth", "speech": "wealth", "vision": "eyes",
    "siblings": "brothers", "courage": "brothers", "ear_throat": "brothers",
    "mother": "mother", "education": "education", "vehicles": "vehicles",
    "property": "property", "happiness": "happiness",
    "children": "children", "intellect": "children",
    "debts": "disease_enemies", "disease_chronic": "disease_enemies",
    "enemies": "disease_enemies", "enemies_disease": "disease_enemies",
    "coverture": "marriage", "marital_happiness": "marriage", "partnership": "marriage",
    "spouse": "marriage", "virility": "marriage",
    "death": "longevity", "longevity": "longevity",
    "father": "father", "dharma": "fortune", "fortune": "fortune", "long_journeys": "fortune",
    "career": "profession", "profession_authority": "profession",
    "profession_learned": "profession", "status_honour": "profession",
    "acquisitions": "gains", "gains": "gains", "elder_siblings": "elder_brothers",
    "expenditure": "losses", "incarceration": "losses", "left_eye": "losses",
    "moksha": "losses",
}


def matter_for(house: int, key: Optional[str] = None) -> Matter:
    """The matter ``key`` of ``house``; the house's first matter when ``key`` is None or is a
    golden signification key not in ``SIGNIFICATION_MATTER`` for this house."""
    rows = MATTERS[house]
    if key is not None:
        key = SIGNIFICATION_MATTER.get(key, key)
        for m in rows:
            if m.key == key:
                return m
    return rows[0]
