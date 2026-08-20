"""The whole reading in words a reader without any astrology can follow.

The report already opens with a plain-English chapter ("Your Reading"). Real feedback was that
it is still too technical, and reading it back that is fair: it names the planet that shapes the
temperament, quotes rules, and reconciles verdicts against each other. Plain ENGLISH is not the
same thing as plain SENSE.

So this is a further step down, and a deliberately small one. Nine short blocks, no Sanskrit, no
planet names, no house numbers, no citations, no percentages — everyday words for everyday
matters, plus the two honesty lines that must never be dropped: how much of a reading like this
is true of nearly everybody, and that a traditional method describing tendencies is not a
forecast.

It creates NOTHING. Every block is a re-read of material judged elsewhere (PREC-10): the house
verdicts and their population shares come from `calibration`, the unusual readings from
`distinctive`, the running period from the Nichod's own current-period line, the temperament
from `psych`. If this section and a chapter below it ever disagree, the chapter governs and the
summary is the thing that is wrong.

Both languages are generated, not translated at render time: the page toggles on the client and
`t()` cannot translate a sentence composed at runtime, so a Hindi reader would otherwise meet an
English summary inside a Hindi report.

Usage:
    from app.raman_saab.simple_summary import build_simple_summary
    summary = build_simple_summary(report)          # `to_report_dict`-shaped dict
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

#: What each house is called in a sentence a person would actually say. Not "the 2nd bhava",
#: not "wealth & speech" — the words someone uses about their own life.
PLAIN_HOUSE: dict[int, tuple[str, str]] = {
    1: ("your health and energy", "आपका स्वास्थ्य और ऊर्जा"),
    2: ("money and family life", "धन और पारिवारिक जीवन"),
    3: ("courage, and brothers and sisters", "साहस, और भाई-बहन"),
    4: ("home, property and your mother", "घर, संपत्ति और माता"),
    5: ("children and learning", "संतान और विद्या"),
    6: ("illness, debts and rivals", "बीमारी, कर्ज़ और विरोधी"),
    7: ("marriage and partnerships", "विवाह और साझेदारी"),
    8: ("big changes and difficult passages", "बड़े बदलाव और कठिन दौर"),
    9: ("luck, higher study and your father", "भाग्य, उच्च शिक्षा और पिता"),
    10: ("work and standing", "काम और प्रतिष्ठा"),
    11: ("income, gains and friends", "आय, लाभ और मित्र"),
    12: ("spending, time away from home, and inner life",
         "खर्च, घर से दूर का समय, और आंतरिक जीवन"),
}

#: A handful of significations whose plain name differs enough from its house's to be worth
#: naming on its own when the reading is an unusual one.
PLAIN_SIGNIFICATION: dict[str, tuple[str, str]] = {
    "poorvapunya": ("luck you did not work for", "बिना मेहनत का भाग्य"),
    "foreign_residence": ("living far from where you were born", "जन्मस्थान से दूर रहना"),
    "loss_moksha": ("letting things go", "चीज़ों को छोड़ पाना"),
    "moksha": ("your inner or religious life", "आपका आंतरिक या धार्मिक जीवन"),
    "incarceration": ("being shut in or restricted", "बंदिश या पाबंदी"),
    "marital_happiness": ("happiness in marriage", "वैवाहिक सुख"),
    "property": ("land and property", "ज़मीन और संपत्ति"),
    "mother": ("your mother", "आपकी माता"),
    "father": ("your father", "आपके पिता"),
    "vehicles": ("vehicles", "वाहन"),
    "status_honour": ("recognition for your work", "काम के लिए मिलने वाली पहचान"),
    "short_journeys": ("short trips and local travel", "छोटी यात्राएँ"),
    "profession_authority": ("working under someone else", "किसी के अधीन काम"),
    "profession_trade": ("working for yourself", "अपना काम"),
    "debts": ("debt", "कर्ज़"),
    "enemies": ("people who work against you", "विरोधी"),
    "disease_chronic": ("long illness", "लंबी बीमारी"),
    "legacies": ("inheritance", "विरासत"),
    "children": ("children", "संतान"),
    "higher_learning": ("higher study", "उच्च शिक्षा"),
}

#: The planets, as the everyday quality the reading already attributes to them. Used only for
#: the one sentence about temperament, so the summary can say something about the person
#: without saying a planet's name.
#: Complete predicates in both languages: the sentence below reads "…describes someone WHO
#: <this>", and a Hindi phrase without a verb leaves it dangling.
_TEMPERAMENT: dict[str, tuple[str, str]] = {
    "Sun": ("is steady and self-reliant, happier leading than following",
            "स्थिर और आत्मनिर्भर हैं, अनुसरण से ज़्यादा नेतृत्व में सहज हैं"),
    "Moon": ("is responsive and changeable, guided a good deal by feeling",
             "संवेदनशील और परिवर्तनशील हैं, बहुत कुछ भावना से चलते हैं"),
    "Mars": ("is direct and quick to act, with a short fuse when crossed",
             "सीधे और तुरंत कर्म करने वाले हैं, टोके जाने पर जल्दी गर्म हो जाते हैं"),
    "Mercury": ("is quick-minded and talkative, at home with words, numbers and dealing",
                "तेज़ बुद्धि वाले और बातूनी हैं, शब्दों, अंकों और लेन-देन में सहज हैं"),
    "Jupiter": ("is broad-minded and trusted by others, drawn to learning and to advising",
                "उदार हैं और दूसरों के भरोसेमंद हैं, विद्या और सलाह की ओर झुकाव रखते हैं"),
    "Venus": ("is sociable and drawn to comfort, beauty and good company",
              "मिलनसार हैं और आराम, सौंदर्य तथा अच्छी संगत की ओर झुकाव रखते हैं"),
    "Saturn": ("is patient and hard-working, slow to change and slow to complain",
               "धैर्यवान और परिश्रमी हैं, धीरे बदलते हैं और कम शिकायत करते हैं"),
}

_DEGREE_WORD: dict[str, tuple[str, str]] = {
    "strong": ("strongly", "प्रबल रूप से"),
    "moderate": ("", ""),
    "mild": ("mildly", "हल्के रूप से"),
}


@dataclass(frozen=True)
class SimpleSummary:
    """The reading in plain words. Every field is prose in both languages, or empty."""
    opening_en: str
    opening_hi: str
    you_en: str
    you_hi: str
    good_en: str
    good_hi: str
    hard_en: str
    hard_hi: str
    mixed_en: str
    mixed_hi: str
    now_en: str
    now_hi: str
    unusual_en: str
    unusual_hi: str
    common_en: str
    common_hi: str
    how_to_read_en: str
    how_to_read_hi: str
    caveat_en: str
    caveat_hi: str
    #: The running period's live matters, as items for the same reason.
    now_items_en: tuple[str, ...] = ()
    now_items_hi: tuple[str, ...] = ()
    #: The three verdict groups as ITEMS rather than one joined sentence. Several plain house
    #: names contain commas of their own ("luck, higher study and your father"), so joining
    #: seven of them produces a run-on where the list commas and the label commas are
    #: indistinguishable. Every renderer shows these as a list.
    good_items_en: tuple[str, ...] = ()
    good_items_hi: tuple[str, ...] = ()
    hard_items_en: tuple[str, ...] = ()
    hard_items_hi: tuple[str, ...] = ()
    mixed_items_en: tuple[str, ...] = ()
    mixed_items_hi: tuple[str, ...] = ()
    #: The houses each list was built from, so a renderer can cross-link and a test can check
    #: the prose against the verdicts rather than against itself.
    good_houses: tuple[int, ...] = ()
    hard_houses: tuple[int, ...] = ()
    mixed_houses: tuple[int, ...] = ()


def _join(parts: list[str], lang: str) -> str:
    parts = [p for p in parts if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    joiner = " और " if lang == "hi" else " and "
    return (", ".join(parts[:-1])) + joiner + parts[-1]


def _house_rollup(report: dict) -> dict[int, str]:
    """One verdict per house — whichever direction most of its readings take.

    The house-by-house chapter judges each signification separately, and a house can hold both
    poles at once. A summary that listed a house under both would be useless, so it takes the
    majority direction and the mixed case is named as mixed rather than resolved by a tiebreak.
    """
    out: dict[int, str] = {}
    for key, block in (report.get("calibration") or {}).items():
        try:
            house = int(key)
        except (TypeError, ValueError):
            continue
        good = bad = other = 0
        for e in block.get("entries") or ():
            v = e.get("verdict")
            if v == "favourable":
                good += 1
            elif v == "afflicted":
                bad += 1
            else:
                other += 1
        if not (good or bad or other):
            continue
        if good and not bad:
            out[house] = "good"
        elif bad and not good:
            out[house] = "hard"
        elif good > bad * 2:
            out[house] = "good"
        elif bad > good * 2:
            out[house] = "hard"
        else:
            out[house] = "mixed"
    return out


def _period_houses(report: dict) -> tuple[int, ...]:
    """The houses the running period lights, read off the Nichod's own current-period line."""
    line = str(((report.get("nichod") or {}).get("current_period")) or "")
    out: list[int] = []
    for token in line.replace(",", " ").split():
        if token.startswith("H") and token[1:].isdigit():
            n = int(token[1:])
            if 1 <= n <= 12 and n not in out:
                out.append(n)
    return tuple(out)


def _period_now(report: dict) -> tuple[str, str]:
    """The running period, said the way a person would say it.

    The Nichod already prints it as "Moon MD / Jupiter AD, ordinary — lighting H2, H4…". That
    line is for someone who knows what an MD is. This one names the matters and the strength,
    and nothing else.
    """
    line = str(((report.get("nichod") or {}).get("current_period")) or "")
    if not line:
        return "", ""
    houses: list[int] = []
    for token in line.replace(",", " ").split():
        if token.startswith("H") and token[1:].isdigit():
            n = int(token[1:])
            if 1 <= n <= 12:
                houses.append(n)
    strength_en = strength_hi = ""
    low = line.casefold()
    if "par excellence" in low:
        strength_en, strength_hi = "a strong stretch", "एक प्रबल दौर"
    elif "ordinary" in low:
        strength_en, strength_hi = "an ordinary stretch", "एक सामान्य दौर"
    elif "limited" in low:
        strength_en, strength_hi = "a quiet stretch", "एक शांत दौर"
    elif "feeble" in low:
        strength_en, strength_hi = "a weak stretch", "एक कमज़ोर दौर"
    if not houses:
        return "", ""
    # A lead sentence and a LIST, for the same reason the verdict groups are lists: the plain
    # labels carry commas of their own, so joining several of them into one clause produces
    # a sentence whose commas cannot be told apart.
    en = (f"Right now the method reads {strength_en or 'a stretch'}. These are the matters it "
          f"calls live — which parts of life the old method considers active, not a claim "
          f"that anything in particular is coming:")
    hi = (f"इस समय यह पद्धति {strength_hi or 'एक दौर'} पढ़ती है। ये वे विषय हैं जिन्हें यह सक्रिय "
          f"कहती है — यानी पुरानी पद्धति जीवन के किन पक्षों को सक्रिय मानती है; यह दावा नहीं कि कुछ "
          f"विशेष होने वाला है:")
    return en, hi


def _unusual(report: dict, limit: int = 3) -> tuple[str, str]:
    """The handful of readings that are actually uncommon for this chart.

    This is the most useful sentence in the summary and the one a reader is least likely to
    get anywhere else: nearly everything a chart says is said about nearly everybody, so the
    few readings that are NOT are where the reading carries information about this person.
    Items on the channels the project's own atlas proved run backwards are excluded — naming
    them as "unusual and true" would be promoting a known error to a headline.
    """
    rows = []
    for house, e in report.get("distinctive") or ():
        if e.get("inverted_warning"):
            continue
        if e.get("rarity") not in ("rare", "notable"):
            continue
        sig = e.get("signification", "")
        plain = PLAIN_SIGNIFICATION.get(sig) or PLAIN_HOUSE.get(int(house))
        if not plain:
            continue
        good = e.get("verdict") == "favourable"
        rows.append((plain, good))
        if len(rows) >= limit:
            break
    if not rows:
        return "", ""
    good_en = [p[0] for p, g in rows if g]
    good_hi = [p[1] for p, g in rows if g]
    bad_en = [p[0] for p, g in rows if not g]
    bad_hi = [p[1] for p, g in rows if not g]
    bits_en, bits_hi = [], []
    if good_en:
        bits_en.append(f"it is unusually positive about {_join(good_en, 'en')}")
        bits_hi.append(f"{_join(good_hi, 'hi')} के बारे में यह असामान्य रूप से अच्छा कहती है")
    if bad_en:
        bits_en.append(f"it is unusually negative about {_join(bad_en, 'en')}")
        bits_hi.append(f"{_join(bad_hi, 'hi')} के बारे में यह असामान्य रूप से कठिन कहती है")
    en = ("Most of this reading would fit most people. The few places where it does not — "
          "where it says something that only a small minority of charts say — are these: "
          + _join(bits_en, "en") + ". If you want to test whether any of this is worth "
          "anything, test it there.")
    hi = ("इस फलादेश का अधिकांश हिस्सा अधिकतर लोगों पर बैठ जाएगा। जहाँ ऐसा नहीं है — जहाँ यह ऐसा "
          "कुछ कहती है जो बहुत कम कुंडलियाँ कहती हैं — वे ये हैं: " + _join(bits_hi, "hi")
          + "। यदि आप जाँचना चाहें कि इसमें कुछ दम है या नहीं, तो वहीं जाँचिए।")
    return en, hi


def _common(report: dict) -> tuple[str, str]:
    """The honesty line, in plain words and with the actual counts from this chart."""
    info = report.get("info") or {}
    total = int(info.get("total") or 0)
    near = int(info.get("near_universal") or 0)
    distinctive = int(info.get("distinctive") or 0)
    if not total:
        return "", ""
    en = (f"Being straight with you about how much this is worth: the reading makes {total} "
          f"separate judgements about your life. {near} of them are held by half the "
          f"population or more, so they say almost nothing about you in particular. About "
          f"{distinctive} are genuinely uncommon. That is the honest shape of it, and it is "
          f"true of any chart read this way, not a fault of yours.")
    hi = (f"यह कितना काम का है, इस बारे में सीधी बात: यह फलादेश आपके जीवन के बारे में {total} "
          f"अलग-अलग निर्णय देता है। इनमें से {near} आधी या उससे अधिक आबादी पर लागू होते हैं, "
          f"इसलिए वे आपके बारे में लगभग कुछ नहीं कहते। लगभग {distinctive} सचमुच असामान्य हैं। "
          f"यही इसकी ईमानदार तस्वीर है, और यह इस तरह पढ़ी गई हर कुंडली पर लागू होती है।")
    return en, hi


def build_simple_summary(report: dict) -> Optional[SimpleSummary]:
    """The whole reading in plain words, or None when the report is too sparse to summarise."""
    roll = _house_rollup(report)
    if not roll:
        return None

    good = tuple(sorted(h for h, v in roll.items() if v == "good"))
    hard = tuple(sorted(h for h, v in roll.items() if v == "hard"))
    mixed = tuple(sorted(h for h, v in roll.items() if v == "mixed"))

    def items(houses: tuple[int, ...], lang: str) -> tuple[str, ...]:
        idx = 0 if lang == "en" else 1
        return tuple(PLAIN_HOUSE[h][idx] for h in houses if h in PLAIN_HOUSE)

    stamp = str((report.get("psych") or {}).get("nature_stamp") or "")
    temper = _TEMPERAMENT.get(stamp)
    you_en = (f"In temperament, the method describes someone who {temper[0]}. That is a "
              f"description of tendencies, not a verdict on your character." if temper else "")
    you_hi = (f"स्वभाव में यह पद्धति ऐसे व्यक्ति का वर्णन करती है जो {temper[1]}। यह प्रवृत्तियों "
              f"का वर्णन है, आपके चरित्र पर निर्णय नहीं।" if temper else "")

    good_en = ("The parts of life this reading calls favourable:"
               if good else "This reading calls no part of life plainly favourable.")
    good_hi = ("जिन पक्षों को यह फलादेश अनुकूल कहता है:"
               if good else "यह फलादेश किसी भी पक्ष को स्पष्ट रूप से अनुकूल नहीं कहता।")
    hard_en = ("The parts it calls difficult:"
               if hard else "It calls no part of life plainly difficult.")
    hard_hi = ("जिन पक्षों को यह कठिन कहता है:"
               if hard else "यह किसी भी पक्ष को स्पष्ट रूप से कठिन नहीं कहता।")
    mixed_en = ("And the parts it reads both ways at once, where the old texts pull in "
                "different directions:" if mixed else "")
    mixed_hi = ("और जिन पक्षों को यह दोनों तरह पढ़ता है, जहाँ पुराने ग्रंथ अलग-अलग दिशा में जाते हैं:"
                if mixed else "")

    now_en, now_hi = _period_now(report)
    now_houses = _period_houses(report)
    unusual_en, unusual_hi = _unusual(report)
    common_en, common_hi = _common(report)

    return SimpleSummary(
        opening_en="This page is the whole reading in ordinary words. Everything below it is "
                   "the same thing said in the traditional way, with the reasons and the book "
                   "references. Nothing here is new — if this page and a chapter below "
                   "disagree, the chapter is right.",
        opening_hi="यह पन्ना पूरे फलादेश को साधारण शब्दों में कहता है। नीचे जो कुछ है वह वही बात "
                   "पारंपरिक ढंग से, कारणों और ग्रंथ-संदर्भों के साथ कही गई है। यहाँ कुछ भी नया नहीं है "
                   "— यदि यह पन्ना और नीचे का कोई अध्याय अलग बात कहें, तो अध्याय सही है।",
        you_en=you_en, you_hi=you_hi,
        good_en=good_en, good_hi=good_hi,
        hard_en=hard_en, hard_hi=hard_hi,
        mixed_en=mixed_en, mixed_hi=mixed_hi,
        now_en=now_en, now_hi=now_hi,
        unusual_en=unusual_en, unusual_hi=unusual_hi,
        common_en=common_en, common_hi=common_hi,
        how_to_read_en="If you read nothing else, read the two paragraphs above about what is "
                       "unusual here and how much of it is common. Then go to whichever "
                       "chapter below covers the matter you actually came here about.",
        how_to_read_hi="अगर और कुछ न पढ़ें, तो ऊपर के दो पैराग्राफ़ पढ़िए — क्या असामान्य है और "
                       "कितना सामान्य है। फिर नीचे उसी अध्याय पर जाइए जो उस विषय का है जिसके "
                       "लिए आप आए हैं।",
        caveat_en="One last thing, plainly. This is a faithful account of what a particular "
                  "old method says about a chart. When this project measured that method "
                  "against thousands of real lives, it did not find that it predicted them. "
                  "So read this as a tradition describing tendencies, not as news about your "
                  "future.",
        caveat_hi="आख़िरी बात, साफ़-साफ़। यह इस बात का निष्ठापूर्ण विवरण है कि एक विशेष पुरानी "
                  "पद्धति कुंडली के बारे में क्या कहती है। जब इस परियोजना ने उस पद्धति को हज़ारों "
                  "वास्तविक जीवनों के विरुद्ध मापा, तो यह नहीं पाया कि वह उन्हें बताती है। इसलिए "
                  "इसे प्रवृत्तियों का वर्णन करती परंपरा मानिए, अपने भविष्य का समाचार नहीं।",
        now_items_en=items(now_houses, "en"), now_items_hi=items(now_houses, "hi"),
        good_items_en=items(good, "en"), good_items_hi=items(good, "hi"),
        hard_items_en=items(hard, "en"), hard_items_hi=items(hard, "hi"),
        mixed_items_en=items(mixed, "en"), mixed_items_hi=items(mixed, "hi"),
        good_houses=good, hard_houses=hard, mixed_houses=mixed)
