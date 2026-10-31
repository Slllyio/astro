"""Verbatim citations for every KP rule the engine fires.

Each entry quotes the OCR text of K. S. Krishnamurti's *KP Reader 3 —
Predictive Stellar Astrology* (source id ``kp_reader3_predictive``) exactly as
it stands in ``data/knowledge_library/sources/kp_reader3_predictive/
chapter_001_full-text-unsplit.md`` on the project PC, with whitespace
collapsed. OCR errors are kept as printed (``1 1`` for 11, ``0112`` for
"or 12") and glossed in ``note``. ``tests/kp/test_citations.py`` checks every
quote against the file when it is present.

``status`` says how directly the engine's use follows from the quote:

* ``"cited"``    the rule is stated in the quote.
* ``"extended"`` the quote states it in a narrower context (e.g. horary) and
  the engine applies it more widely; the extension is named in KP_RULINGS.md.

Usage:
    from app.kp.citations import CITATIONS
    CITATIONS["KPR3-SUB"].quote
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

SOURCE_FILE: Final[str] = (
    "data/knowledge_library/sources/kp_reader3_predictive/chapter_001_full-text-unsplit.md"
)


@dataclass(frozen=True, slots=True)
class Citation:
    """One verbatim passage of KP Reader 3."""

    key: str
    lines: str
    quote: str
    status: str = "cited"
    note: str = ""

    def ref(self) -> str:
        """Short reference such as ``KPR3:3402-3404``."""
        return f"KPR3:{self.lines}"


_C = Citation
CITATIONS: Final[dict[str, Citation]] = {c.key: c for c in (
    _C("KPR3-SUB", "3402-3404",
       "it is the 9 divisions of each constellation in the proportion in which they are "
       "allotted total number of years in Vimshottari dasa."),
    _C("KPR3-RAPHAEL", "7664-7665",
       "(2) Erect horoscope using Raphael Ephemeris and Table of houses.",
       note="Raphael's Tables of Houses are Placidus tables."),
    _C("KPR3-SAYANA-MINUS", "19556-19559",
       "The values given by Raphael are tropical. But, we work with sidereal (nirayana) values. "
       "Hence, from each of the sayana cusps, we must deduct Krishnamurti ayanamsa"),
    _C("KPR3-AYANAMSA-1922", "18871", "K.P. Ayanamsa - 22 40'.",
       note="Printed for a birth of 18 July 1922; Swiss Ephemeris SIDM_KRISHNAMURTI gives 22°41'."),
    _C("KPR3-AYANAMSA-1969", "19559", "Krishnamurti ayanamsa (23 20' for 1969)."),
    _C("KPR3-HORARY-206", "19551-19553",
       "the nirayana horary ascendant is the commencement of 206th sub of Krishnamurti Pad hdhati. "
       "Hence the lagna is Capricorn 26° 6' 40\"."),
    _C("KPR3-HORARY-37", "19779-19780",
       "Number 37 implies that the horary ascendant is Taurus 22° 40' on the nirayana zodiac."),
    _C("KPR3-STARLORD-HOUSES", "6594-6597",
       "one is to take each planet and consider in which constellation it is, the lord of the "
       "constellation and note in which houses the lord of the constellation is, ownership"),
    _C("KPR3-SUB-DECIDES", "6704-6706",
       "Hence Planet is the source, constellation indicates nature of the result and the SUB is "
       "a deciding factor whether the matter is favourable or not."),
    _C("KPR3-LADDER", "8738-8740",
       "(a) Planets posited in the constellation of the occupants in the houses 2, 6, 10 or 11 "
       "are the strongest to give wealth to a person.",
       note="The ladder continues (b) occupants, (c) planets in the constellation of the lords, "
            "(d) the lords, (e) planets conjoined with or aspected by them."),
    _C("KPR3-LADDER-C", "8751-8752",
       "(c) The planets in the constellation of the lords of the houses 2 or 6 or 1 0 or 1 1"),
    _C("KPR3-LADDER-D", "8754", "(d) The lords of these houses in the Sub of the significators"),
    _C("KPR3-TENANT", "7883-7884", "Tenant is stronger than owner."),
    _C("KPR3-NODES-STRONGER", "9441-9442", "Remember nodes are stronger than planets."),
    _C("KPR3-NODE-AGENT", "2571-2573",
       "(Rahu or Kethu will give the results of the planets with which it is conjoined then those "
       "of the planet which aspects them. Lastly, those of the lord of the sign)."),
    _C("KPR3-NODE-CONJ", "14471", "A node, conjoined with a planet gives the results of the planet."),
    _C("KPR3-6812", "6671-6674",
       "Similarly, for each house we have to note whether the significator of the house, is posited "
       "in the constellation and sub of the significator of the houses 6, 8 and 12 counted from "
       "that particular sign."),
    _C("KPR3-CUSP-SUB", "6754-6755",
       "(2) If the sub lord of the Ascendant is the significator of the ascendant and second house, "
       "one gains money;",
       note="Opens the cusp chapter: what follows when a cusp's sub-lord is the significator of "
            "given houses."),
    _C("KPR3-RP", "24916-24925",
       "( 1 ) The lord of the day. (2) Lord of the star in which Moon transits. (3) Lord of the sign "
       "(Rasi) in which Moon transits. (4) Lord of the lagna sign or the sign in which the Ascendant "
       "transits. (5) The lord of the star rising in the east"),
    _C("KPR3-RP-FOUR", "24764-24766",
       "(1) Note the lord of the day when the query is answered; (2) Note the star at that time",
       note="The same book lists four ruling planets here and five at 24916-24922."),
    _C("KPR3-PERIODS", "8741-8742",
       "Still one's status will improve in their periods and sub- periods, if they are in the sub "
       "of the Significators of 2 or 6 or 1 1 ."),
    _C("KPR3-DBA-PICK", "9447-9449",
       "Among the significators, Kethu is the strongest and hence choose Kethu Anthra."),
    _C("KPR3-MARRIAGE-HOUSES", "14306-14307",
       "That is why houses 2, 7 and 1 1 are examined to find out whether:"),
    _C("KPR3-H7-DENIAL", "21495-21497",
       "The sub-lord of the 7th cusp should be the significator of the houses 1, 6, 10 0112. It "
       "shows that the marriage will not take place with the party in question.",
       status="extended",
       note="'0112' is OCR for 'or 12'. Stated for a horary question; the engine applies the "
            "same 7th-cusp test to the natal chart (ruling R7)."),
    _C("KPR3-FINANCE-SUB", "8742",
       "if they are in the sub of the Significators of 2 or 6 or 1 1"),
    _C("KPR3-RETIRE", "9425-9426",
       "Houses 2, 6 & 1 0 indicate service. So 12th house to the above i.e 1 , 5 & 9 show end of "
       "service or retirement."),
    _C("KPR3-BUSINESS", "17816-17817",
       "whether one will do business, is to be judged from the significator of 7 and the 7\" cusp "
       "sublord.", note="'7\"' is OCR for 7th."),
    _C("KPR3-HEALTH", "6663-6664",
       "(a) As regards health, the significator of the ascendant should not be the significator of "
       "the houses 6 or 8 or 12."),
    _C("KPR3-CUSP-LORD", "17845-17846",
       "Lord of the sign in which 7th cusp falls is Jupiter.",
       note="House lord = lord of the sign on the (Placidus) cusp."),
    _C("KPR3-STAR-OCCUPIED", "7036-7038",
       "A planet 'A' offers the results of the house occupied by that planet B\u2019 which is the "
       "lord of the star wherein this planet \u2019A\u2019 is deposited."),
    _C("KPR3-GENERAL", "6676-6677", "The above is the general principle."),
    _C("KPR3-ASC-SICK", "6774-6776",
       "(6) It the sub lord of the Ascendant is not only the significator of lagna but also that "
       "of 6th house, one will have sickness;", note="'It' is OCR for 'If'."),
    _C("KPR3-ASC-11", "6814-6815",
       "Cure to disease, speedy recovery and taking prophylactic medicines preventing diseases, "
       "are promised.", note="From rule (11): sub lord of the ascendant the significator of 1 and 11."),
    _C("KPR3-CALMLY", "6918-6919",
       "Thus one is to find out to which house a planet is the significator and calmly judge what "
       "it can do.", note="Krishnamurti leaves the final weighing to the astrologer."),
)}
