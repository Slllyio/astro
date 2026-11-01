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
#: Reader 4 ("Marriage, Married Life & Children"), OCR'd 2026-11-01 with tesseract 4.1.1 from
#: the page scans in ``sources/kp-readers/J_KP reader_4_..._jp2.zip``. Each page is preceded
#: by ``<!-- page N (scan NNNN) -->``; book page = scan number - 3.
READER4_FILE: Final[str] = (
    "data/knowledge_library/sources/kp_reader4_marriage/chapter_001_full-text-unsplit.md"
)
#: Every page-cited Reader (OCR'd 2026-11-01 the same way). ``p.N`` is the page marker in the
#: file (scan number minus the offset in its YAML header). In Reader 5 the printed folio from
#: p.150 on is two higher than the marker (the book reuses Reader 3 pages); citations use markers. Key = the ``source`` field of a :class:`Citation`.
PAGE_SOURCES: Final[dict[str, str]] = {
    "KPR1": "data/knowledge_library/sources/kp_reader1_casting/chapter_001_full-text-unsplit.md",
    "KPR4": READER4_FILE,
    "KPR5": "data/knowledge_library/sources/kp_reader5_transits/chapter_001_full-text-unsplit.md",
    "KPR6": "data/knowledge_library/sources/kp_reader6_horary/chapter_001_full-text-unsplit.md",
}


@dataclass(frozen=True, slots=True)
class Citation:
    """One verbatim passage of a KP Reader.

    ``source`` is ``"KPR3"`` (Reader 3, cited by line of the library file) or
    ``"KPR4"`` (Reader 4, cited by printed book page; the OCR file marks each
    page, see ``READER4_FILE``).
    """

    key: str
    lines: str
    quote: str
    status: str = "cited"
    note: str = ""
    source: str = "KPR3"

    def ref(self) -> str:
        """Short reference such as ``KPR3:3402-3404`` or ``KPR4:p.106``."""
        return f"{self.source}:{self.lines}"


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
    _C("KPR4-LADDER", "p.118",
       "You have clearly said that occupants are stronger than owners. Constellations are stronger "
       "than signs.", source="KPR4",
       note="Followed on the same page by the ladder (1)-(5), identical to Reader 3's."),
    _C("KPR4-NODES", "p.121",
       "The nodes having no sign of their own first offer the results of the planets with which "
       "they are conjoined and secondly of the lord of the sign in which they are placed.",
       source="KPR4", note="No aspect step: supports ruling R6/R8."),
    _C("KPR4-PROMISE", "p.121",
       "Note the sub-lord of the 7th cusp. If it is a significator of house 7 or 2 or 11, "
       "marriage is promised", source="KPR4"),
    _C("KPR4-DENIAL", "p.105",
       "According to Krishnamurti Padhdhati a person is denied of marriage when the 7th Cusp sub "
       "lord is deposited in tbe constellation of the significators of 4, 6 and 10 because the "
       "houses 2, 7 and 11 show the marriage,", source="KPR4", note="'tbe' is OCR for 'the'."),
    _C("KPR4-DENIAL-SIMPLE", "p.106",
       "The simple rule is, note the sublord of the 7th Cusp; if the sub lord is connected with "
       "4, 6, 10th houses, one will be denied of marriage.", source="KPR4"),
    _C("KPR4-STRONGER", "p.106",
       "Rahu occupying Venus sign and conjoined with it shows that 6th house result is stronger "
       "than 7. Further Rahu is in the sub of Saturn in the 12th house.", source="KPR4",
       note="His worked denial case: the 7th sub-lord is tied to 6 and to 7; the stronger tie "
            "(occupation of 6 over agency for 7) decides, and Rahu's own sub-lord confirms."),
    _C("KPR4-SUB-RESPONSIBLE", "p.106",
       "it is the sub lord which is mainly responsible to give clear idea, and correct picture.",
       source="KPR4"),
    _C("KPR4-SUB-1-6-10-12", "p.118",
       "But if the sub is lord of 1, 6, 10 and is the significator of 12 houses, marriage cannot "
       "take place.", source="KPR4",
       note="Stated for choosing among significators (timing), not for the 7th cusp itself."),
    _C("KPR4-SATURN-DELAY", "p.109",
       "Whenever Sani happens to be a significator of a particular matter, it will not deny but "
       "will cause delay.", source="KPR4"),
    # --- Children and the matter/event registry (added 2026-11-01) ---
    _C("KPR3-CHILD", "21258-21262",
       "But if the sub lord of the 5th cusp is the significator of 1 or 4 or 10 he can never have "
       "a child at all. Houses 1, 4, 10 are detrimental to the birth of children, being the 1 2'h. "
       "(negation) to houses 2, 5 and 1 1 .",
       note="'1 2'h' = 12th; '1 1' = 11. Stated in a horary passage; the preceding line gives "
            "the promise side (2, 5 or 11)."),
    _C("KPR3-ENGAGEMENT", "20977-20983",
       "The significators of the house 2, 7 and 11 denote marriage in their conjoined periods. But "
       "the planets which are the significators of 2 or 7 or 11 is also the significator of 3 and "
       "also 9 the marriage will be engaged in their conjoined periods."),
    _C("KPR3-DEPUTATION", "20988-20990",
       "Here the houses 5, 9 and 11 are to be judged. The significators of 11, will be the "
       "significator of the 12th also, denoting life or service in a new place."),
    _C("KPR3-MONEY", "9800-9801",
       "Generally, houses 2, 10 and 11 are studied to understand how one makes money"),
    _C("KPR3-BUSINESS-HOUSES", "17796", "For business, judge houses 2, 7 and 10."),
    _C("KPR3-BUILDING", "12896-12898",
       "To own any building, one is to note the house 4, 11 and 12. Fourth house denotes permanent "
       "possession 12'; indicates issue of a cheque; 1 1th indicates the gains.",
       note="12'; = 12th; 1 1th = 11th."),
    _C("KPR3-DISPOSAL", "11594", "For disposal, study the houses 3, 5 and 10."),
    _C("KPR3-STUDY", "15192-15198",
       "one is to judge the houses 4 and 1 1 . If one has to work himself, do research, submit "
       "thesis etc., or if one is to leave his native place, remain in a hostel in the foreign "
       "land, leaving his kith and kin and enjoying new surroundings environments, one is to judge "
       "the houses 9 and 12"),
    _C("KPR3-SCHOLARSHIP", "15084-15085",
       "Scholarship is a non-refundable loan with a string attached to it. Hence judge houses 6 "
       "and 1 1 ."),
    _C("KPR3-TRANSFER", "18767-18768",
       "For transfer judge houses 3, 9 and 12 which includes change of residence also. They "
       "should be connected with house 6 or 10."),
    _C("KPR3-OVERSEAS", "15236-15238",
       "As regards overseas, judge the house 12 as it promises, separation from family, living in "
       "new surroundings and environments."),
    _C("KPR3-REGAIN", "19232-19235",
       "To regain one's position, one has to judge the house 10 and 11, as lOt house indicates the "
       "position, fame, reputation and honour in profession",
       note="'lOt' = 10th."),
    _C("KPR3-CONFINEMENT", "21221-21222",
       "Therefore 3, 8 and 12 indicate imprisonment. Detention in one's own house is judged from "
       "the house 4, 8 and 12."),
    _C("KPR3-LONGEVITY", "7966-7970",
       "Houses 1, 8 and 3 are to be examined to ascertain, whether",
       note="Cited only to record the deliberate omission (ruling R20): longevity and maraka "
            "timing are not encoded."),
    _C("KPR4-CHILD-HOUSES", "p.216",
       "For children, one has to examine the houses 2, 5 and 11 ; also one should note the "
       "strength of Jupiter.", source="KPR4"),
    _C("KPR4-CHILD-DENIAL", "p.106",
       "4th house indicates failure in love affairs and also denial of children or separation "
       "from them.", source="KPR4"),
    # --- Reader 1 (casting), Reader 5 (transits), Reader 6 (horary): added 2026-11-01 ---
    _C("KPR1-PLACIDUS", "p.43",
       "The method in commen use is that followed by Placidus, geatfally knowns as \u201cSei Are System\",",
       source="KPR1", note="OCR of 'common', 'generally known as \"Semi Arc System\"'."),
    _C("KPR5-LADDER", "p.153",
       "(1) Planets in the constellation of the occupants. (2) Occupants, (3) Planets in the "
       "constellation of owners. (4) Owners,", source="KPR5"),
    _C("KPR5-NODE-STAR", "p.152",
       "VII. Jupiter and Sun in moola, VIII. Kethu in Dhanishta.", source="KPR5",
       note="Ruling R6a: Sun and Jupiter in Ketu's star take only Ketu's occupied house (7); "
            "his table on p.154 gives Sun 2, 7, 5 and Jupiter 7, 5, 6, 9, without Ketu's agent houses."),
    _C("KPR5-SOURCE", "p.159",
       "Thus the source is indicated by the transiting planet and what will happen is shown by the "
       "lord of the constellation, whether it will materialise or not, whether it is favourable or "
       "not, is indicated by the sublord according to the houses signified by the sublord.",
       source="KPR5"),
    _C("KPR5-DBA-POINTS", "p.160",
       "Therefore when A dasa B Bhukthi C Anthra operates, that part of the Zodiac governed by "
       "these three will be transited by them, or luminaries and Lagna.", source="KPR5"),
    _C("KPR5-GROUP", "p.160",
       "Thus there are four different points for the group of Mars, Saturn and Mercury.",
       source="KPR5"),
    _C("KPR5-PLACE", "p.160",
       "One should not always calculate the ascendant for the place of birth unless the native is "
       "permanent in his birth place.", source="KPR5"),
    _C("KPR6-NUMBER", "p.99",
       "number 48 refers to Mercury sign, Rake star, Jupiter sub, which commences at 8\u00b0 40\u00b0 nm Gemmi-",
       source="KPR6", note="OCR: 'Rahu star', 'in Gemini'. The same page later prints the number as '43'."),
    _C("KPR6-AYANAMSA-ADD", "p.99",
       "Therefore, it 1s peceseary \\o add the Ayenamesa of that date of judgment to the position "
       "of the Ascendam, arrived at for the umber given by the con- sultant.", source="KPR6"),
    _C("KPR6-LATITUDE", "p.100",
       "One is to take the lati- tude of the place where the astrologer fudges the horoscope even "
       "though the consultant would have written from any part of the world.", source="KPR6",
       note="'fudges' = judges."),
    _C("KPR6-PLANETS-TIME", "p.103",
       "If you yudge a chart mmedately after calculation, then you have to note the position of "
       "the planets at whsch you started casting of the horoscope for judgment.", source="KPR6"),
    _C("KPR6-RP", "p.123",
       "All the above lords are called the Ruling planet\u2019.", source="KPR6"),
    _C("KPR6-RP-RETRO", "p.123",
       "Among these, these deposited in the constellation of a retrograde planet should be "
       "rejected.", source="KPR6"),
    _C("KPR6-CSL-RETRO", "p.124",
       "If the lord of the constellation in which third cusp sub-lord is deposited is retrograde, "
       "the call will not materialise.", source="KPR6"),
    _C("KPR6-RP-COMMON", "p.126",
       "The common ones found among the significators are Sun, Jupiter and Venus. These planets "
       "conjointly indicate the time of fructification of the trunk call", source="KPR6"),
    _C("KPR6-TRUNK", "p.126",
       "It can be Venus sign, Jupiter star, Sun sub, Venus sub sub.", source="KPR6"),
    _C("KPR6-TRUNK-RESULT", "p.127",
       "As predicted the telephone trunk call came through sharp at 9-41 A.M.", source="KPR6"),
    _C("KPR6-FRIEND", "p.128",
       "the lagna was _ transiting in the sub sub of Rahu in the sub of SUN in the star Rohini",
       source="KPR6"),
    _C("KPR6-SERVANT", "p.130",
       "take the sub of Satur and sub sub of Mercury.", source="KPR6"),
    _C("KPR6-CHILD-RETRO", "p.130",
       "If the sub-lord is deposited in the constellation of a planet in retrograde motion, the "
       "child will not return home.", source="KPR6"),
    _C("KPR6-RP-BODY", "p.131",
       "If a matter is to be materialised in days and within a month you take the position of Moon "
       "and _ therefrom you calculate. But if it would take more than a month, move the Sun from "
       "the present position of the Sun.", source="KPR6"),
    _C("KPR6-RECTIFY", "p.141",
       "The ruling planets at the time of judgment will rule (a) the sign, star sub and sub sub of "
       "the position of lagna,", source="KPR6"),
    _C("KPR6-RECT-CASE2", "p.141",
       "Therefore one is to take as Mercury sign Moon star, Sun sub and Mercury sub sub. It is 23\u00b0 "
       "10\u00b0 in Virgo.", source="KPR6"),
)}