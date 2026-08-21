"""The chart feedback instrument — the questionnaire the reader answers about their own life.

`feedback_questions.py` asks five quick questions off the digest and shows the verdict before
asking ("your chart points to a positive time for your finances; does that match?"). That is a
satisfaction survey, not a measurement: this project's own validation measured that the median
chart carries 19 afflicted and 31 favourable significations simultaneously and that 97.1% of
charts offer both poles at once (CLAUDE.md, MEASURED TRUTH). A reading that says something about
everything can be agreed with by anyone, so agreement with a SHOWN claim costs nothing and means
nothing.

This module builds the instrument that can actually be scored. Four parts, in a fixed order:

  A. BLIND — plain life questions with no astrology in them. Answered first, ideally before the
     reading is read at all. This is the only unbiased evidence the reader can give.
  B. RECTIFICATION — how far the ascendant sits from its own cusp, and the questions that settle
     which side of it the birth really falls on. Chart-specific and computed.
  C. FORCED CHOICE — each of the chart's own distinctive readings paired with its exact inverse,
     both unlabelled, so a coin scores 50% and agreement above that is information. Ordered by
     RARITY (`1 - band_share`), never by digest position: a reading half the population shares
     cannot discriminate one life however true it feels.
  D. REACTION — what the reading got wrong, what it could not have guessed, what was skipped.

THE ANSWER KEY NEVER LEAVES THE SERVER. `build_feedback_instrument` returns the reader-facing
payload with no indication of which option is the chart's; `instrument_key` recomputes the
mapping for scoring. This is a deliberate, documented exception to the report-completeness law
(CLAUDE.md): the key is not a reading, and rendering it beside the questions destroys the only
property that makes the answers worth collecting. `test_the_key_never_rides_the_payload` pins it.

Two readings are kept in the set even though the project's own atlas proved their channels run
BACKWARDS (`inverted_warning`): they are the honesty check. A reader who agrees with those while
disagreeing elsewhere is agreeing with whatever is put in front of them, and the scorer needs to
be able to see that. They are flagged in the key, never in the payload.

Usage:
    from app.raman_saab.feedback_instrument import (
        build_feedback_instrument, instrument_key, validate_instrument_answers)

    payload = build_feedback_instrument(report_dict)              # reader-facing, no key
    payload = build_feedback_instrument(report_dict, lang="hi")   # same ids, Hindi text
    key = instrument_key(report_dict)                             # qid -> chart's own option
    errors = validate_instrument_answers(report_dict, answers)    # [] when every answer is legal
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Literal, Optional

from app.raman_saab.render import _jd_to_date

logger = logging.getLogger(__name__)

Lang = Literal["en", "hi"]

#: Bumped when the question set changes in a way that makes old answers non-comparable. Stored
#: rows carry it inside the qid (`inst.v1.C3`), so a later version never silently pools with this
#: one in the same analysis.
INSTRUMENT_VERSION = "v2"

#: The fixed scale for the agree/disagree items (Part D). Same four values the older
#: `feedback_questions` flow uses, so both write comparable rows.
ANSWER_SCALE: tuple[str, ...] = ("agree", "partly", "disagree", "not sure")

#: The four scale values in Hindi. The STORED value stays the English token whatever the reader
#: sees, so answers pool across languages — the same rule the older feedback flow follows.
_SCALE_HI: dict[str, str] = {
    "agree": "सहमत", "partly": "कुछ हद तक", "disagree": "असहमत", "not sure": "पता नहीं",
}

#: How sure the reader is of a forced choice. Asked on every Part C item — a confident wrong
#: answer and a coin-flip right one are different evidence and must not be pooled.
CONFIDENCE_SCALE: tuple[str, ...] = ("1", "2", "3", "4", "5")

#: Significations that are never asked about. `death` and `longevity` are the standing wall: no
#: answer a person can give confirms or refutes a lifespan band, the question does harm, and the
#: engine's own guard refuses the decree voice on exactly this material (CLAUDE.md, PREC-8).
#: `left_eye` is medical specificity of the kind the medical read already refuses to diagnose.
EXCLUDED_SIGNIFICATIONS: frozenset[str] = frozenset({"death", "longevity", "left_eye"})

#: One plain, everyday noun phrase per signification — what a reader would actually call that
#: part of life. Hindi phrases are plain oblique-ready noun phrases so the frame sentences below
#: attach to them without gender agreement problems.
TOPIC: dict[str, tuple[str, str]] = {
    # H1
    "self": ("you as a person", "एक व्यक्ति के रूप में आप"),
    "body": ("your build and constitution", "आपकी शारीरिक बनावट"),
    "health": ("your general health", "आपके सामान्य स्वास्थ्य"),
    # H2
    "wealth": ("your savings and what you have put by", "आपकी बचत और जमा-पूँजी"),
    "family": ("your immediate family", "आपके निकट परिवार"),
    "speech": ("the way you speak", "आपके बोलने के ढंग"),
    "vision": ("your eyesight", "आपकी दृष्टि"),
    # H3
    "courage": ("your boldness", "आपके साहस"),
    "siblings": ("your brothers and sisters", "आपके भाई-बहनों"),
    "short_journeys": ("local travel and short journeys", "स्थानीय आवागमन और छोटी यात्राओं"),
    "ear_throat": ("your ears and throat", "आपके कान और गले"),
    # H4
    "mother": ("your mother", "आपकी माता"),
    "property": ("land and property", "ज़मीन और संपत्ति"),
    "home_comforts": ("comfort at home", "घर के सुख-आराम"),
    "happiness": ("contentment at home", "घर में संतोष"),
    "education": ("your schooling", "आपकी पढ़ाई"),
    "vehicles": ("vehicles", "वाहनों"),
    # H5
    "children": ("children", "संतान"),
    "intellect": ("your intelligence and judgement", "आपकी बुद्धि और निर्णय-क्षमता"),
    "poorvapunya": ("unearned luck — speculation, windfalls, merit you did not work for",
                    "बिना मेहनत का भाग्य — सट्टा, अप्रत्याशित धन"),
    # H6
    "disease_chronic": ("long-term illness", "लंबी बीमारी"),
    "enemies": ("people who work against you", "आपके विरोधियों"),
    "debts": ("debt", "कर्ज़"),
    "accidents": ("accidents", "दुर्घटनाओं"),
    "enemies_disease": ("illness and opposition together", "बीमारी और विरोध"),
    # H7
    "spouse": ("your husband or wife", "आपके जीवनसाथी"),
    "marital_happiness": ("happiness in your marriage", "आपके वैवाहिक सुख"),
    "partnership": ("partnership with others", "दूसरों के साथ साझेदारी"),
    "coverture": ("married life as a settled state", "गृहस्थ जीवन"),
    "virility": ("your vitality in marriage", "वैवाहिक जीवन में आपकी ऊर्जा"),
    "wealth_through_marriage": ("money that came through marriage", "विवाह से आए धन"),
    # H8
    "legacies": ("inheritance", "विरासत"),
    "sudden_gains": ("sudden unexpected money", "अचानक मिले धन"),
    # H9
    "father": ("your father", "आपके पिता"),
    "fortune": ("your luck", "आपके भाग्य"),
    "higher_learning": ("higher study", "उच्च शिक्षा"),
    "dharma": ("your sense of right conduct", "आपकी नैतिक समझ"),
    "long_journeys": ("long journeys", "लंबी यात्राओं"),
    # H10
    "career": ("your career", "आपके करियर"),
    "profession_authority": ("working under authority — an employer, government, seniors",
                             "किसी के अधीन काम — नियोक्ता, सरकार, वरिष्ठ"),
    "profession_trade": ("your own trade or business", "अपने व्यापार या कारोबार"),
    "profession_learned": ("learned or professional work", "विद्या या पेशेवर कार्य"),
    "profession_labour": ("work done by service or effort", "सेवा या श्रम के काम"),
    "status_honour": ("public standing and honour", "सार्वजनिक प्रतिष्ठा और सम्मान"),
    # H11
    "gains": ("income and gains", "आय और लाभ"),
    "acquisitions": ("the things you have acquired", "आपकी अर्जित वस्तुओं"),
    "friends": ("friends", "मित्रों"),
    "elder_siblings": ("your elder brothers and sisters", "आपके बड़े भाई-बहनों"),
    # H12
    "expenditure": ("your spending", "आपके खर्च"),
    "foreign_residence": ("living far from your birthplace", "जन्मस्थान से दूर रहने"),
    "incarceration": ("confinement of any kind — hostel, institution, hospital, restriction",
                      "किसी भी तरह की बंदिश — छात्रावास, संस्था, अस्पताल, पाबंदी"),
    "loss_moksha": ("letting go, and what you have given up", "छोड़ने और त्यागने"),
    "moksha": ("your inner or spiritual life", "आपके आंतरिक या आध्यात्मिक जीवन"),
}

#: The claim frames. A verdict becomes a sentence about a life, never about a house — the reader
#: has no way to answer "the 6th is favourable" and every way to answer "debt has gone well".
#: These are PREDICATES only: the topic names itself once in the question stem, and repeating it
#: inside both options makes the pair harder to read and the difference harder to see.
_FRAME_EN: dict[str, str] = {
    "favourable": "This has gone well for you.",
    "afflicted": "This has been a real difficulty for you.",
    "mixed": "Genuinely both — real good and real difficulty together, not one or the other.",
    "one_way": "Clearly one way — either solidly good, or solidly difficult.",
}
_FRAME_HI: dict[str, str] = {
    "favourable": "इस मामले में आपका अनुभव अच्छा रहा है।",
    "afflicted": "इस मामले में आपको वास्तविक कठिनाई रही है।",
    "mixed": "यह सचमुच मिला-जुला रहा है — अच्छा और कठिन साथ-साथ, कोई एक नहीं।",
    "one_way": "यह साफ़ तौर पर एक ही तरफ़ रहा है — या तो अच्छा, या कठिन।",
}

#: verdict -> (the frame that states it, the frame that states its inverse)
_OPPOSITE: dict[str, tuple[str, str]] = {
    "favourable": ("favourable", "afflicted"),
    "afflicted": ("afflicted", "favourable"),
    "mixed": ("mixed", "one_way"),
}

#: Short, plain contrasts per rasi — enough for a reader to say which of two neighbouring
#: ascendants fits them, without quoting HPA-18's long portraits (which need the corpus mounted).
#: Descriptive temperament only; nothing here is a judgment of the person.
_SIGN_PORTRAIT: dict[int, tuple[str, str]] = {
    1: ("quick to act, impatient, leads from the front, says it before thinking it",
        "तुरंत कर्म करने वाले, अधीर, आगे बढ़कर नेतृत्व करने वाले, सोचने से पहले कह देने वाले"),
    2: ("steady, slow to change, fond of comfort and good food, hard to move once settled",
        "स्थिर, धीरे बदलने वाले, आराम और अच्छे भोजन के शौक़ीन, एक बार जम जाएँ तो टलते नहीं"),
    3: ("talkative, curious, many interests at once, restless with routine",
        "बातूनी, जिज्ञासु, एक साथ कई रुचियाँ, एकरसता से ऊबने वाले"),
    4: ("feeling runs close to the surface, attached to home and mother, remembers slights",
        "भावुक, घर और माता से गहरा लगाव, बातें मन में रख लेने वाले"),
    5: ("wants to be seen and respected, generous, proud, does not take correction easily",
        "मान-सम्मान चाहने वाले, उदार, स्वाभिमानी, टोका जाना पसंद नहीं"),
    6: ("careful, critical, notices the flaw first, useful and hard to satisfy",
        "सतर्क, आलोचक, पहले कमी दिखती है, उपयोगी और कठिनाई से संतुष्ट होने वाले"),
    7: ("weighs both sides, avoids open conflict, works through people and agreement",
        "दोनों पक्ष तौलने वाले, खुले टकराव से बचने वाले, सहमति से काम करने वाले"),
    8: ("private, intense, keeps the real reason back, forgives slowly",
        "एकांतप्रिय, गहन, असली कारण छिपाकर रखने वाले, देर से क्षमा करने वाले"),
    9: ("outspoken, hasty in speech, hates show, drawn to philosophy and hidden subjects",
        "स्पष्टवादी, बोलने में जल्दबाज़, दिखावे से चिढ़, दर्शन और गूढ़ विषयों में रुचि"),
    10: ("reserved, calculating, patient, quietly ambitious, practical before philosophical",
         "संयमित, गणनात्मक, धैर्यवान, चुपचाप महत्वाकांक्षी, दार्शनिक से पहले व्यावहारिक"),
    11: ("independent, contrary, keeps a wide circle but few close, thinks in systems",
         "स्वतंत्र, विपरीत सोच वाले, बड़ा दायरा पर कम निकट मित्र, व्यवस्था में सोचने वाले"),
    12: ("impressionable, easily moved, drifts rather than pushes, gives way and returns",
         "संवेदनशील, जल्दी प्रभावित होने वाले, टकराने के बजाय बहने वाले"),
}

_SIGN_NAMES: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_SIGN_NAMES_HI: tuple[str, ...] = (
    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन")

#: The ascendant advances ~1 degree in this many minutes of clock time at middling latitudes.
#: Only ever used to phrase "about N minutes from the cusp" as an ORDER OF MAGNITUDE — the real
#: rate swings with latitude and the rising sign, and the wording says "about" for that reason.
_DEG_PER_MINUTE = 0.25


# ── the closed answer vocabularies ──────────────────────────────────────────────────────────
# Every question below is answered by SELECTING, not by writing. Two reasons, and the second
# is the one that changed the design:
#
#   1. Prose cannot be scored. Thirty-one paragraphs about a life are thirty-one paragraphs a
#      person has to read before anything is learned, and nothing aggregates across charts.
#   2. Several of these vocabularies are the ENGINE'S OWN. The body regions are the values
#      HPA-29's sign->anatomy table emits; the trade families are the vocation words
#      HTJAH-II's tables emit; the work modes are the four H10 profession significations. So a
#      reader's selection can be compared with what the engine said DIRECTLY, code against
#      code, with no interpretation step in between — which is what makes the scoring in
#      `feedback_scoring.py` an objective measurement rather than a reading of free text.
#
# Free text stays available on every question as a supplement (`allow_free_text`), never as
# the answer itself.

#: value -> (english, hindi). Body regions, the vocabulary HPA-29's own anatomy table speaks.
BODY_REGIONS: dict[str, tuple[str, str]] = {
    "head": ("head, brain", "सिर, मस्तिष्क"),
    "eyes": ("eyes, sight", "आँखें, दृष्टि"),
    "ears": ("ears, hearing", "कान, श्रवण"),
    "throat_neck": ("throat, neck, thyroid, voice", "गला, गर्दन, थायरॉइड, आवाज़"),
    "teeth_jaw": ("teeth, jaw", "दाँत, जबड़ा"),
    "chest_lungs": ("chest, lungs, breathing", "छाती, फेफड़े, साँस"),
    "heart": ("heart, blood pressure", "हृदय, रक्तचाप"),
    "stomach": ("stomach, digestion, bowels", "पेट, पाचन, आँतें"),
    "liver": ("liver, bile", "यकृत, पित्त"),
    "kidney_urinary": ("kidneys, urinary system", "गुर्दे, मूत्र-तंत्र"),
    "reproductive": ("reproductive system", "प्रजनन-तंत्र"),
    "skin": ("skin", "त्वचा"),
    "joints": ("joints, arthritis", "जोड़, गठिया"),
    "back_spine": ("back, spine", "पीठ, रीढ़"),
    "nerves": ("nerves, sleep, anxiety", "स्नायु, नींद, चिंता"),
    "blood_sugar": ("blood sugar, metabolism", "रक्त-शर्करा, चयापचय"),
    "legs_feet": ("legs, feet", "पैर, तलवे"),
    "none": ("nothing recurring", "कुछ भी बार-बार नहीं"),
}

#: value -> (english, hindi). Trade families, drawn from Raman's own vocation vocabulary so a
#: reader's working life can be matched against the three career frames without paraphrase.
TRADE_FAMILIES: dict[str, tuple[str, str]] = {
    "metals_machinery": ("metals, machinery, engineering", "धातु, मशीन, इंजीनियरिंग"),
    "construction": ("construction, buildings, land", "निर्माण, भवन, भूमि"),
    "fire_heat": ("fire or heat trades, chemicals", "आग/गर्मी वाले काम, रसायन"),
    "military_police": ("military, police, security", "सेना, पुलिस, सुरक्षा"),
    "medicine_surgery": ("medicine, surgery, pharmacy", "चिकित्सा, सर्जरी, दवा"),
    "transport": ("driving, transport, logistics", "ड्राइविंग, परिवहन"),
    "writing_media": ("writing, journalism, media", "लेखन, पत्रकारिता, मीडिया"),
    "maths_accounts": ("mathematics, accounts, analysis", "गणित, लेखा, विश्लेषण"),
    "teaching": ("teaching, research", "अध्यापन, शोध"),
    "astrology_occult": ("astrology, the occult, priestcraft", "ज्योतिष, गूढ़ विद्या, पौरोहित्य"),
    "design_art": ("design, art, music, performance", "डिज़ाइन, कला, संगीत, प्रदर्शन"),
    "law": ("law, courts", "क़ानून, न्यायालय"),
    "counselling": ("counselling, advisory work", "परामर्श, सलाहकार कार्य"),
    "banking_finance": ("banking, finance, insurance", "बैंकिंग, वित्त, बीमा"),
    "religious": ("religious or charitable work", "धार्मिक या सेवा कार्य"),
    "agriculture": ("agriculture, horticulture", "कृषि, बाग़वानी"),
    "textiles_luxury": ("textiles, jewellery, luxury goods", "वस्त्र, आभूषण, विलासिता"),
    "trade_retail": ("trade, retail, buying and selling", "व्यापार, दुकानदारी"),
    "none": ("none of these", "इनमें से कोई नहीं"),
}

#: value -> (english, hindi). How a person earns. These four map onto the H10 profession
#: significations the engine already judges separately, which is why they are asked separately.
WORK_MODES: dict[str, tuple[str, str]] = {
    "salary_government": ("salaried, government or public body",
                          "वेतनभोगी, सरकारी या सार्वजनिक संस्था"),
    "salary_private": ("salaried, private employer", "वेतनभोगी, निजी नियोक्ता"),
    "own_business": ("own business or firm", "अपना व्यवसाय या फर्म"),
    "trade": ("trade, buying and selling", "व्यापार, ख़रीद-बिक्री"),
    "commission": ("commission or brokerage", "कमीशन या दलाली"),
    "professional_practice": ("professional practice of my own",
                              "अपनी पेशेवर प्रैक्टिस"),
    "farming": ("farming or land", "खेती या भूमि"),
    "manual": ("manual or service work", "श्रम या सेवा कार्य"),
    "not_earning": ("not earning at present", "इस समय कोई आय नहीं"),
}

#: value -> (english, hindi). Life-event categories for the dated spine. Each maps to the house
#: the engine reads that matter from, so a dated event can be checked against what the engine
#: said about that house during the period it fell in.
EVENT_KINDS: dict[str, tuple[str, str]] = {
    "move_home": ("moved home or city", "घर या शहर बदला"),
    "moved_abroad": ("moved abroad", "विदेश गए"),
    "job_start": ("started a job or business", "नौकरी या व्यवसाय शुरू किया"),
    "job_loss": ("lost a job, or a business failed", "नौकरी गई, या व्यवसाय बंद हुआ"),
    "promotion": ("promotion or public recognition", "पदोन्नति या सार्वजनिक पहचान"),
    "marriage": ("marriage or engagement", "विवाह या सगाई"),
    "separation": ("separation or divorce", "अलगाव या तलाक़"),
    "child_born": ("a child was born", "संतान का जन्म"),
    "bereavement": ("a death in the family", "परिवार में मृत्यु"),
    "own_illness": ("serious illness or surgery of my own",
                    "अपनी गंभीर बीमारी या ऑपरेशन"),
    "family_illness": ("serious illness of someone close", "किसी निकट की गंभीर बीमारी"),
    "money_gain": ("a significant financial gain", "बड़ा आर्थिक लाभ"),
    "money_loss": ("a significant financial loss or debt", "बड़ी आर्थिक हानि या कर्ज़"),
    "education": ("started or finished a course of study", "पढ़ाई शुरू या पूरी की"),
    "legal": ("a court case or legal trouble", "मुक़दमा या क़ानूनी परेशानी"),
    "accident": ("an accident", "दुर्घटना"),
    "spiritual": ("a turn toward religion or practice", "धर्म या साधना की ओर मोड़"),
    "other": ("something else", "कुछ और"),
}

#: Whether an event is a good thing, a bad thing, or genuinely neither. Used ONLY by the
#: scorer, to ask whether an event's direction agrees with the engine's verdict for its house.
#: Anything a reasonable person could file either way is `neutral` and is NOT direction-scored
#: — moving abroad and finishing a course are opportunities to some people and upheavals to
#: others, and forcing a sign on them would manufacture agreement out of the labelling.
EVENT_VALENCE: dict[str, str] = {
    "promotion": "good", "marriage": "good", "child_born": "good", "money_gain": "good",
    "job_start": "good",
    "job_loss": "bad", "separation": "bad", "bereavement": "bad", "own_illness": "bad",
    "family_illness": "bad", "money_loss": "bad", "legal": "bad", "accident": "bad",
    "move_home": "neutral", "moved_abroad": "neutral", "education": "neutral",
    "spiritual": "neutral", "other": "neutral",
}

#: Which house each event category is read from. Used ONLY by the scorer, to ask whether the
#: engine's verdict for that house was active in the period the event actually fell in. Kept
#: beside the vocabulary so the two cannot drift apart.
EVENT_HOUSE: dict[str, int] = {
    "move_home": 4, "moved_abroad": 12, "job_start": 10, "job_loss": 10, "promotion": 10,
    "marriage": 7, "separation": 7, "child_born": 5, "bereavement": 8, "own_illness": 6,
    "family_illness": 6, "money_gain": 11, "money_loss": 12, "education": 4, "legal": 6,
    "accident": 6, "spiritual": 12, "other": 0,
}


@dataclass(frozen=True)
class Q:
    """One question in the fixed banks.

    `maps_to` names the engine fact this answer is scored against. It lives here rather than in
    the scorer so the two cannot drift: a question whose comparison target is renamed fails
    loudly in one place instead of silently scoring nothing.
    """
    sid: str
    group: str
    kind: str                                   # choice | multi | scale | events | year | open
    en: str
    hi: str
    options: tuple[tuple[str, str, str], ...] = ()      # (value, english, hindi)
    hint_en: str = ""
    hint_hi: str = ""
    maps_to: str = ""


def _opts(vocab: dict[str, tuple[str, str]]) -> tuple[tuple[str, str, str], ...]:
    return tuple((k, en, hi) for k, (en, hi) in vocab.items())


_YES_NO = (("yes", "yes", "हाँ"), ("no", "no", "नहीं"), ("unknown", "I don't know", "पता नहीं"))

# ── Part A: the blind bank, all closed ──────────────────────────────────────────────────────
_PART_A: tuple[Q, ...] = (
    Q("A1", "birth_record", "choice", "Where did your birth time come from?",
      "आपका जन्म-समय कहाँ से आया?",
      (("hospital", "a hospital record", "अस्पताल का रिकॉर्ड"),
       ("certificate", "a birth certificate", "जन्म प्रमाण-पत्र"),
       ("horoscope_then", "a horoscope cast at the time", "उस समय बनी कुंडली"),
       ("family_memory", "someone's memory", "किसी की याददाश्त"),
       ("unknown", "I don't know", "पता नहीं")), maps_to="rect.source"),
    Q("A2", "birth_record", "choice", "How precise is that time?",
      "वह समय कितना सटीक है?",
      (("exact", "an exact clock reading", "घड़ी का सटीक समय"),
       ("to_5", "right to within about 5 minutes", "लगभग 5 मिनट तक सही"),
       ("to_15", "right to within about 15 minutes", "लगभग 15 मिनट तक सही"),
       ("round_hour", "a round number — the hour or the half hour",
        "गोल समय — घंटा या आधा घंटा"),
       ("part_of_day", "only a part of the day", "केवल दिन का एक पहर"),
       ("unknown", "I don't know", "पता नहीं")), maps_to="rect.precision"),
    Q("A3", "birth_record", "choice",
      "Has an astrologer already changed or corrected this time?",
      "क्या किसी ज्योतिषी ने यह समय पहले बदला या शोधित किया है?", _YES_NO,
      maps_to="rect.already_rectified"),

    Q("A4", "health", "choice", "How many times have you been admitted to hospital?",
      "आप कितनी बार अस्पताल में भर्ती हुए हैं?",
      (("none", "never", "कभी नहीं"), ("one", "once", "एक बार"),
       ("two_three", "two or three times", "दो या तीन बार"),
       ("four_plus", "four or more", "चार या अधिक")), maps_to="health.hospitalisations"),
    Q("A5", "health", "choice", "How many surgeries have you had?",
      "आपके कितने ऑपरेशन हुए हैं?",
      (("none", "none", "कोई नहीं"), ("one", "one", "एक"),
       ("two_plus", "two or more", "दो या अधिक")), maps_to="health.surgeries"),
    Q("A6", "health", "multi",
      "Which parts of your body give you recurring trouble?",
      "शरीर के कौन-से हिस्से बार-बार परेशान करते हैं?", _opts(BODY_REGIONS),
      "Choose any that apply, or the last option if nothing troubles you regularly.",
      "जितने लागू हों चुनें, या यदि कुछ भी नियमित रूप से परेशान नहीं करता तो अंतिम विकल्प।",
      maps_to="medical.regions"),
    Q("A7", "health", "choice", "How was your health as a small child?",
      "छोटी उम्र में आपका स्वास्थ्य कैसा था?",
      (("sickly", "sickly — often ill", "कमज़ोर — अक्सर बीमार"),
       ("average", "about average", "सामान्य"),
       ("robust", "robust — rarely ill", "मज़बूत — कम बीमार"),
       ("unknown", "I don't know", "पता नहीं")), maps_to="arishta.balarishta"),
    Q("A8", "health", "choice", "Was there danger to your life before the age of eight?",
      "आठ वर्ष की आयु से पहले जान का कोई ख़तरा था?", _YES_NO,
      maps_to="arishta.balarishta"),
    Q("A9", "health", "choice", "How long did your grandparents live, on average?",
      "आपके दादा-दादी / नाना-नानी औसतन कितने वर्ष जिए?",
      (("under60", "under 60", "60 से कम"), ("60_70", "60 to 70", "60 से 70"),
       ("70_80", "70 to 80", "70 से 80"), ("80_90", "80 to 90", "80 से 90"),
       ("over90", "over 90", "90 से अधिक"),
       ("mixed", "very mixed", "बहुत भिन्न"),
       ("unknown", "I don't know", "पता नहीं")), maps_to="longevity.family"),

    Q("A10", "family", "choice", "Your relationship with your father:",
      "पिता से आपका संबंध:",
      (("close", "close and supportive", "निकट और सहयोगी"),
       ("distant", "distant but not hostile", "दूर, पर वैमनस्य नहीं"),
       ("conflicted", "conflicted", "मतभेदपूर्ण"),
       ("absent", "absent for long stretches", "लंबे समय अनुपस्थित"),
       ("died_early", "he died while I was young", "मेरे बचपन में उनकी मृत्यु हुई"),
       ("na", "does not apply", "लागू नहीं")), maps_to="h9.father"),
    Q("A11", "family", "choice", "Your father's fortunes during your childhood:",
      "आपके बचपन में पिता की आर्थिक स्थिति:",
      (("prospered", "prospered", "समृद्ध हुई"), ("steady", "steady", "स्थिर रही"),
       ("reversal", "suffered a reversal", "बड़ा नुक़सान हुआ"),
       ("unknown", "I don't know", "पता नहीं")), maps_to="h9.father"),
    Q("A12", "family", "choice", "Your relationship with your mother:",
      "माता से आपका संबंध:",
      (("close", "close and supportive", "निकट और सहयोगी"),
       ("distant", "distant but not hostile", "दूर, पर वैमनस्य नहीं"),
       ("conflicted", "conflicted", "मतभेदपूर्ण"),
       ("absent", "absent for long stretches", "लंबे समय अनुपस्थित"),
       ("died_early", "she died while I was young", "मेरे बचपन में उनकी मृत्यु हुई"),
       ("na", "does not apply", "लागू नहीं")), maps_to="h4.mother"),
    Q("A13", "family", "choice", "Your brothers and sisters:",
      "आपके भाई-बहन:",
      (("none", "I have none", "कोई नहीं"),
       ("close", "close to them", "उनसे निकट"),
       ("distant", "distant from them", "उनसे दूर"),
       ("conflicted", "in conflict with them", "उनसे मतभेद"),
       ("lost", "I have lost one", "एक की मृत्यु हो चुकी")), maps_to="h3.siblings"),

    Q("A14", "education", "choice", "Your highest completed education:",
      "आपकी उच्चतम पूर्ण शिक्षा:",
      (("none", "no formal schooling", "औपचारिक शिक्षा नहीं"),
       ("school", "school", "विद्यालय"),
       ("higher_secondary", "higher secondary", "उच्चतर माध्यमिक"),
       ("graduate", "graduate", "स्नातक"),
       ("postgraduate", "postgraduate", "स्नातकोत्तर"),
       ("doctorate", "doctorate", "पीएच.डी.")), maps_to="h9.higher_learning"),
    Q("A15", "education", "choice", "Was your education interrupted?",
      "क्या आपकी पढ़ाई बीच में रुकी?",
      (("no", "no", "नहीं"), ("brief", "briefly", "थोड़े समय के लिए"),
       ("serious", "seriously", "गंभीर रूप से")), maps_to="h4.education"),

    Q("A16", "work", "multi", "How do you earn? Choose everything that applies.",
      "आप कैसे कमाते हैं? जितने लागू हों चुनें।", _opts(WORK_MODES), "", "",
      maps_to="h10.modes"),
    Q("A17", "work", "choice",
      "Which has gone better for you — working under an authority, or working for yourself?",
      "आपके लिए कौन बेहतर रहा — किसी के अधीन काम, या अपना काम?",
      (("under_authority", "under an employer, government or senior",
        "नियोक्ता, सरकार या वरिष्ठ के अधीन"),
       ("own", "for myself", "अपने लिए"),
       ("both_equal", "about the same", "दोनों बराबर"),
       ("untested", "I have only tried one", "मैंने केवल एक ही आज़माया है")),
      maps_to="h10.authority_vs_trade"),
    Q("A18", "work", "multi",
      "Which kinds of work have you actually done, or been strongly drawn to?",
      "आपने वास्तव में किस तरह का काम किया है, या किसकी ओर प्रबल आकर्षण रहा है?",
      _opts(TRADE_FAMILIES),
      "Include work you only tried briefly, and attractions that went nowhere.",
      "थोड़े समय किया हुआ काम और अधूरे आकर्षण भी शामिल करें।",
      maps_to="career.trades"),
    Q("A19", "work", "choice", "Recognition compared with the work you actually did:",
      "आपके वास्तविक काम की तुलना में मिली पहचान:",
      (("above", "more than it deserved", "काम से ज़्यादा"),
       ("about_right", "about right", "उचित"),
       ("short", "less than it deserved", "काम से कम"),
       ("na", "does not apply", "लागू नहीं")), maps_to="h10.status_honour"),

    Q("A20", "money", "choice", "Money earned far from your birthplace, or abroad:",
      "जन्मस्थान से दूर या विदेश से अर्जित धन:",
      (("none", "none", "कोई नहीं"), ("some", "some of my income", "आय का कुछ हिस्सा"),
       ("most", "most of my income", "आय का अधिकांश")), maps_to="h12.foreign_residence"),
    Q("A21", "money", "choice",
      "Speculation, betting, lottery or shares — how has it gone overall?",
      "सट्टा, लॉटरी या शेयर — कुल मिलाकर कैसा रहा?",
      (("never", "I have never done it", "मैंने कभी नहीं किया"),
       ("net_loss", "a net loss", "कुल मिलाकर हानि"),
       ("about_even", "about even", "बराबर"),
       ("net_gain", "a net gain", "कुल मिलाकर लाभ")), maps_to="h5.poorvapunya"),
    Q("A22", "money", "choice", "Inheritance, insurance, or an unexpected windfall:",
      "विरासत, बीमा, या अप्रत्याशित धन:",
      (("none", "none", "कोई नहीं"), ("small", "something small", "छोटी राशि"),
       ("significant", "something significant", "बड़ी राशि")), maps_to="h8.legacies"),
    Q("A23", "money", "choice", "Debt:",
      "कर्ज़:",
      (("none", "none", "कोई नहीं"),
       ("manageable", "some, manageable", "कुछ, संभाला जा सकता है"),
       ("serious_past", "serious trouble in the past", "पहले गंभीर संकट रहा"),
       ("serious_now", "serious trouble now", "अभी गंभीर संकट")), maps_to="h6.debts"),

    Q("A24", "marriage", "choice", "Your marital status:",
      "आपकी वैवाहिक स्थिति:",
      (("never_married", "never married", "अविवाहित"),
       ("engaged", "engaged, not yet married", "सगाई हुई, विवाह नहीं"),
       ("married", "married", "विवाहित"),
       ("separated", "separated", "अलग"),
       ("divorced", "divorced", "तलाक़शुदा"),
       ("widowed", "widowed", "विधुर/विधवा")), maps_to="marriage.status"),
    Q("A25", "marriage", "year", "If you married, in which year?",
      "यदि विवाह हुआ, तो किस वर्ष?", (), "", "", maps_to="marriage.year"),
    Q("A26", "marriage", "choice",
      "By your family's usual pattern, was the marriage early or late?",
      "आपके परिवार के सामान्य ढर्रे के हिसाब से विवाह जल्दी हुआ या देर से?",
      (("early", "early", "जल्दी"), ("on_time", "about usual", "सामान्य समय पर"),
       ("late", "late", "देर से"), ("very_late", "much later than usual", "बहुत देर से"),
       ("na", "does not apply", "लागू नहीं")), maps_to="marriage.delay"),
    Q("A27", "marriage", "choice", "The marriage or your closest partnership has been:",
      "विवाह या आपकी निकटतम साझेदारी रही है:",
      (("happy", "happy", "सुखी"), ("mixed", "mixed", "मिली-जुली"),
       ("strained", "strained", "तनावपूर्ण"),
       ("ended", "it ended", "समाप्त हो गई"),
       ("na", "does not apply", "लागू नहीं")), maps_to="h7.marital_happiness"),
    Q("A28", "children", "choice", "Children:",
      "संतान:",
      (("none", "none", "कोई नहीं"), ("one", "one", "एक"), ("two", "two", "दो"),
       ("three_plus", "three or more", "तीन या अधिक")), maps_to="h5.children"),
    Q("A29", "children", "choice", "Difficulty conceiving, or the loss of a child:",
      "संतान होने में कठिनाई, या संतान की हानि:",
      (("no", "no", "नहीं"), ("yes", "yes", "हाँ"),
       ("na", "does not apply", "लागू नहीं")), maps_to="h5.children"),

    Q("A30", "mind", "multi",
      "Which of these describe you? Choose as many as fit.",
      "इनमें से कौन आप पर लागू होते हैं? जितने ठीक बैठें चुनें।",
      (("outspoken", "outspoken, says it plainly", "स्पष्टवादी, सीधा कहने वाला"),
       ("reserved", "reserved, keeps things back", "संयमित, बात रखने वाला"),
       ("quick_tempered", "quick-tempered", "जल्दी क्रोधित"),
       ("patient", "patient", "धैर्यवान"),
       ("cautious", "cautious", "सतर्क"), ("bold", "bold", "साहसी"),
       ("solitary", "happiest alone", "एकांत में प्रसन्न"),
       ("sociable", "happiest among people", "लोगों के बीच प्रसन्न"),
       ("practical", "practical", "व्यावहारिक"),
       ("philosophical", "philosophical", "दार्शनिक")), maps_to="psych.temperament"),
    Q("A31", "mind", "choice",
      "Have you had a period of depression, severe anxiety, or treatment for the mind?",
      "क्या आपको अवसाद, गंभीर चिंता, या मानसिक उपचार का कोई दौर रहा है?",
      (("no", "no", "नहीं"), ("brief", "yes, briefly", "हाँ, थोड़े समय"),
       ("extended", "yes, for an extended period", "हाँ, लंबे समय"),
       ("prefer_not", "I would rather not say", "मैं नहीं बताना चाहूँगा/चाहूँगी")),
      maps_to="psych.mind_screen"),
    Q("A32", "mind", "choice", "Religion, philosophy, the occult, or solitary practice:",
      "धर्म, दर्शन, गूढ़ विद्या, या एकांत साधना:",
      (("none", "no interest", "कोई रुचि नहीं"), ("mild", "mild interest", "थोड़ी रुचि"),
       ("strong", "strong interest", "प्रबल रुचि"),
       ("central", "central to my life", "मेरे जीवन का केंद्र")), maps_to="h12.moksha"),
    Q("A33", "mind", "choice", "Time lived away from your birthplace:",
      "जन्मस्थान से दूर बिताया समय:",
      (("never", "never", "कभी नहीं"), ("under1", "under a year", "एक वर्ष से कम"),
       ("1_5", "one to five years", "एक से पाँच वर्ष"),
       ("over5", "more than five years", "पाँच वर्ष से अधिक"),
       ("abroad", "abroad", "विदेश में")), maps_to="h12.foreign_residence"),
    Q("A34", "mind", "choice",
      "Time in a hostel, institution, hospital, or any kind of confinement:",
      "छात्रावास, संस्था, अस्पताल, या किसी बंदिश में बिताया समय:",
      (("never", "never", "कभी नहीं"), ("brief", "briefly", "थोड़े समय"),
       ("extended", "for an extended period", "लंबे समय")), maps_to="h12.incarceration"),

    Q("A35", "turning_points", "events",
      "The turning points of your life so far. Add a row for each: the year, the month if you "
      "remember it, and what kind of event it was.",
      "अब तक के जीवन के निर्णायक मोड़। हर एक के लिए एक पंक्ति जोड़ें: वर्ष, महीना (यदि याद हो), "
      "और वह किस तरह की घटना थी।",
      _opts(EVENT_KINDS),
      "Five to eight is plenty. This is the most valuable answer here — fill it in before you "
      "read the rest of the report, and do not go back and change it afterwards.",
      "पाँच से आठ पर्याप्त हैं। यह यहाँ का सबसे मूल्यवान उत्तर है — बाक़ी फलादेश पढ़ने से पहले भरें, "
      "और बाद में बदलें नहीं।", maps_to="spine.events"),
    Q("A36", "turning_points", "choice",
      "Compared with the six years before it, the time since the middle of 2023 has been:",
      "उससे पहले के छह वर्षों की तुलना में, मध्य-2023 के बाद का समय रहा है:",
      (("much_better", "much better", "बहुत बेहतर"), ("better", "better", "बेहतर"),
       ("same", "about the same", "लगभग वैसा ही"), ("worse", "worse", "ख़राब"),
       ("much_worse", "much worse", "बहुत ख़राब")), maps_to="spine.recent"),
)

_PART_A_GROUPS: dict[str, tuple[str, str]] = {
    "birth_record": ("The birth record", "जन्म का विवरण"),
    "health": ("Body and health", "शरीर और स्वास्थ्य"),
    "family": ("Parents and siblings", "माता-पिता और भाई-बहन"),
    "education": ("Education", "शिक्षा"),
    "work": ("Work", "काम"),
    "money": ("Money", "धन"),
    "marriage": ("Marriage and partnership", "विवाह और साझेदारी"),
    "children": ("Children", "संतान"),
    "mind": ("Mind and temperament", "मन और स्वभाव"),
    "turning_points": ("The turning points", "जीवन के मोड़"),
}

# ── Part B: rectification, all closed ───────────────────────────────────────────────────────
_PART_B_FIXED: tuple[Q, ...] = (
    Q("B2", "rectification", "choice", "Your build:", "आपकी शारीरिक बनावट:",
      (("lean_tall", "lean and tall-ish", "दुबला और कुछ लंबा"),
       ("lean_short", "lean and short", "दुबला और नाटा"),
       ("medium", "medium", "मध्यम"),
       ("solid_heavy", "solid, puts on weight easily", "भारी, वज़न जल्दी बढ़ता है")),
      maps_to="rect.build"),
    Q("B3", "rectification", "choice", "People usually guess your age as:",
      "लोग आमतौर पर आपकी उम्र आँकते हैं:",
      (("older", "older than I am", "मेरी उम्र से ज़्यादा"),
       ("right", "about right", "लगभग सही"),
       ("younger", "younger than I am", "मेरी उम्र से कम")), maps_to="rect.apparent_age"),
    Q("B4", "rectification", "choice", "Your birth order:", "जन्म-क्रम:",
      (("only", "only child", "इकलौता"), ("eldest", "eldest", "सबसे बड़ा"),
       ("middle", "middle", "मंझला"), ("youngest", "youngest", "सबसे छोटा")),
      maps_to="rect.birth_order"),
    Q("B5", "rectification", "choice", "You were born:", "आपका जन्म हुआ:",
      (("hospital", "in a hospital", "अस्पताल में"), ("home", "at home", "घर पर"),
       ("unknown", "I don't know", "पता नहीं")), maps_to="rect.birth_place"),
    Q("B6", "rectification", "events",
      "The events a birth time is actually corrected against. Give the year and, where you "
      "can, the month.",
      "जिन घटनाओं से जन्म-समय शोधित होता है। वर्ष और यदि संभव हो तो महीना बताएँ।",
      (("father_death", "father's death or major illness",
        "पिता की मृत्यु या गंभीर बीमारी"),
       ("mother_death", "mother's death or major illness",
        "माता की मृत्यु या गंभीर बीमारी"),
       ("marriage", "marriage", "विवाह"),
       ("first_job", "first job", "पहली नौकरी"),
       ("own_surgery", "a surgery of my own", "अपना ऑपरेशन"),
       ("child_born", "the birth of a first child", "पहली संतान का जन्म")),
      "Exact months matter more here than anywhere else on the form.",
      "यहाँ सटीक महीने बाक़ी फ़ॉर्म से ज़्यादा मायने रखते हैं।", maps_to="rect.anchors"),
)

# ── Part D: after the reading, all closed ───────────────────────────────────────────────────
# D1/D2/D3/D5 are multi-selects over the report's OWN section list, which is built at render
# time from SECTION_CONTRACT — so "which chapters got me wrong" comes back as section ids the
# scorer can count per chapter, and a chapter that is wrong for many readers is named rather
# than buried in prose.
_PART_D: tuple[Q, ...] = (
    Q("D1", "reaction", "multi",
      "Which chapters said something plainly WRONG about your life?",
      "किन अध्यायों ने आपके जीवन के बारे में साफ़ ग़लत बात कही?", (), "", "",
      maps_to="reaction.wrong"),
    Q("D2", "reaction", "multi",
      "Which chapters said something right that could NOT have been guessed about anyone?",
      "किन अध्यायों ने ऐसा सही कहा जो किसी के भी बारे में अंदाज़े से नहीं कहा जा सकता था?",
      (), "", "", maps_to="reaction.specific"),
    Q("D3", "reaction", "multi",
      "Which chapters felt true of you AND of most people you know?",
      "कौन-से अध्याय आप पर और आपके अधिकांश परिचितों पर भी सही लगे?", (), "", "",
      maps_to="reaction.barnum"),
    Q("D4", "reaction", "multi",
      "Which chapters did you skip, or not understand?",
      "कौन-से अध्याय आपने छोड़ दिए, या समझ नहीं आए?", (), "", "",
      maps_to="reaction.skipped"),
    Q("D5", "reaction", "choice", "Was anything upsetting or frightening?",
      "क्या कुछ परेशान करने वाला या डरावना था?",
      (("no", "no", "नहीं"), ("mildly", "mildly", "थोड़ा"),
       ("yes", "yes", "हाँ")), maps_to="reaction.harm"),
    Q("D6", "reaction", "scale", "Overall, how well did this reading match your life?",
      "कुल मिलाकर, यह फलादेश आपके जीवन से कितना मेल खाता है?", (), "", "",
      maps_to="reaction.overall"),
    Q("D7", "reaction", "choice", "Would this have been worth paying for?",
      "क्या यह पैसे देने लायक़ होता?",
      (("no", "no", "नहीं"), ("maybe", "maybe", "शायद"),
       ("yes", "yes", "हाँ")), maps_to="reaction.worth_paying"),
    Q("D8", "reaction", "open", "Anything else you want to say?",
      "और कुछ कहना चाहेंगे?", (), "", "", maps_to=""),
)

#: The chapters a reader actually experiences, as a closed vocabulary for Part D. Deliberately
#: NOT the 56 rows of SECTION_CONTRACT: a person cannot usefully say which of fifty-six sections
#: was wrong, and a list that long is not answered at all. Values are real section ids, so a
#: count of "wrong" answers per chapter points straight at the code that produced it.
REPORT_CHAPTERS: dict[str, tuple[str, str]] = {
    "plain_reading": ("The plain-English reading", "सरल भाषा का फलादेश"),
    "houses": ("The twelve matters, house by house", "बारह भाव, एक-एक करके"),
    "longevity": ("Longevity and the span", "आयु और जीवन-काल"),
    "health_readout": ("Health and vulnerability", "स्वास्थ्य और दुर्बलता"),
    "medical": ("The medical read — body areas", "चिकित्सा पाठ — शरीर के अंग"),
    "marriage": ("Marriage", "विवाह"),
    "children": ("Children", "संतान"),
    "profession": ("Profession and career", "व्यवसाय और करियर"),
    "wealth": ("Wealth and money", "धन और सम्पत्ति"),
    "psych": ("Temperament and the inner portrait", "स्वभाव और आंतरिक चित्र"),
    "aptitude": ("Aptitude and working style", "योग्यता और कार्यशैली"),
    "timeline": ("The dasha timeline — when things happen", "दशा-काल — कब क्या होता है"),
    "gochara": ("Transits", "गोचर"),
    "divisional": ("The divisional charts", "वर्ग कुंडलियाँ"),
    "karmic": ("Soul, karma and destiny", "आत्मा, कर्म और भाग्य"),
    "nichod": ("The Nichod — the distilled essence", "निचोड़ — सार"),
}

# ── builders ────────────────────────────────────────────────────────────────────────────────

def _sign_name(sign: int, lang: Lang) -> str:
    table = _SIGN_NAMES_HI if lang == "hi" else _SIGN_NAMES
    return table[sign - 1] if 1 <= sign <= 12 else f"sign {sign}"


#: The seed's field precision, chosen to match `_chart_key` in the report routes EXACTLY.
#: Scoring recasts a chart from its stored `chart_key`, which keeps latitude and longitude to
#: four places and the offset to two. Seeding on anything finer — the ascendant longitude was
#: in here, to six places — means the recast produces a DIFFERENT shuffle from the one the
#: reader answered, and every stored answer silently inverts. The seed must therefore depend
#: only on what the key round-trips.
_SEED_FIELDS: tuple[tuple[str, str], ...] = (
    ("year", "04d"), ("month", "02d"), ("day", "02d"), ("hour", "02d"), ("minute", "02d"),
    ("tz_offset", "+.2f"), ("latitude", ".4f"), ("longitude", ".4f"),
)


def _seed(report: dict) -> str:
    """A stable per-chart seed.

    Built from the birth fields only — the name is left out, so two readings of the same
    nativity get the same instrument — at the precision `chart_key` preserves, so a chart
    recast from a stored key reproduces the shuffle the reader actually saw.

    Hashed with sha256 rather than `hash()`: the interpreter's string hash is salted per
    process, so a hash()-based shuffle would differ between the request that asked the
    questions and the request that scores them.
    """
    b = report.get("birth") or {}
    parts = []
    for field, fmt in _SEED_FIELDS:
        v = b.get(field)
        try:
            parts.append(format(float(v) if "f" in fmt else int(v), fmt))
        except (TypeError, ValueError):
            parts.append("")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _flip(seed: str, qid: str) -> bool:
    """Whether this item presents the chart's own claim SECOND. Deterministic per (chart, item),
    so the same reader reloading the page sees the same order and a stored answer keeps meaning
    what it meant — but no reader can learn a global rule like "it is always the first one"."""
    h = hashlib.sha256(f"{seed}:{qid}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 2 == 1


def _choice_rows(report: dict, max_choices: int) -> list[dict[str, Any]]:
    """The chart's own distinctive readings, rarest first, at most two per house.

    Rarity is `band_share` — the fraction of the 16,450-chart population carrying this exact
    reading on this exact signification. Ordering by it rather than by digest position is the
    whole point: the digest ranks by how loudly the engine speaks, and the engine speaks loudest
    where every chart agrees. A 72%-share reading confirmed tells you nothing about a person.
    """
    rows: list[dict[str, Any]] = []
    for house_key, block in (report.get("calibration") or {}).items():
        try:
            house = int(house_key)
        except (TypeError, ValueError):
            continue
        for e in block.get("entries") or ():
            sig = e.get("signification", "")
            verdict = e.get("verdict", "")
            if sig in EXCLUDED_SIGNIFICATIONS or sig not in TOPIC:
                continue
            if verdict not in _OPPOSITE:
                continue                            # neutral asserts no direction to test
            rows.append({
                "house": house,
                "signification": sig,
                "verdict": verdict,
                "degree": e.get("degree", ""),
                "band_share": float(e.get("band_share") or 1.0),
                "favourability_percentile": e.get("favourability_percentile"),
                "rarity": e.get("rarity", ""),
                "inverted_warning": bool(e.get("inverted_warning")),
            })
    rows.sort(key=lambda r: (r["band_share"], r["house"], r["signification"]))

    picked: list[dict[str, Any]] = []
    per_house: dict[int, int] = {}
    for r in rows:
        if len(picked) >= max_choices:
            break
        if per_house.get(r["house"], 0) >= 2:       # spread across life areas, not one house
            continue
        per_house[r["house"]] = per_house.get(r["house"], 0) + 1
        picked.append(r)
    return picked


def _boundary_rows(report: dict) -> list[dict[str, str]]:
    """Every Mahadasha change inside the report's own window, as calendar dates.

    These are what a freely-given list of turning points (A35) is compared against. They are
    shown only in Part C, never beside A35 — a reader who sees the dates first will find events
    near them, which is the failure mode the whole instrument exists to avoid.
    """
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    prev_maha: Optional[str] = None
    for p in report.get("timeline") or ():
        maha = str(p.get("maha", ""))
        start = p.get("start_jd")
        if not maha or start is None:
            continue
        if prev_maha is not None and maha != prev_maha:
            row = (maha, _jd_to_date(float(start)))
            if row not in seen:
                seen.add(row)
                out.append({"date": row[1], "maha": maha})
        prev_maha = maha
    return out


def _rectification(report: dict) -> Optional[dict[str, Any]]:
    """How close the ascendant sits to its own cusp, and the two portraits that settle it.

    A round birth time is usually a rounded one, and an ascendant a few minutes from a cusp
    means the whole chart is a coin-flip. Quoting the gap in minutes of clock time is an
    approximation (the rate depends on latitude and rising sign), so the wording says "about".
    """
    chart = report.get("chart") or {}
    asc_lon = chart.get("asc_lon")
    asc_sign = chart.get("asc_sign")
    if asc_lon is None or not isinstance(asc_sign, int) or not 1 <= asc_sign <= 12:
        return None
    deg_in_sign = float(asc_lon) % 30.0
    to_next = 30.0 - deg_in_sign
    from_prev = deg_in_sign
    if to_next <= from_prev:
        neighbour = asc_sign % 12 + 1
        gap_deg, direction = to_next, "later"
    else:
        neighbour = (asc_sign - 2) % 12 + 1
        gap_deg, direction = from_prev, "earlier"
    minutes = int(round(gap_deg / _DEG_PER_MINUTE))

    note_en = (f"Your ascendant stands at {deg_in_sign:.1f}\u00b0 of "
               f"{_sign_name(asc_sign, 'en')} — about {minutes} minutes of clock time "
               f"{'before' if direction == 'later' else 'after'} the "
               f"{_sign_name(neighbour, 'en')} cusp. An error of that many minutes changes "
               f"every house in the chart, not part of it.")
    note_hi = (f"आपका लग्न {_sign_name(asc_sign, 'hi')} में {deg_in_sign:.1f}\u00b0 पर है — "
               f"{_sign_name(neighbour, 'hi')} की सीमा से लगभग {minutes} मिनट "
               f"{'पहले' if direction == 'later' else 'बाद'}। इतने मिनट की गड़बड़ी भी पूरी कुंडली "
               f"बदल देती है, उसका कोई हिस्सा नहीं।")
    return {
        "asc_sign": asc_sign,
        "asc_sign_name_en": _sign_name(asc_sign, "en"),
        "asc_sign_name_hi": _sign_name(asc_sign, "hi"),
        "neighbour_sign": neighbour,
        "neighbour_sign_name_en": _sign_name(neighbour, "en"),
        "neighbour_sign_name_hi": _sign_name(neighbour, "hi"),
        "degrees_into_sign": round(deg_in_sign, 2),
        "gap_degrees": round(gap_deg, 2), "approx_gap_minutes": minutes,
        "cusp_direction": direction,
        "note_en": note_en, "note_hi": note_hi,
        "question_en": "Which of these two fits you better?",
        "question_hi": "इनमें से कौन-सा आप पर ज़्यादा ठीक बैठता है?",
        "portrait_here_en": _SIGN_PORTRAIT[asc_sign][0],
        "portrait_here_hi": _SIGN_PORTRAIT[asc_sign][1],
        "portrait_neighbour_en": _SIGN_PORTRAIT[neighbour][0],
        "portrait_neighbour_hi": _SIGN_PORTRAIT[neighbour][1],
        #: A birth time this close to a cusp is a coin-flip dressed as a reading. The page
        #: raises the rectification part to the top of the section when this is true.
        "tight": minutes <= 30,
    }


def _q(qid: str, part: str, group: str, group_label_en: str, group_label_hi: str, kind: str,
       text_en: str, text_hi: str, hint_en: str = "", hint_hi: str = "",
       options: tuple[dict[str, str], ...] = (),
       confidence: bool = False, allow_free_text: bool = True,
       maps_to: str = "") -> dict[str, Any]:
    """One question, in BOTH languages, with its options as CODES.

    Two things are load-bearing here. Options carry a stable `value` code and the display text
    beside it, so an answer means the same thing whichever language it was given in and can be
    compared with the engine's own output without parsing prose. And `maps_to` names the engine
    fact this answer is scored against, travelling with the question rather than living in a
    parallel table in the scorer, where the two would drift.

    There is no `text` key on purpose: a consumer must choose a language rather than silently
    getting whichever one the request happened to default to.
    """
    return {"qid": qid, "part": part, "group": group,
            "group_label_en": group_label_en, "group_label_hi": group_label_hi,
            "kind": kind, "text_en": text_en, "text_hi": text_hi,
            "hint_en": hint_en, "hint_hi": hint_hi, "options": list(options),
            "confidence": confidence, "allow_free_text": allow_free_text,
            "maps_to": maps_to}


def _bank_q(q: "Q", part: str) -> dict[str, Any]:
    """A fixed-bank row -> a question dict."""
    label = _PART_A_GROUPS.get(q.group) or ("Checking the birth time", "जन्म-समय की जाँच") \
        if part in ("A", "B") else ("After the reading", "फलादेश पढ़ने के बाद")
    opts = tuple({"value": v, "text_en": en, "text_hi": hi} for v, en, hi in q.options)
    return _q(f"inst.{INSTRUMENT_VERSION}.{q.sid}", part, q.group, label[0], label[1],
              q.kind, q.en, q.hi, q.hint_en, q.hint_hi, opts, maps_to=q.maps_to)


def _claim(row: dict[str, Any], which: str, lang: Lang) -> str:
    """One side of a forced choice. The topic sits in the question stem; this is the predicate,
    so the two options differ ONLY in what they claim and the reader compares the claim itself."""
    del row                                  # the topic is carried by the stem, not the option
    return (_FRAME_HI if lang == "hi" else _FRAME_EN)[which]


def _build(report: dict, lang: Lang, max_choices: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """The single builder. Returns (reader-facing payload, server-only key) so the two public
    entry points cannot drift apart — the key is derived from the same rows, in the same order,
    with the same shuffle, and is simply not attached to what ships."""
    seed = _seed(report)
    key_answers: dict[str, str] = {}
    key_meta: dict[str, Any] = {}
    inverted: list[str] = []
    chapter_opts = tuple({"value": k, "text_en": en, "text_hi": hi}
                         for k, (en, hi) in REPORT_CHAPTERS.items())

    # ── Part A ──────────────────────────────────────────────────────────────────────────
    a_questions = [_bank_q(q, "A") for q in _PART_A]

    # ── Part B ──────────────────────────────────────────────────────────────────────────
    rect = _rectification(report)
    b_label = ("Checking the birth time", "जन्म-समय की जाँच")
    b_questions: list[dict[str, Any]] = []
    if rect is not None:
        qid = f"inst.{INSTRUMENT_VERSION}.B1"
        pair = [("here", rect["portrait_here_en"], rect["portrait_here_hi"]),
                ("there", rect["portrait_neighbour_en"], rect["portrait_neighbour_hi"])]
        if _flip(seed, qid):
            pair.reverse()
        opts = tuple({"value": f"opt{i}", "text_en": en, "text_hi": hin}
                     for i, (_who, en, hin) in enumerate(pair, 1))
        b_questions.append(_q(qid, "B", "rectification", b_label[0], b_label[1], "choice",
                              rect["question_en"], rect["question_hi"],
                              rect["note_en"], rect["note_hi"], opts,
                              maps_to="rect.portrait"))
        key_answers[qid] = f"opt{[w for w, _e, _h in pair].index('here') + 1}"
        key_meta[qid] = {"kind": "rectification", "asc_sign": rect["asc_sign"],
                         "neighbour_sign": rect["neighbour_sign"],
                         "approx_gap_minutes": rect["approx_gap_minutes"]}
    b_questions += [_bank_q(q, "B") for q in _PART_B_FIXED]

    # ── Part C ──────────────────────────────────────────────────────────────────────────
    c_questions: list[dict[str, Any]] = []
    for n, row in enumerate(_choice_rows(report, max_choices), 1):
        qid = f"inst.{INSTRUMENT_VERSION}.C{n}"
        mine, theirs = _OPPOSITE[row["verdict"]]
        pair = [("mine", _claim(row, mine, "en"), _claim(row, mine, "hi")),
                ("inverse", _claim(row, theirs, "en"), _claim(row, theirs, "hi"))]
        if _flip(seed, qid):
            pair.reverse()
        opts = tuple({"value": f"opt{i}", "text_en": en, "text_hi": hin}
                     for i, (_who, en, hin) in enumerate(pair, 1))
        topic_en, topic_hi = TOPIC[row["signification"]]
        c_questions.append(_q(
            qid, "C", "forced_choice",
            "Which one is closer?", "कौन-सा ज़्यादा नज़दीक है?", "choice",
            f"{topic_en[0].upper()}{topic_en[1:]} — which is closer to your life?",
            f"{topic_hi} — इनमें से कौन-सा आपके जीवन के ज़्यादा नज़दीक है?",
            options=opts, confidence=True, maps_to="forced_choice"))
        key_answers[qid] = f"opt{[w for w, _e, _h in pair].index('mine') + 1}"
        key_meta[qid] = {"kind": "forced_choice", "house": row["house"],
                         "signification": row["signification"], "verdict": row["verdict"],
                         "degree": row["degree"], "band_share": row["band_share"],
                         "rarity": row["rarity"],
                         "favourability_percentile": row["favourability_percentile"],
                         "inverted_warning": row["inverted_warning"]}
        if row["inverted_warning"]:
            inverted.append(qid)

    boundaries = _boundary_rows(report)

    # ── Part D ──────────────────────────────────────────────────────────────────────────
    d_questions = []
    for q in _PART_D:
        row = _bank_q(q, "D")
        if q.kind == "multi" and not row["options"]:
            row["options"] = list(chapter_opts)          # the chapter list, not 56 section ids
        if q.kind == "scale":
            row["options"] = [{"value": v, "text_en": v, "text_hi": _SCALE_HI[v]}
                              for v in ANSWER_SCALE]
        d_questions.append(row)

    parts = [
        {"part": "A",
         "title_en": "Your life, in your own words",
         "title_hi": "आपका जीवन, आपके अपने शब्दों में",
         "note_en": "Nothing here mentions astrology, and nothing is being checked against a "
                    "prediction yet. Answer this part BEFORE reading the rest of the report — "
                    "once you have read what a chart says about you, you can no longer report "
                    "what you would have said on your own, and that is the only answer worth "
                    "measuring. Every question is answered by choosing, not by writing.",
         "note_hi": "यहाँ ज्योतिष का कोई ज़िक्र नहीं है, और अभी किसी भविष्यवाणी से कुछ नहीं मिलाया जा "
                    "रहा। यह भाग बाक़ी फलादेश पढ़ने से पहले भरें — एक बार पढ़ लेने के बाद आप वह नहीं बता "
                    "सकते जो आप अपनी ओर से कहते, और मापने लायक़ वही एक उत्तर है। हर प्रश्न का उत्तर "
                    "चुनकर दिया जाता है, लिखकर नहीं।",
         "questions": a_questions},
        {"part": "B",
         "title_en": "Checking the birth time",
         "title_hi": "जन्म-समय की जाँच",
         "note_en": "A round birth time is usually a rounded one. If the true time is even a "
                    "few minutes off, the rising sign can change and no part of the reading "
                    "stands.",
         "note_hi": "गोल जन्म-समय अक्सर अनुमानित होता है। यदि वास्तविक समय कुछ मिनट भी अलग है, तो "
                    "लग्न बदल सकता है और फलादेश का कोई हिस्सा नहीं टिकता।",
         "questions": b_questions},
        {"part": "C",
         "title_en": "Which one is closer?",
         "title_hi": "कौन-सा ज़्यादा नज़दीक है?",
         "note_en": "Each pair holds one statement drawn from your chart and one that is its "
                    "exact opposite, and you are not told which is which. A coin gets half of "
                    "them right — that is the point, and it is why an answer here is worth "
                    "something.",
         "note_hi": "हर जोड़ी में एक कथन आपकी कुंडली से लिया गया है और दूसरा उसका ठीक उल्टा; आपको "
                    "बताया नहीं जाएगा कि कौन-सा कौन है। सिक्का उछालने पर भी आधे सही आ जाते हैं — "
                    "इसीलिए यहाँ दिया गया उत्तर कुछ मायने रखता है।",
         "questions": c_questions},
        {"part": "D",
         "title_en": "After the reading",
         "title_hi": "फलादेश पढ़ने के बाद",
         "note_en": "This part is about the reading itself, not about the chart. Naming the "
                    "chapters that got you wrong is more useful than being kind about them.",
         "note_hi": "यह भाग फलादेश के बारे में है, कुंडली के बारे में नहीं। जिन अध्यायों ने ग़लत कहा "
                    "उन्हें नाम से बताना, उनके बारे में सँभालकर कहने से ज़्यादा उपयोगी है।",
         "questions": d_questions},
    ]

    payload = {
        "version": INSTRUMENT_VERSION,
        #: The language the caller asked for. Content is ALWAYS carried in both — the page
        #: toggles on the client without re-fetching — so this is a default hint for a
        #: consumer that renders one, never a statement that the other is absent.
        "lang": lang,
        "parts": parts,
        "boundaries": boundaries,
        "rectification": rect,
        "answer_scale": list(ANSWER_SCALE),
        "answer_scale_hi": {k: _SCALE_HI[k] for k in ANSWER_SCALE},
        "confidence_scale": list(CONFIDENCE_SCALE),
        "event_kinds": {k: {"text_en": en, "text_hi": hi}
                        for k, (en, hi) in EVENT_KINDS.items()},
        "caveat_en": "These questions calibrate the reading; they do not validate it. This "
                     "project's own measurement found no chart-specific signal against real "
                     "outcomes, so your answers measure how a faithful rendering of Raman's "
                     "method meets one real life — never a claim that it predicted it.",
        "caveat_hi": "ये प्रश्न फलादेश को कैलिब्रेट करते हैं, उसे प्रमाणित नहीं करते। इस परियोजना के "
                     "अपने मापन में वास्तविक जीवन-घटनाओं के विरुद्ध कोई कुंडली-विशिष्ट संकेत नहीं मिला, "
                     "इसलिए आपके उत्तर यह मापते हैं कि रामन की पद्धति का निष्ठापूर्ण प्रस्तुतीकरण एक "
                     "वास्तविक जीवन से कैसे मिलता है — यह दावा कभी नहीं कि उसने भविष्य बताया।",
        "counts": {"A": len(a_questions), "B": len(b_questions),
                   "C": len(c_questions), "D": len(d_questions)},
    }
    key = {"version": INSTRUMENT_VERSION, "answers": key_answers, "meta": key_meta,
           "inverted": inverted,
           "chance_rate": 0.5 if key_answers else None}
    return payload, key


def build_feedback_instrument(report: dict, *, lang: Lang = "en",
                              max_choices: int = 12) -> dict[str, Any]:
    """The reader-facing instrument for one report dict (``to_report_dict`` output).

    Deterministic for a chart, in either language, with language-independent `qid`s and option
    codes so answers given in Hindi pool with answers given in English. Carries NO indication of
    which option each forced choice was drawn from — see `instrument_key`.
    """
    lang = lang if lang in ("en", "hi") else "en"
    payload, _key = _build(report, lang, max_choices)
    return payload


def instrument_key(report: dict, *, max_choices: int = 12) -> dict[str, Any]:
    """The scoring key — SERVER-SIDE ONLY. `answers` maps each forced-choice qid to the option
    that states the chart's own reading; `meta` carries the rarity of each so a score can be
    weighted by how much information the item actually held; `inverted` names the items sitting
    on channels the atlas proved run backwards, where agreement is evidence AGAINST the method
    rather than for it.

    Never merge this into the report dict, and never send it to a client that is about to ask
    the questions.
    """
    _payload, key = _build(report, "en", max_choices)
    return key


#: An events answer is stored one row per event, `qid#n`, valued `YYYY-MM:kind` or `YYYY:kind`.
#: One row per event rather than a packed blob because the scorer reads them individually, and
#: because a single column of comma-joined dates is the kind of thing nobody ever queries again.
_EVENT_RE = __import__("re").compile(r"^(\d{4})(?:-(0[1-9]|1[0-2]))?:([a-z_]+)$")
#: A multi-select answer is stored as comma-joined codes in one row.
_MULTI_SEP = ","


def _widest_multi_answer() -> int:
    """Length of the longest answer this instrument can legally produce.

    A multi-select ships as its codes comma-joined into ONE row, so the widest closed
    vocabulary sets the bound — today `TRADE_FAMILIES`, whose nineteen codes join to 236
    characters. Derived rather than written down because a vocabulary gains entries over time
    and a hand-set number silently stops covering it: the transport limit was 40, which three
    trades already exceeded, so a reader ticking three boxes got a 422 and any answer that did
    get through was truncated mid-code on its way into the database.
    """
    banks = (BODY_REGIONS, TRADE_FAMILIES, WORK_MODES, EVENT_KINDS, REPORT_CHAPTERS)
    widest = max(len(_MULTI_SEP.join(bank)) for bank in banks)
    inline = max((len(_MULTI_SEP.join(o[0] for o in q.options))
                  for q in _PART_A + _PART_B_FIXED + _PART_D if q.kind == "multi"),
                 default=0)
    return max(widest, inline)


#: Transport bound for one stored answer. Rounded up from the widest the instrument can emit,
#: so the wire never refuses an answer its own question offered, while staying a real bound.
MAX_ANSWER_CHARS: int = ((_widest_multi_answer() // 64) + 1) * 64


def validate_instrument_answers(report: dict, answers: list[dict[str, Any]], *,
                                max_choices: int = 12) -> list[str]:
    """Check submitted answers against the instrument this chart actually generates.

    The instrument is deterministic, so the server can rebuild it and reject a qid it never
    asked or a value it never offered — no client-supplied question text is trusted into the
    scoring path. Returns a list of human-readable problems; empty means every answer is legal.
    """
    payload, _key = _build(report, "en", max_choices)
    by_qid = {q["qid"]: q for p in payload["parts"] for q in p["questions"]}
    problems: list[str] = []
    for a in answers:
        qid = str(a.get("qid", ""))
        base = qid.removesuffix(".confidence").split("#", 1)[0]
        q = by_qid.get(base)
        if q is None:
            problems.append(f"unknown question {qid!r}")
            continue
        value = a.get("answer")
        if qid.endswith(".confidence"):
            if not q.get("confidence"):
                problems.append(f"{qid!r} does not take a confidence rating")
            elif str(value) not in CONFIDENCE_SCALE:
                problems.append(f"{qid!r}: confidence must be one of {CONFIDENCE_SCALE}")
            continue
        legal = {o["value"] for o in q["options"]}
        kind = q["kind"]
        if kind == "choice":
            if str(value) not in legal:
                problems.append(f"{qid!r}: answer must be one of {sorted(legal)}")
        elif kind == "multi":
            picked = [v.strip() for v in str(value or "").split(_MULTI_SEP) if v.strip()]
            if not picked:
                problems.append(f"{qid!r}: choose at least one option")
            for v in picked:
                if v not in legal:
                    problems.append(f"{qid!r}: {v!r} is not one of {sorted(legal)}")
        elif kind == "scale":
            if str(value) not in ANSWER_SCALE:
                problems.append(f"{qid!r}: answer must be one of {ANSWER_SCALE}")
        elif kind == "year":
            if not (str(value or "").isdigit() and 1800 <= int(value) <= 2200):
                problems.append(f"{qid!r}: expected a four-digit year")
        elif kind == "events":
            m = _EVENT_RE.match(str(value or ""))
            if m is None:
                problems.append(f"{qid!r}: expected YYYY:kind or YYYY-MM:kind")
            elif m.group(3) not in legal:
                problems.append(f"{qid!r}: {m.group(3)!r} is not one of {sorted(legal)}")
        elif value not in (None, "", "answered"):
            problems.append(f"{qid!r} is an open question and takes free text only")
    return problems
