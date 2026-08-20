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
INSTRUMENT_VERSION = "v1"

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


# ── Part A: the blind bank ──────────────────────────────────────────────────────────────────
# Chart-INDEPENDENT by design. These are the questions whose answers can be scored against the
# reading afterwards, and they are worth nothing if the reader has already been told what the
# chart says. Only A34 reaches into the chart, and only to be compared later — never shown with
# its dates attached.
#
# Each row: (qid suffix, group, english, hindi, hint_en, hint_hi)
_PART_A: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("A1", "birth_record",
     "Where did your birth time come from — a hospital record, a birth certificate, a horoscope "
     "written at the time, or someone's memory?",
     "आपका जन्म-समय कहाँ से आया — अस्पताल का रिकॉर्ड, जन्म प्रमाण-पत्र, उस समय बनी कुंडली, या किसी की याददाश्त?",
     "", ""),
    ("A2", "birth_record",
     "If it came from memory, was it a round number like \"about five\", a time of day like "
     "\"just before dawn\", or an exact clock reading?",
     "अगर याददाश्त से — कोई गोल समय जैसे \"लगभग पाँच\", दिन का कोई पहर जैसे \"भोर से ठीक पहले\", या घड़ी का सटीक समय?",
     "", ""),
    ("A3", "birth_record",
     "Has any astrologer already changed or corrected this time? To what, and on what grounds?",
     "क्या किसी ज्योतिषी ने यह समय पहले बदला या शोधित किया है? किस समय पर, और किस आधार पर?",
     "", ""),
    ("A4", "health",
     "List every illness, injury, surgery or hospital stay you have had, with the year of each.",
     "हर बीमारी, चोट, ऑपरेशन या अस्पताल में भर्ती होने की सूची, वर्ष सहित।",
     "", ""),
    ("A5", "health",
     "Which parts of your body give you recurring trouble — the ones you would mention to a new "
     "doctor without being asked?",
     "शरीर के कौन-से हिस्से बार-बार परेशान करते हैं — जो आप नए डॉक्टर को बिना पूछे बताएँगे?",
     "", ""),
    ("A6", "health",
     "Were you a sickly infant or a healthy one? Was there any danger to your life before the "
     "age of eight?",
     "बचपन में सेहत कैसी थी? आठ वर्ष की आयु से पहले जान का कोई ख़तरा?",
     "", ""),
    ("A7", "health",
     "How long did your grandparents live? How is your parents' health now?",
     "दादा-दादी / नाना-नानी कितने वर्ष जिए? माता-पिता का वर्तमान स्वास्थ्य कैसा है?",
     "", ""),
    ("A8", "family",
     "Describe your relationship with your father — including any long absence, illness, "
     "financial reversal, conflict, or early death.",
     "पिता से अपने संबंध बताइए — लंबी अनुपस्थिति, बीमारी, आर्थिक नुक़सान, मतभेद, या असमय मृत्यु सहित।",
     "", ""),
    ("A9", "family",
     "The same for your mother.",
     "यही माता के बारे में।",
     "", ""),
    ("A10", "family",
     "Your relationship with your siblings — close, distant, or absent? Any loss among them?",
     "भाई-बहनों से संबंध — निकट, दूर, या नहीं? कोई हानि?",
     "", ""),
    ("A11", "education",
     "Your highest completed education — and did it go smoothly, or was it interrupted?",
     "आपकी उच्चतम शिक्षा — वह सहज रही या बीच में रुकी?",
     "", ""),
    ("A12", "money",
     "How do you actually earn — salary, own business, trade, commission, professional practice, "
     "farming, something else? Has that changed over the years?",
     "आप वास्तव में कैसे कमाते हैं — वेतन, अपना व्यवसाय, व्यापार, कमीशन, पेशेवर प्रैक्टिस, खेती, या कुछ और? क्या यह बदला है?",
     "", ""),
    ("A13", "money",
     "Have you had significant money from travel, from outside your home district, or from "
     "abroad?",
     "यात्रा से, अपने ज़िले के बाहर से, या विदेश से कोई बड़ी आमदनी हुई है?",
     "", ""),
    ("A14", "money",
     "Have you ever gained or lost significantly through speculation, lottery, betting, shares, "
     "or crypto? Roughly when, and how large against your income?",
     "सट्टा, लॉटरी, शेयर, या क्रिप्टो से कभी बड़ा लाभ या हानि? कब, और आय के मुक़ाबले कितना?",
     "", ""),
    ("A15", "money",
     "Any inheritance, legacy, insurance payout, or unexpected windfall? Do you carry debt now?",
     "कोई विरासत, बीमा, या अप्रत्याशित धन? क्या इस समय आप पर कर्ज़ है?",
     "", ""),
    ("A16", "work",
     "What is your work — stated plainly enough that a stranger would understand it?",
     "आपका काम क्या है — इतना सीधा बताइए कि कोई अजनबी समझ जाए।",
     "", ""),
    ("A17", "work",
     "Have you ever worked in, or been drawn to: metals, machinery, construction, fire or heat "
     "trades, military or police, surgery or pharmacy, driving or transport?",
     "धातु, मशीन, निर्माण, आग/गर्मी वाले काम, सेना या पुलिस, सर्जरी या दवा, ड्राइविंग या परिवहन — कभी काम किया या आकर्षण रहा?",
     "Answer even if it was brief, or only an attraction that went nowhere.",
     "अगर थोड़े समय के लिए भी, या सिर्फ़ आकर्षण रहा हो, तब भी बताइए।"),
    ("A18", "work",
     "Have you ever worked in, or been drawn to: writing, journalism, mathematics, accounts, "
     "teaching, astrology, or design?",
     "लेखन, पत्रकारिता, गणित, लेखा, अध्यापन, ज्योतिष, या डिज़ाइन — कभी काम किया या आकर्षण रहा?",
     "", ""),
    ("A19", "work",
     "Have you ever worked in, or been drawn to: law, counselling, banking, or religious and "
     "advisory work?",
     "क़ानून, परामर्श, बैंकिंग, या धार्मिक/सलाहकार कार्य — कभी?",
     "", ""),
    ("A20", "work",
     "Do you work under an authority — an employer, the government, a senior — or for yourself? "
     "Which has gone better for you?",
     "आप किसी के अधीन काम करते हैं या अपने लिए? कौन-सा बेहतर रहा?",
     "", ""),
    ("A21", "work",
     "Any promotion, public recognition, honour or title — or any public setback or humiliation? "
     "Give the year of each.",
     "कोई पदोन्नति, सार्वजनिक सम्मान या उपाधि — या कोई सार्वजनिक झटका या अपमान? हर एक का वर्ष बताइए।",
     "", ""),
    ("A22", "marriage",
     "Are you married? If yes, the month and year. If not, has marriage been attempted, "
     "arranged, delayed, or broken off — and when?",
     "विवाह हुआ? हाँ तो महीना और वर्ष। नहीं तो — प्रयास, तय होकर टूटना, या देरी — कब?",
     "", ""),
    ("A23", "marriage",
     "By your family's standards, was there delay or difficulty in it happening? Describe the "
     "marriage, or your closest partnership, plainly — happy, strained, separated?",
     "आपके परिवार के हिसाब से इसमें देरी या कठिनाई हुई? विवाह या निकटतम साझेदारी को सीधे शब्दों में बताइए — सुखी, तनावपूर्ण, अलगाव?",
     "", ""),
    ("A24", "marriage",
     "Any business partnership? How did it end?",
     "कोई व्यापारिक साझेदारी? उसका अंत कैसे हुआ?",
     "", ""),
    ("A25", "children",
     "Children — how many, and the year of each. Any difficulty conceiving, or any loss?",
     "संतान — कितने, हर एक का वर्ष। गर्भधारण में कठिनाई, या कोई हानि?",
     "", ""),
    ("A26", "mind",
     "In three words, how would someone who dislikes you describe you?",
     "तीन शब्दों में — जो आपको नापसंद करता है, वह आपका वर्णन कैसे करेगा?",
     "", ""),
    ("A27", "mind",
     "Have you had any period of depression, severe anxiety, breakdown, or treatment for the "
     "mind?",
     "अवसाद, गंभीर चिंता, या मानसिक इलाज का कोई दौर?",
     "Leave this blank if you would rather not answer.",
     "यदि उत्तर न देना चाहें तो खाली छोड़ दें।"),
    ("A28", "mind",
     "Are you drawn to religion, philosophy, the occult, or solitary practice? To what degree?",
     "धर्म, दर्शन, गूढ़ विद्या, या एकांत साधना में रुचि? कितनी?",
     "", ""),
    ("A29", "mind",
     "Have you lived away from your birthplace for long? Abroad? In a hostel, institution, "
     "ashram, hospital, or confinement of any kind?",
     "जन्मस्थान से लंबे समय दूर रहे? विदेश? किसी छात्रावास, संस्था, आश्रम, अस्पताल, या बंदिश में?",
     "", ""),
    ("A30", "turning_points",
     "Without thinking about astrology at all, list the five to eight turning points of your "
     "life so far — each with a month and year. Anything that changed your direction: a move, a "
     "job, a loss, an illness, a marriage, a break, a beginning.",
     "ज्योतिष को बिल्कुल भूलकर — अब तक के पाँच से आठ निर्णायक मोड़, हर एक का महीना और वर्ष लिखिए। "
     "जिसने भी आपकी दिशा बदली: स्थानांतरण, नौकरी, हानि, बीमारी, विवाह, कोई अंत, कोई शुरुआत।",
     "This is the most valuable answer on the form. Write it before you read anything else, and "
     "do not go back and change it later.",
     "यह इस फ़ॉर्म का सबसे मूल्यवान उत्तर है। कुछ भी और पढ़ने से पहले लिखिए, और बाद में बदलिए मत।"),
    ("A31", "turning_points",
     "Which single year of your life was the worst? Which was the best?",
     "कौन-सा एक वर्ष सबसे बुरा रहा? कौन-सा सबसे अच्छा?",
     "", ""),
)

_PART_A_GROUPS: dict[str, tuple[str, str]] = {
    "birth_record": ("The birth record", "जन्म का विवरण"),
    "health": ("Body and health", "शरीर और स्वास्थ्य"),
    "family": ("Parents and siblings", "माता-पिता और भाई-बहन"),
    "education": ("Education", "शिक्षा"),
    "money": ("Money", "धन"),
    "work": ("Work", "काम"),
    "marriage": ("Marriage and partnership", "विवाह और साझेदारी"),
    "children": ("Children", "संतान"),
    "mind": ("Mind and temperament", "मन और स्वभाव"),
    "turning_points": ("The turning points", "जीवन के मोड़"),
}

# ── Part B: the fixed rectification questions ───────────────────────────────────────────────
_PART_B_FIXED: tuple[tuple[str, str, str, str, str], ...] = (
    ("B2", "Your build — lean and on the taller side, or solid and heavy-set with a tendency to "
            "put on weight?",
     "शरीर — दुबला और कुछ लंबा, या भारी और वज़न बढ़ने की प्रवृत्ति वाला?", "", ""),
    ("B3", "Your complexion and hair — and do people guess your age older or younger than you "
            "are?",
     "रंग और बाल — लोग आपकी उम्र ज़्यादा आँकते हैं या कम?", "", ""),
    ("B4", "Any distinguishing mark, mole or scar on your head, face or upper body — and on "
            "which side?",
     "सिर, चेहरे या ऊपरी शरीर पर कोई तिल, निशान या दाग़ — और किस तरफ़?", "", ""),
    ("B5", "Are you the eldest, middle, or youngest? Were you born at home or in a hospital?",
     "आप सबसे बड़े, मंझले, या सबसे छोटे? जन्म घर पर हुआ या अस्पताल में?", "", ""),
    ("B6", "Give exact months, as far as you can, for: your father's death or major illness, "
            "your marriage, your first job, and any surgery.",
     "इनके सटीक महीने बताइए: पिता की मृत्यु या गंभीर बीमारी, विवाह, पहली नौकरी, और कोई ऑपरेशन।",
     "These are the events a birth time is actually corrected against, so exact months matter "
     "more here than anywhere else on the form.",
     "जन्म-समय इन्हीं घटनाओं से शोधित होता है, इसलिए यहाँ सटीक महीने सबसे ज़्यादा मायने रखते हैं।"),
)

# ── Part D: after the reading ───────────────────────────────────────────────────────────────
_PART_D: tuple[tuple[str, str, str, str], ...] = (
    ("D1", "open", "What in the reading was wrong — plainly, factually wrong about your life?",
     "फलादेश में क्या ग़लत था — आपके जीवन के बारे में साफ़ तौर पर तथ्यतः ग़लत?"),
    ("D2", "open", "What was right in a way that could not have been guessed about just anyone?",
     "क्या ऐसा सही था जो किसी के भी बारे में अंदाज़े से नहीं कहा जा सकता था?"),
    ("D3", "open", "Which parts felt true of you — and also true of most people you know?",
     "कौन-से हिस्से आप पर सही लगे — और आपके अधिकांश परिचितों पर भी?"),
    ("D4", "open", "Was anything upsetting, frightening, or badly worded?",
     "कुछ परेशान करने वाला, डरावना, या ग़लत शब्दों में कहा हुआ था?"),
    ("D5", "open", "Which section did you skip, or not understand?",
     "कौन-सा भाग आपने छोड़ दिया, या समझ नहीं आया?"),
    ("D6", "scale", "Overall, how well did this reading match your life?",
     "कुल मिलाकर, यह फलादेश आपके जीवन से कितना मेल खाता है?"),
)


# ── builders ────────────────────────────────────────────────────────────────────────────────

def _sign_name(sign: int, lang: Lang) -> str:
    table = _SIGN_NAMES_HI if lang == "hi" else _SIGN_NAMES
    return table[sign - 1] if 1 <= sign <= 12 else f"sign {sign}"


def _seed(report: dict) -> str:
    """A stable per-chart seed. Built from the birth fields ONLY (the name is left out, so two
    readings of the same nativity get the same instrument), and hashed with sha256 rather than
    `hash()` — the interpreter's string hash is randomised per process, which would reshuffle
    the forced choices on every restart and make stored answers unscoreable."""
    b = report.get("birth") or {}
    parts = [str(b.get(k, "")) for k in
             ("year", "month", "day", "hour", "minute", "tz_offset", "latitude", "longitude")]
    parts.append(str((report.get("chart") or {}).get("asc_lon", "")))
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

    These are what a freely-given list of turning points (A30) is compared against. They are
    shown only in Part C, never beside A30 — a reader who sees the dates first will find events
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
       confidence: bool = False, allow_free_text: bool = True) -> dict[str, Any]:
    """One question, in BOTH languages.

    The page toggles language on the client without re-fetching, so a payload carrying only the
    language that was asked for would leave a Hindi reader answering an English questionnaire
    inside an otherwise Hindi page. There is no `text` key on purpose: a consumer must choose a
    language rather than silently getting whichever one the request happened to default to.
    """
    return {"qid": qid, "part": part, "group": group,
            "group_label_en": group_label_en, "group_label_hi": group_label_hi,
            "kind": kind, "text_en": text_en, "text_hi": text_hi,
            "hint_en": hint_en, "hint_hi": hint_hi, "options": list(options),
            "confidence": confidence, "allow_free_text": allow_free_text}


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

    # ── Part A ──────────────────────────────────────────────────────────────────────────
    a_questions = [
        _q(f"inst.{INSTRUMENT_VERSION}.{sid}", "A", group,
           _PART_A_GROUPS[group][0], _PART_A_GROUPS[group][1], "open",
           text_en, text_hi, hint_en, hint_hi)
        for sid, group, text_en, text_hi, hint_en, hint_hi in _PART_A]

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
                              rect["note_en"], rect["note_hi"], opts))
        key_answers[qid] = f"opt{[w for w, _e, _h in pair].index('here') + 1}"
        key_meta[qid] = {"kind": "rectification", "asc_sign": rect["asc_sign"],
                         "neighbour_sign": rect["neighbour_sign"],
                         "approx_gap_minutes": rect["approx_gap_minutes"]}
    b_questions += [
        _q(f"inst.{INSTRUMENT_VERSION}.{sid}", "B", "rectification", b_label[0], b_label[1],
           "open", text_en, text_hi, hint_en, hint_hi)
        for sid, text_en, text_hi, hint_en, hint_hi in _PART_B_FIXED]

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
            options=opts, confidence=True))
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
    if boundaries:
        qid = f"inst.{INSTRUMENT_VERSION}.C0"
        c_questions.append(_q(
            qid, "C", "dated_spine", "The dates", "तिथियाँ", "open",
            "These are the dates on which the chart's major periods change. Look back at the "
            "turning points you listed yourself — do not change that answer now — and say how "
            "many of them fall within about three months of one of these.",
            "ये वे तिथियाँ हैं जिन पर कुंडली की महादशा बदलती है। अपने ही लिखे मोड़ों को देखिए — "
            "उन्हें अब बदलिए मत — और बताइए कि कितने इनमें से किसी के लगभग तीन महीने के भीतर आते हैं।",
            "Use three months, not six: the period changes cluster, so a wider window covers "
            "much of a life and half-passes the test by itself.",
            "तीन महीने लीजिए, छह नहीं: दशा-परिवर्तन पास-पास आते हैं, और बड़ी खिड़की जीवन का बड़ा "
            "हिस्सा ढक लेती है।"))

    # ── Part D ──────────────────────────────────────────────────────────────────────────
    d_questions = []
    for sid, kind, text_en, text_hi in _PART_D:
        qid = f"inst.{INSTRUMENT_VERSION}.{sid}"
        opts = (tuple({"value": v, "text_en": v, "text_hi": _SCALE_HI[v]} for v in ANSWER_SCALE)
                if kind == "scale" else ())
        d_questions.append(_q(qid, "D", "reaction", "After the reading", "फलादेश पढ़ने के बाद",
                              kind, text_en, text_hi, options=opts))

    parts = [
        {"part": "A",
         "title_en": "Your life, in your own words",
         "title_hi": "आपका जीवन, आपके अपने शब्दों में",
         "note_en": "Nothing here mentions astrology, and nothing is being checked against a "
                    "prediction yet. Answer this part BEFORE reading the rest of the report — "
                    "once you have read what a chart says about you, you can no longer report "
                    "what you would have said on your own, and that is the only answer worth "
                    "measuring.",
         "note_hi": "यहाँ ज्योतिष का कोई ज़िक्र नहीं है, और अभी किसी भविष्यवाणी से कुछ नहीं मिलाया जा "
                    "रहा। यह भाग बाक़ी फलादेश पढ़ने से पहले भरें — एक बार पढ़ लेने के बाद आप वह नहीं बता "
                    "सकते जो आप अपनी ओर से कहते, और मापने लायक़ वही एक उत्तर है।",
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
         "note_en": "This part is about the reading itself, not about the chart. Being blunt "
                    "here is more useful than being kind.",
         "note_hi": "यह भाग फलादेश के बारे में है, कुंडली के बारे में नहीं। यहाँ साफ़-साफ़ कहना, "
                    "सँभालकर कहने से ज़्यादा उपयोगी है।",
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

    Deterministic for a chart, in either language, with language-independent `qid`s so answers
    given in Hindi pool with answers given in English. Carries NO indication of which option
    each forced choice was drawn from — see `instrument_key`.
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
        base, _, suffix = qid.partition(".confidence")
        q = by_qid.get(base if suffix == "" and base != qid else qid) or by_qid.get(base)
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
        if q["kind"] == "choice":
            legal = {o["value"] for o in q["options"]}
            if str(value) not in legal:
                problems.append(f"{qid!r}: answer must be one of {sorted(legal)}")
        elif q["kind"] == "scale":
            if str(value) not in ANSWER_SCALE:
                problems.append(f"{qid!r}: answer must be one of {ANSWER_SCALE}")
        elif value not in (None, "", "answered"):
            problems.append(f"{qid!r} is an open question and takes free text only")
    return problems
