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
    # --- Reader 6 horary question rules (registry in app/kp/horary/questions.py) ---
    _C("KPR6-Q-ILLNESS", "p.158",
       'If the sub-lord of the 6th house is deposited in the constellation of a planet which is the significator of the 6 and 1 and not of 11, then the sub-lord, during its sub-period, will give the disease.', source="KPR6"),
    _C("KPR6-Q-SECOND_MARRIAGE", "p.165",
       '(i) The sub-lord of the 7th cusp is deposited in a dual sign or in the constellation of a planet in or owning a dual sign or if the sub-lord of the 7th cusp is Mercury ; and (11) the sub-lord of the 7th cusp is also a significator of either of the houses 2 or 11.', source="KPR6"),
    _C("KPR6-Q-APPEAL", "p.168",
       'If the sub-lord of the third cusp is deposited in the constel- lation of a planet which is the significator of 6 and 11 then one will have success. But if the sub-lord of the 3rd cuspls deposit- ed in the constellation of a planet who is the significator of the houses 5 and 12, one cannot have success.', source="KPR6"),
    _C("KPR6-Q-EXCHANGE_6", "p.173",
       'If the sub-lord of the 6th cusp is deposited in the constellation of a planet which is the significator of 6 or 11, you gain. But if It is the significator of 5 or 12, by so exchanging you must lose', source="KPR6"),
    _C("KPR6-Q-EXCHANGE_12", "p.173",
       'If the sub-lord of the 12th cusp is deposited in the constellation of the significators of 6 and 11, you gain. But if the sub-lord of the Izth is in the constellation of a planet, signifying 5 and 12, definitely you must incur loss.', source="KPR6"),
    _C("KPR6-Q-TREASURE", "p.191",
       'If the sub-lord of the 4th cusp is deposited in a constellation, lord of which is the significator of the houses 2 or 11 or 6 one will surely have the treasure.', source="KPR6"),
    _C("KPR6-Q-LOVE_AFFAIR", "p.191",
       'If the sub-lord of the 5th cusp is deposited in the constella- tion of a planet who is the significator of the houses 7 and 11 then materialisation of the love affairs is promised. But if the sub-lord of the 5th cusp happens to be in a constellation, the lord of which is the significator of the houses 6 or 12 then it will never materialise.', source="KPR6"),
    _C("KPR6-Q-CHILD_RECOVERY", "p.191",
       "If the sub-lord of the 5th cusp is deposited in a constellation, the lord of which is the significator of the houses 3 and 5, the child will pick'up.", source="KPR6"),
    _C("KPR6-Q-BUSINESS_PARTNER", "p.192",
       'If the sub-lord of the 8th cusp is situated in the constellation of a planet signifying houses 6 and Il. you can have a partner. But if the sub-lord of the 8th cusp is deposited in a constellation, the lord of which is the significator of the houses 5 and 12. never have a partner.', source="KPR6"),
    _C("KPR6-Q-ACTOR", "p.192",
       'If the sub-lord of the 5th cusp is deposited in a constellation of a planet who is the significator of the houses 5. 6 and 10 one can be popular as an Actor.', source="KPR6"),
    _C("KPR6-Q-CHILDREN", "p.192",
       'the 5th cusp is not | retrograde. (i) It is not posited in a constellation of a retrograde Planet and (iii) It is a significator of either 2nd or Sth or 11th house. If any one of these three conditions is not satisfied, one will not be able to produce a child at all.', source="KPR6"),
    _C("KPR6-Q-LOTTERY", "p.213",
       'If the sub lord and the lord of the constellation in which the sub lord is situated are in direct motion and if such a sub-lord of 11th cusp is also a significator of the houses 2 or 6,or 11, then one will win', source="KPR6"),
    _C("KPR6-Q-PARTNERSHIP", "p.253",
       'Note the sub lord of the seventn. If it is connec- IV 17.15 arer ted with houses 6 and Sun 6-51 12, the partnership will ems break.', source="KPR6"),
    _C("KPR6-Q-DOWRY", "p.256",
       'Therefore, the sublord of the eighth cusp must be deposited in the constellation of the planet who signifies the matters of the houses 6 and 11. But if the sublord of the eighth cusp happens to be the significator of 5 and 12, then the consul- tant is to give.', source="KPR6"),
    _C("KPR6-Q-SCHOLARSHIP", "p.257",
       'will have the sublord of the 11th cusp deposited in the constellation of a planet who is the significator of 2, 6 and 11 and should not be a significator of 8 or 12.', source="KPR6"),
    _C("KPR6-Q-GO_ABROAD", "p.265",
       'If the sub-lord and the lord of ths constellation tn which the sub-lord is situated are in direct motion and if the sub-lord of the 12th cusp is also a significator of either 3rd or 9th or 12th house, one goes abroad.', source="KPR6"),
    _C("KPR6-Q-PROMOTION", "p.288",
       'If the sub-lord and the lord of the constellation In which it is situated are in direct motion and if the same sub-lord is also a significator of houses 2 or 6 or 10 or 11, then promotion is promised.', source="KPR6"),
    _C("KPR6-Q-PRESS", "p.307",
       'if the sub-lord of the meridian is deposited in the constell- ation of a planet which is the significator of at least one of the three houses 2, 6 and 10', source="KPR6"),
    _C("KPR6-Q-SPIRITUAL", "p.308",
       'One is to find out the sub-lord of the 11th: if it is depo” sited in the constellation of a planet who is the significator of 5 and 10, one will surely have the satisfaction in the spiritual life.', source="KPR6"),
    _C("KPR6-Q-SANYASI", "p.308",
       'one can become a Sanyasi only when the sub-lord of the Ascendant is connected with the houses 3, 10 and 12 and it is In any manner connected with Saturn.', source="KPR6"),
    _C("KPR6-Q-REAPPOINTMENT", "p.308",
       'The sub-lord of the 6th cusp Is to be deposited in the constellation, the lord of which is the signifi- cator of the 6th or 10th or 2nd then he will be re-appointed. But if the sub-lord is in the constellation lord of which is the Ssignificator or 1 or 5 or 9 or 12th house he will not be re- appointed.', source="KPR6"),
    _C("KPR6-Q-PASSPORT", "p.321",
       'If the sub-lord of the 11th cusp is in the constellation of the silgnifictor of the houses 3, 9 ana 11, you will surely get the', source="KPR6"),
    _C("KPR6-Q-SETTLE_ABROAD", "p.322",
       'sub-lortj of 11th cusp is io the constellation of significator of 11 and 2 you will surely live in foreign place.', source="KPR6"),
    _C("KPR6-Q-OVERSEAS", "p.322",
       'If the sub-lord of the 11th is in the constellation of the planet who is the significator of 3, 9 and 12, you will surely proceed to foreign countries.', source="KPR6"),
    _C("KPR6-Q-HIGH_POSITION", "p.322",
       'If the sub-lord of the IJth cusp is in the constellation of the planet who is the significator of the 9th, the Ifith andLitth', source="KPR6"),
    _C("KPR6-Q-SERVANT", "p.322",
       'But, if you appoint him ata time when the sub-lord of the ascendant is the significator of 6 and 11, yon will surely have satisfaction.', source="KPR6"),
    _C("KPR6-Q-BUY_ARTICLE", "p.322",
       'The sub-lord of the second house must be deposited in the constellation of a planet which is the Significator of 6 and 11.', source="KPR6"),
    _C("KPR6-Q-SELL_ARTICLE", "p.322",
       'The sub-lord of the i2th must be situated in the’ constella- tion, the lord of which is the significator of the houses 6 and 11.', source="KPR6"),
    _C("KPR6-Q-ENTER_SERVICE", "p.322",
       'The sub-lord of the sixth is to he deposited in the constella- tion of the planet signifying houses 10-and 11.', source="KPR6"),
    _C("KPR6-Q-SIGN_AGREEMENT", "p.323",
       'The sub-lord of the third cusp is to be deposited fa a cons- tellation, the lord of which is the significator of the houses 6 and 11.', source="KPR6"),
    _C("KPR6-Q-START_BUSINESS", "p.323",
       'To start a business : The sub-lord of the 7th is to be deposited in the constellation the lord of which is the significator of the houses 6 and 11.', source="KPR6"),
    _C("KPR6-Q-RELEASE_FILM", "p.323",
       'To release a film: The sub-lord of the 7th is to be deposited in the constellation, the lord of which 4s the significator of 6 and 11.', source="KPR6"),
    _C("KPR6-Q-LAY_FOUNDATION", "p.323",
       'The sub-lord of the fourth is to be deposited in the constel- lation of the significator of the 11th and not a significator of 5 and 12.', source="KPR6"),
    _C("KPR6-Q-OVERSEAS_PROBATION", "p.323",
       'If the sub-lord of the 6th cusp is deposited in the constella- tion of a planet which is the significator of 9 and 12, you go overseas, only for probation, training or education.', source="KPR6"),
    _C("KPR6-Q-PROMOTION_6TH", "p.323",
       'But, if the sub-lord of the 6th cusp is deposited in a constellation, the lord of which Is a significator of the 11th house and also either 6 or 10, you are sure to have promotion.', source="KPR6"),
    _C("KPR5-LEVEL-E", "p.153",
       '(5) Very weak but yet those connected with a bhava are those planets conjoined with or aspected by the significators found out already.', source="KPR5",
       note="Level E: weakest significators, used only when levels A-D leave a house unsignified or on request."),
    _C("KPR6-LEVEL-E", "p.197",
       '(e) those which are conjoined with these significators; or (f) those receiving aspects from the indicators.', source="KPR6"),
    _C("KPR6-DRISHTI", "p.288",
       'Further Saturn (owner of 11th) aspects Moon by its 10th aspect. Jupiter (owner of 10th) aspects Moon by its 5th aspect.', source="KPR6",
       note="KSK counts the special Hindu (drishti) aspects; the engine uses 7th for all, 4/8 Mars, 5/9 Jupiter, 3/10 Saturn, none for the nodes.",
       status="extended"),
    _C('KPR3-IND-ASC_1_2', '6752-6756',
       '(2) If the sub lord of the Ascendant is the significator of the ascendant and second house, one gains money;'),
    _C('KPR3-IND-ASC_1_3', '6757-6762',
       '(3) If the sub lord of the ascendant is the significator of the ascendant and 3rd house, ,ne has good mental development;'),
    _C('KPR3-IND-ASC_1_4', '6763-6767',
       '(4) If the sub lord of the Ascendant is the significator of houses 1 and 4, one has good education, studious, gains through estates, mines, etc.'),
    _C('KPR3-IND-ASC_1_5', '6768-6772',
       '(5) If the sub lord of the ascendant is the significator of houses 1 and 5, one has much delight in sports, speculation and pleasurable pursuit.'),
    _C('KPR3-IND-ASC_1_6', '6775-6777',
       '(6) It the sub lord of the Ascendant is not only the significator of lagna but also that of 6th house, one will have sickness;'),
    _C('KPR3-IND-ASC_1_7', '6782-6787',
       '(7) If the sub lord signifies 1 and 7, public enemies disappear, there will be union; partnership;'),
    _C('KPR3-IND-ASC_1_8', '6787-6790',
       '(8) If the sub lord is the significator of 1 and 8 one will meet with danger.'),
    _C('KPR3-IND-ASC_1_9', '6794-6800',
       '(9) If the sub lord of the ascendant is the significator of 1 and 9, one likes his father,'),
    _C('KPR3-IND-ASC_1_10', '6801-6807',
       '(10) If the sub lord of the ascendant is the significator or 1 and 10 houses, one does meritorious deed, held in high esteem:'),
    _C('KPR3-IND-ASC_1_11', '6809-6812',
       '(11) If the sub lord of the ascendant is the significator of 1 and 11, large profits; large number of benefactors.'),
    _C('KPR3-IND-ASC_1_12', '6817-6820',
       '(12) If the sub lord of the ascendant is the significator of 1 and 12, there will be enough of troubles, jealousy, secret inimical'),
    _C('KPR3-IND-SECOND_2_1', '6831-6836',
       'If the sub lord of the 2nd cusp is the significator of 1 and 2 then the native will be finding it easy to make money by his personal efforts;'),
    _C('KPR3-IND-SECOND_2_3', '6844-6850',
       'If the sub-lord of the second cusp is the significator of the second and the third, one can gain through education, writing, publicity, Publication, journalism,'),
    _C('KPR3-IND-SECOND_2_4', '6852-6857',
       'If the sub-lord of the second cusp is the significator of the second and the fourth house, then one gets estates and money as inheritance'),
    _C('KPR3-IND-SECOND_2_5', '6859-6860',
       'If the sub-lord of the second cusp is the significator of 2nd and 5tn houses, one gains through music opera, cinema, pleasant'),
    _C('KPR3-IND-SECOND_2_6', '6868-6870',
       'If the sub-lord of the second cusp is the sign ii:;cator of the houses 2 and 6. one makes profit in any transaction.'),
    _C('KPR3-IND-SECOND_2_7', '6876-6881',
       'If the sub-lord of 2nd cusp is the significator of 2 and 7 one gains through partner in business or by marriage,'),
    _C('KPR3-IND-SECOND_2_8', '6882-6886',
       'If the sub-lord of the second is the significator of the houses 2 and 8 one can gain, by legacy, Insurance bonus, gratuity or by will.'),
    _C('KPR3-IND-SECOND_2_9', '6889-6895',
       'If the sub-lord of 2 is the significator of 2 and 9 one makes money by export, and import by publication of books,'),
    _C('KPR3-IND-SECOND_2_10', '6896-6903',
       'If sub-lord of the 2nd cusp is the significator of the second and the tenth house, one makes steady progress, ever prosperous,'),
    _C('KPR3-IND-SECOND_2_11', '6905-6909',
       'If the sub-lord of the second cusp is the significator of the houses 2 and 1 1 one makes money without much effort, gains without pains,'),
    _C('KPR3-IND-SECOND_2_12', '6912-6916',
       'If the sub-lord of the second cusp is the significator of 2 and 1 2, one can make money by serving in a sanatorium, asylum, hospital,'),
    _C('KPR3-IND-SECOND_IS_MERCURY', '14148-14152',
       'if the sublord of the 2nd cusp is Mercury, one speaks a lot, best fitted for Insurance agent, salesman, propagandist, etc.'),
    _C('KPR3-IND-SECOND_IS_MARS', '14152-14155',
       'if the sub-lord is Mars, one will be blunt and outspoken; it is Saturn, he speaks a little and he drags on; if Jupiter, wise talk; if Venus, mostly the talk will be about the other sex or sexual life.'),
    _C('KPR3-IND-THIRD_IS_MARS', '21078-21081',
       'One is never contented if the sub-lord of the third house is Mars.'),
    _C('KPR3-IND-ELEVENTH_RETRO', '21017-21021',
       "If the sub-lord of the 1 1 'h cusp is retrograde then only whatever he desires to have will not be had."),
    _C('KPR3-IND-ASC_STAR_6_8_12', '14025-14028',
       'If the sub-lord of the Ascendant is in the constellation of the significator of 6 or 8 or 12 then one suffers from disease or faces danger or is hospitalised.'),
    _C('KPR3-IND-EIGHTH_DEBT', '9854-9858',
       'If the sublord of 8th cusp is the significator of houses 5, 6, 8 and 12 difficulties come as a battalion and he has to face them by borrowing'),
    _C('KPR3-IND-EIGHTH_REPAY', '9858-9863',
       'But if the sublord of the 8th Cusp is the Significator of 2, 10 or 1 1- houses and if its period or sub-period runs, with pleasure, he returns the money.'),
    _C('KPR3-IND-FIFTH_MUSICIAN', '17879-17881',
       'If the sublord of the 5th cusp is deposited in the constellation of a planet situated in Leo or Aquarius, one will be a popular musician.'),
    _C('KPR3-IND-TENTH_ARIES', '17330-17332',
       'If the sub-lord of the Meridian is in the constellation of the planet in Aries, generally you are attached to the Army or military or Police or Fire-brigade or any such job.'),
    _C('KPR3-IND-ASC_STAR_IN_ARIES', '21611-21616',
       'If the sub-lord of your Ascendant is in the constellation of a planet in ARIES:- You would change your views quite suddenly without any consideration:'),
    _C('KPR3-IND-ASC_STAR_IN_TAURUS', '21646-21650',
       'If the sub-lord of your Ascendant is in the constellation of a planet in TAURUS:- Your feelings will be extremely concentrated and they will create many enemies — all undesirable.'),
    _C('KPR3-IND-ASC_STAR_IN_GEMINI', '21682-21684',
       'If the sub-lord of the ascendant is in the constellation of the planet occupying GEMINI:-'),
    _C('KPR3-IND-ASC_STAR_IN_CANCER', '21719-21724',
       'If the sub-lord of the ascendant is deposited in the constellation of the planet situated in CANCER: You have the tendency to imagine slights,'),
    _C('KPR3-IND-ASC_STAR_IN_LEO', '21758-21761',
       'If the sub lord of your Ascendant is in the constellation of a planet in LEO:- Your thirst for personal glory is unquenchable.'),
    _C('KPR3-IND-ASC_STAR_IN_VIRGO', '21796-21799',
       'If the sub-lord of your Ascendant is in the constellation of a planet in VIRGO:- Your nature is to be chatty.'),
    _C('KPR3-IND-ASC_STAR_IN_LIBRA', '21834-21837',
       'If the sub-lord of your Ascendant is in the constellation of a planet in LIBRA:- YOU HAVE TO KEEP YOUR EMOTIONS IN CHECK.'),
    _C('KPR3-IND-ASC_STAR_IN_SCORPIO', '21878-21882',
       'If the sub-lord of your Ascendant is in the constellation of a planet in SCORPIO:- You generally over-estimate yourself and thereby invite trouble.'),
    _C('KPR3-IND-ASC_STAR_IN_SAGITTARIUS', '21920-21923',
       'if the sub-lord of your Ascendant is in the constellation of a planet in SAGITTARIUS:- Generally you are inherently selfish and inconsiderate.'),
    _C('KPR3-IND-ASC_STAR_IN_CAPRICORN', '21965-21969',
       'If the sub-lord of your Ascendant is in the constellation of a planet in CAPRICORN:- You are over ambitious both to make money and also to acquire power.'),
    _C('KPR3-IND-ASC_STAR_IN_AQUARIUS', '22007-22012',
       'If the sub-lord of the Ascendant is in the constellation of the planet in AQUARIUS: You always prefer solitude;'),
    _C('KPR3-IND-ASC_STAR_IN_PISCES', '22041-22045',
       'If the sub-lord of the Ascendant is in the constellation of the planet in PISCES:- You have a very bad tendency of brooding over things'),
    _C('KPR4-IND-ASC_2_R4', 'p.248',
       'If the sub-lord of 1 is the significator of the second house, one will work hard for long number of hours and will be always after making money.', source="KPR4"),
    _C('KPR4-IND-ASC_3_R4', 'p.248',
       'If the sub lord of | is the significator of the third house, there will be much mental development, One will gain by frequent-short journeys.', source="KPR4"),
    _C('KPR4-IND-ASC_4_R4', 'p.248',
       'If the sub lord of | is the significator of the 4th house, one will be interested in lands, buildings, estates, conveyances, mines,', source="KPR4"),
    _C('KPR4-IND-ASC_5_R4', 'p.248',
       'If the sub-lord of 1 is the significator of the 5th house, one will find delight in sports, music, opera, speculation etc.', source="KPR4"),
    _C('KPR4-IND-ASC_6_R4', 'p.248',
       'If the sub-lord of | is the significator or the sixth house, one will be having ill-health, one will be susceptible to diseases,', source="KPR4"),
    _C('KPR4-IND-ASC_7_R4', 'p.248',
       'if the sub-lord of | is the significator of the 7th house, one will have good partners in life.', source="KPR4"),
    _C('KPR4-IND-ASC_9_R4', 'p.249',
       'If the sub-lord of the Ist is the significator of the 9th house, one is always desirous of proceeding on long journey.', source="KPR4"),
    _C('KPR4-IND-ASC_10_R4', 'p.249',
       'If the sub-lord of 1 is the significator of the 10th house, one earns name and fame.', source="KPR4"),
    _C('KPR4-IND-ASC_11_R4', 'p.249',
       'If the sub-lord of 1 is significator of 11, all success.', source="KPR4"),
    _C('KPR4-IND-ASC_12_R4', 'p.249',
       'If the sub-lord of 1 is the significator of 12th house, one has to suffer from secret unhappiness, secret enemies,', source="KPR4"),
    _C('KPR4-IND-CAREER_PARTNER', 'p.98',
       'One will marry a career girl if the sublord of the 4th Cusp is the Significator of 8 or 12 or 4.', source="KPR4"),
    _C('KPR4-IND-PLURAL_MARRIAGE', 'p.182',
       'If the sub-lord of the 7th cusp is either Mercury or any other planet occupying a dual sign or deposited in the constellation of a planet in a dual sign, there will be more than one marriage.', source="KPR4"),
    _C('KPR4-IND-SECOND_MARRIAGE_2ND', 'p.146',
       'Further if the sub lord of the second cusp is connected with 7th house, second marriage;', source="KPR4"),
    _C("KPR4-PARTNER", "p.86",
       'Note the sub-lord of the 7th cusp. Find out in which sign the sub-lord is posited. The result depends on the nature of the planet and also the sign occupied by it.', source="KPR4"),
    _C("KPR4-PARTNER-NODES", "p.97",
       'the results should be referred to that planet with which Rahu or Kethu is conjoined ; if no planet is conjoined with Rahu or Kethu, then read the result of the planet which aspects Rahu or Kethu; if no planet is conjoined with and no planet aspects then take the lord of the star in which Rahu or Kethu was.', source="KPR4"),
    _C("KPR4-LOVE", "p.156",
       'LOVE AND LIFE IF THE SUB LORD OF THE Sth CUSP IS IN Aries: Male:', source="KPR4",
       note="'Sth' is the OCR of '5th'."),
    # --- Selecting strong and fruitful significators (rulings R24-R26, added 2026-11-02) ---
    _C("KPR4-ELIMINATE", "p.118",
       '"When majority of the planets are connected with the houses 2, 7 and 11, how to eliminate '
       'the useless ones and select the useful ones".', source="KPR4"),
    _C("KPR5-STAR-DWELLERS", "p.208",
       "If there is planet in the star of the occupant, the planet situated in the star will give "
       "the results of the Bhava occupied by the lord of the star", source="KPR5"),
    _C("KPR5-OCCUPANT-EMPTY", "p.209",
       "If there is no planet in any of the 3 stars of the occupant, then the occupant offers the "
       "results of the bhava occupied by it and it is stronger than the lord of the house.",
       source="KPR5"),
    _C("KPR5-LORD-EMPTY", "p.147",
       "Planets, if deposited in these stars will refer the matters signified by first house. If "
       "there is no planet, Sun gives lagna bhava results.", source="KPR5",
       note="Sun is the lord of an unoccupied lagna in his example: the lord's star-dwellers, else the lord."),
    _C("KPR6-TAKE-NODE", "p.162", "Kethu in Virgo represents Mercury. Take Kethu.", source="KPR6"),
    _C("KPR4-NODE-STAR", "p.190",
       "No planet in 7 lord is Saturn. Kethu represents Saturn Rahu is in Kethu star and Rahu is a "
       "significator.", source="KPR4"),
    _C("KPR4-USEFUL", "p.118",
       "Ruling planets at the moment of judgement must agree. Further the sub lord of each of the "
       "significators. If a planet is in such a position that its sub lord is connected with the "
       "houses 2, 7 and 11 then this planet is useful.", source="KPR4"),
    _C("KPR5-SUB-THRIVE", "p.147",
       "the depositor in that constellation is in the favourable sub matters indicated by lagna "
       "will thrive. Ifthe depositor in that constellation is in unfavourable sub the matters "
       "indicated by the lord of the constellation as per its occupation or ownership will suffer.",
       source="KPR5"),
    _C("KPR6-RETRO-FAIL", "p.280",
       "When the significator touches that point, one has his matter materialised in one\u2019s "
       "favour if it is in direct motion. One meets with f ailure on that day when the significator "
       "touches that point and it is retrograde.", source="KPR6",
       note="'f ailure' is OCR for 'failure'. Stated for the day a significator transits the point."),
    _C("KPR4-RP-BENEFACTORS", "p.189",
       "Now the question arises how to select the strongest and the fruitful ones. I have "
       "discovered that the ruling planets at the moment of judgment will be helpful and they are "
       "the real benefactors.", source="KPR4"),
    # --- Day-fixing by transit (ruling R27, added 2026-11-02) ---
    _C("KPR4-DAY-FIX", "p.133",
       "Sun, lord of 2, to fix the day must transit in Venus sign, Moon star Saturn or Ketu sub.",
       source="KPR4", note="Venus, Moon, Saturn and Ketu are the favourable significators he selected (same page)."),
    _C("KPR4-DAY-FIX-2", "p.189",
       "Hence the date of marriage will be on the day when Sun transits in Venus sign, Moon star, "
       "Rahu sub, i.e., 25th May 1970", source="KPR4",
       note="Venus is among his 'strongest' significators on this page but not among the ruling "
            "planets, so day-fixing draws on the significators before the ruling-planet cut."),
)}
