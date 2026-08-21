"""The short reading — the whole app in one folio, for a reader who wants the gist.

The full reading is fifty-odd chapters and stays exactly as it is; this is a second WAY TO
READ the same computed report, not a smaller report. Nothing is dropped from the payload,
the long reading is one toggle away on every surface, and it remains the default.

What the short reading is for: someone who will not read fifty chapters wants three things —
what kind of stretch they are in and what is coming, which combinations their chart carries,
and what of it is actually distinctive. So this is:

    a plain portrait  ->  what is coming  ->  the combinations  ->  what is unusual  ->  the caveat

**No astrological vocabulary.** No house numbers, no sign names, no Sanskrit except a
combination's own name as a label, no citations, no quoted book text, no percentages. A test
runs every generated string through a banned-vocabulary screen built from the project's own
glossary, so this cannot rot: the day someone writes "the 7th house" into a sentence here,
the suite says so.

**It judges nothing.** Every line is a re-read of material judged elsewhere (PREC-10) — the
plain portrait and the verdict groups come from `simple_summary`, the periods from the
already-graded `timeline`, the combinations from the fired-yoga list and `yoga_timing`. If
this and a chapter of the full reading ever disagree, the chapter governs.

**Why the classical effects are not reprinted.** The fired-yoga records carry Raman's own
printed effects, and several of them read as verdicts on a person's character ("dirty,
sorrowful, ... a rogue and a swindler"). Handing that to a lay reader with no frame is the
opposite of a plain reading, so each combination gets a written plain gloss instead, and the
ones without a gloss say only what their family says. The full reading still prints the
effect verbatim, where it sits inside its method and its citation.

Both languages are composed here rather than translated at render time, for the same reason
`simple_summary` does it: `t()` cannot translate a sentence built at runtime.

Usage:
    from app.raman_saab.short_reading import build_short_reading
    short = build_short_reading(report_dict)      # `to_report_dict`-shaped dict
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.raman_saab.simple_summary import PLAIN_HOUSE, build_simple_summary

logger = logging.getLogger(__name__)

_DAYS_PER_YEAR = 365.2425

#: Month names for the date labels. English is the report's existing abbreviation; Hindi is
#: the Devanagari month so a Hindi reader does not meet "Mar" inside a Hindi sentence.
_MONTH: dict[int, tuple[str, str]] = {
    1: ("Jan", "जन"), 2: ("Feb", "फ़र"), 3: ("Mar", "मार्च"), 4: ("Apr", "अप्रैल"),
    5: ("May", "मई"), 6: ("Jun", "जून"), 7: ("Jul", "जुल"), 8: ("Aug", "अग"),
    9: ("Sep", "सित"), 10: ("Oct", "अक्तू"), 11: ("Nov", "नव"), 12: ("Dec", "दिस"),
}

#: The four grading tiers, said without the grading vocabulary. The tiers themselves are
#: Raman's (HTJAH-I:1592-1640) and the full reading names them; here only their sense travels.
_STRENGTH: dict[str, tuple[str, str]] = {
    "par excellence": ("a strong, well-supported stretch", "एक प्रबल, भरपूर सहारे वाला दौर"),
    "ordinary": ("a steady, ordinary stretch", "एक स्थिर, सामान्य दौर"),
    "limited": ("a quieter stretch", "एक अपेक्षाकृत शांत दौर"),
    "feeble": ("a thin stretch", "एक कमज़ोर दौर"),
}
_TIER_ORDER = ("par excellence", "ordinary", "limited", "feeble")

#: Tone by combination family — the one thing the family alone honestly settles.
_TONE: dict[str, tuple[str, str, str]] = {
    # kind -> (tone key, en word, hi word)
    "raja": ("supportive", "supportive", "सहायक"),
    "dhana": ("supportive", "supportive", "सहायक"),
    "arishta": ("difficult", "difficult", "कठिन"),
    "lunar": ("mixed", "mixed", "मिश्रित"),
    "other": ("mixed", "mixed", "मिश्रित"),
}

#: What each combination says, in words a person would use. Written, not generated, and
#: deliberately modest: a combination is a tendency the method names, never a promise.
#: Curated against measured fire-rates over the 225 golden charts, commonest first — every
#: combination that fires on more than ~1% of charts has an entry, and the rest fall back to
#: their family sentence rather than to an invented one.
PLAIN_YOGA: dict[str, tuple[str, str]] = {
    "Y.RAJA.KT": ("the supports of standing and of good fortune are tied together in your "
                  "chart — the method reads this as a lift to position and recognition",
                  "आपकी कुंडली में प्रतिष्ठा और भाग्य के आधार आपस में जुड़े हैं — यह पद्धति इसे पद और "
                  "पहचान के लिए सहायक मानती है"),
    "Y.RAJA.910X": ("the supports of fortune and of work have exchanged places — read as a "
                    "lift to standing that arrives through effort rather than by itself",
                    "भाग्य और कर्म के आधारों ने आपस में स्थान बदले हैं — इसे परिश्रम से आने वाली "
                    "प्रतिष्ठा के रूप में पढ़ा जाता है"),
    "Y.RAJA.910A": ("the supports of fortune and of work reach one another at a distance — "
                    "a milder form of the same lift to standing",
                    "भाग्य और कर्म के आधार दूर से एक-दूसरे तक पहुँचते हैं — प्रतिष्ठा की उसी वृद्धि "
                    "का हल्का रूप"),
    "Y.VIPAREETA": ("difficulty turned to advantage — the method reads hard placements as "
                    "working in your favour rather than against you",
                    "कठिनाई का लाभ में बदलना — यह पद्धति कठिन स्थितियों को आपके विरुद्ध नहीं, "
                    "आपके पक्ष में काम करता मानती है"),
    "Y.SREENATHA": ("standing and good fortune reinforce one another",
                    "प्रतिष्ठा और भाग्य एक-दूसरे को बल देते हैं"),
    "Y.VESI": ("a settled, truthful disposition; the method describes someone balanced and "
               "well spoken of",
               "स्थिर, सच्चा स्वभाव; यह पद्धति ऐसे व्यक्ति का वर्णन करती है जो संतुलित हो और जिसकी "
               "अच्छी बात हो"),
    "Y.VASI": ("openness and generosity of manner; described as liked and well regarded",
               "खुला और उदार व्यवहार; प्रिय और सम्मानित बताया गया"),
    "Y.UBHAYACHARI": ("support on both sides — the method describes an even, well-supplied "
                      "temperament",
                      "दोनों ओर से सहारा — यह पद्धति एक संतुलित, भरपूर स्वभाव का वर्णन करती है"),
    "Y.BUDHA_ADITYA": ("a quick, capable mind — described as clever and good at learning",
                       "तेज़ और सक्षम बुद्धि — चतुर और सीखने में अच्छा बताया गया"),
    "Y.AMALA": ("a clean reputation — the method describes work that is spoken of well",
                "निष्कलंक प्रतिष्ठा — यह पद्धति ऐसे काम का वर्णन करती है जिसकी अच्छी चर्चा हो"),
    "Y.GAJAKESARI": ("judgement and generosity together — one of the combinations the method "
                     "counts most supportive for standing",
                     "विवेक और उदारता साथ — प्रतिष्ठा के लिए इस पद्धति के सबसे सहायक योगों में एक"),
    "Y.SUNAPHA": ("self-earned means — described as making your own way rather than "
                  "inheriting it",
                  "स्वअर्जित साधन — विरासत के बजाय अपनी राह बनाने वाला बताया गया"),
    "Y.ANAPHA": ("an easy, well-turned-out manner; described as comfortable and well liked",
                 "सहज, सुरुचिपूर्ण व्यवहार; सुखी और प्रिय बताया गया"),
    "Y.DURUDHARA": ("support on either side of the mind's significator — described as "
                    "comfortable, with means and helpers",
                    "मन के कारक के दोनों ओर सहारा — साधन और सहयोगियों सहित सुखी बताया गया"),
    "Y.CHANDRAMANGALA": ("earning drive — the method ties it to money made through effort "
                         "and enterprise",
                         "अर्जन की प्रेरणा — यह पद्धति इसे परिश्रम और उद्यम से बने धन से जोड़ती है"),
    "Y.ADHI": ("quiet, well-placed support — described as steady standing and good health",
               "शांत, सुस्थित सहारा — स्थिर प्रतिष्ठा और अच्छा स्वास्थ्य बताया गया"),
    "Y.DHANA.CHAIN": ("the supports of earning are linked to one another — read as a "
                      "tendency for money to gather rather than scatter",
                      "अर्जन के आधार आपस में जुड़े हैं — धन के बिखरने के बजाय इकट्ठा होने की "
                      "प्रवृत्ति के रूप में पढ़ा जाता है"),
    "Y.DHANA.EXCH": ("earning and holding support each other directly",
                     "अर्जन और संचय सीधे एक-दूसरे को सहारा देते हैं"),
    "Y.DHANA.59": ("gains that come with fortune rather than only with effort",
                   "ऐसे लाभ जो केवल परिश्रम से नहीं, भाग्य के साथ आते हैं"),
    "Y.VASUMATHI": ("things tend to accumulate — described as comfortable in means",
                    "वस्तुएँ संचित होती जाती हैं — साधनों में सुखी बताया गया"),
    "Y.PARVATA": ("a raised position — described as well known in your own circle",
                  "ऊँचा स्थान — अपने क्षेत्र में सुपरिचित बताया गया"),
    "Y.CHATUSSAGARA": ("support in all four directions — described as broad standing",
                       "चारों दिशाओं से सहारा — व्यापक प्रतिष्ठा बताई गई"),
    "Y.JAYA": ("the method reads this as winning through — success against opposition",
               "यह पद्धति इसे विजय के रूप में पढ़ती है — विरोध के बावजूद सफलता"),
    "Y.RUCHAKA": ("physical vigour and command — described as forceful and well built",
                  "शारीरिक ओज और नेतृत्व — बलवान और सुगठित बताया गया"),
    "Y.BHADRA": ("sharp intelligence and skill — described as learned and well spoken",
                 "तीव्र बुद्धि और कौशल — विद्वान और वाक्पटु बताया गया"),
    "Y.HAMSA": ("an upright disposition — described as principled and well regarded",
                "सद्वृत्ति — सिद्धांतप्रिय और सम्मानित बताया गया"),
    "Y.MALAVYA": ("comfort and refinement — described as well provided for and content at "
                  "home",
                  "सुख और परिष्कार — साधन-संपन्न और घर में संतुष्ट बताया गया"),
    "Y.SASA": ("authority over others — described as commanding, and firm in getting things "
               "done",
               "दूसरों पर अधिकार — प्रभावशाली और काम कराने में दृढ़ बताया गया"),
    "Y.KEDARA": ("effort spread across several fields at once",
                 "एक साथ कई क्षेत्रों में बँटा हुआ परिश्रम"),
    "Y.DAMINI": ("wide-spread activity — the method describes many interests at once",
                 "विस्तृत सक्रियता — यह पद्धति एक साथ अनेक रुचियों का वर्णन करती है"),
    "Y.PASA": ("a busy, entangled pattern — described as much to manage at once",
               "व्यस्त, उलझा हुआ स्वरूप — एक साथ बहुत कुछ सँभालना बताया गया"),
    "Y.MALA": ("a strung-together pattern — described as comfort arriving in a series",
               "मालावत् स्वरूप — क्रमशः आता हुआ सुख बताया गया"),
    "Y.ARDHACHANDRA": ("a half-gathered pattern — described as recognition that builds",
                       "अर्धसंचित स्वरूप — क्रमशः बढ़ती पहचान बताई गई"),
    "Y.KUTA": ("a shut-in pattern — described as work done under constraint",
               "बंद स्वरूप — बंधन में किया गया काम बताया गया"),
    "Y.SULA": ("a sharp, concentrated pattern — described as force applied narrowly",
               "तीखा, केंद्रित स्वरूप — सीमित दिशा में लगाया गया बल"),
    "Y.SARPA": ("a difficult, coiled pattern — the method reads it as hardship to work "
                "through",
                "कठिन, कुंडलित स्वरूप — इसे पार करने योग्य कठिनाई के रूप में पढ़ा जाता है"),
    "Y.VEENA": ("everything in play at once — described as many-sided and artistic",
                "सब कुछ एक साथ सक्रिय — बहुमुखी और कलाप्रिय बताया गया"),
    "Y.SAMUDRA": ("a wide, even spread — described as broadly comfortable",
                  "विस्तृत, समान फैलाव — व्यापक रूप से सुखी बताया गया"),
    "Y.CHAPA": ("a drawn-bow pattern — described as effort held under tension",
                "धनुष-सा खिंचा स्वरूप — तनाव में सधा परिश्रम"),
    "Y.NAVA": ("a boat-shaped pattern — described as movement and travel",
               "नौका-सा स्वरूप — गति और यात्रा बताई गई"),
    "Y.SARADA": ("a settled, favourable arrangement of supports",
                 "आधारों की स्थिर, अनुकूल व्यवस्था"),
    "Y.SAKATA": ("fortune that rises and falls rather than holding level — the method reads "
                 "this as ups and downs to expect, not as a loss",
                 "भाग्य जो स्थिर रहने के बजाय चढ़ता-उतरता है — यह पद्धति इसे हानि नहीं, "
                 "उतार-चढ़ाव मानती है"),
    "Y.DARIDRA": ("a pattern the method counts as straitening — read as means being harder "
                  "to hold than to earn",
                  "एक स्वरूप जिसे यह पद्धति तंगी मानती है — कमाने से अधिक कठिन है सँभालना"),
    "Y.ASATYAVADI": ("a pattern the method associates with speaking loosely",
                     "एक स्वरूप जिसे यह पद्धति असंयत वाणी से जोड़ती है"),
    "Y.KEMADRUMA": ("the mind's significator standing without support on either side — the "
                    "method counts this a difficult pattern, and also names several ways it "
                    "is cancelled",
                    "मन के कारक का दोनों ओर बिना सहारे रहना — यह पद्धति इसे कठिन मानती है, और "
                    "इसके रद्द होने के कई प्रकार भी बताती है"),
    "Y.BRIHADBIJA": ("a pattern read as bearing on children",
                     "संतान से संबंधित माना जाने वाला स्वरूप"),
}

#: Said when a combination has no written gloss. Honest understatement beats invention.
_KIND_FALLBACK: dict[str, tuple[str, str]] = {
    "raja": ("a combination this method counts as lifting position and standing",
             "एक योग जिसे यह पद्धति पद और प्रतिष्ठा बढ़ाने वाला मानती है"),
    "dhana": ("a combination this method counts as supporting earning",
              "एक योग जिसे यह पद्धति अर्जन में सहायक मानती है"),
    "arishta": ("a combination this method counts as a difficulty to be aware of",
                "एक योग जिसे यह पद्धति ध्यान देने योग्य कठिनाई मानती है"),
    "lunar": ("a combination read from the mind's significator and its neighbours",
              "मन के कारक और उसके निकटवर्ती ग्रहों से पढ़ा जाने वाला योग"),
    "other": ("a named combination this chart carries",
              "इस कुंडली में उपस्थित एक नामित योग"),
}


@dataclass(frozen=True)
class PlainPeriod:
    """One stretch of time, said without any of the machinery that graded it."""
    from_label_en: str
    from_label_hi: str
    to_label_en: str
    to_label_hi: str
    is_now: bool
    strength_en: str
    strength_hi: str
    #: The matters the method calls live and reads well in this stretch.
    supportive_en: tuple[str, ...] = ()
    supportive_hi: tuple[str, ...] = ()
    #: The matters it calls live but reads as friction.
    strained_en: tuple[str, ...] = ()
    strained_hi: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlainCombination:
    """One named combination, its tone, what it means, and when its own stretch runs."""
    name: str
    tone: str                      # "supportive" | "difficult" | "mixed"
    tone_en: str
    tone_hi: str
    plain_en: str
    plain_hi: str
    when_en: str = ""
    when_hi: str = ""


@dataclass(frozen=True)
class ShortReading:
    """The short reading. Every field is prose or items in both languages, or empty."""
    opening_en: str
    opening_hi: str
    you_en: str
    you_hi: str
    strengths_en: tuple[str, ...]
    strengths_hi: tuple[str, ...]
    difficulties_en: tuple[str, ...]
    difficulties_hi: tuple[str, ...]
    mixed_en: tuple[str, ...]
    mixed_hi: tuple[str, ...]
    ahead_lead_en: str
    ahead_lead_hi: str
    periods: tuple[PlainPeriod, ...]
    combinations_lead_en: str
    combinations_lead_hi: str
    combinations: tuple[PlainCombination, ...] = ()
    unusual_en: str = ""
    unusual_hi: str = ""
    common_en: str = ""
    common_hi: str = ""
    caveat_en: str = ""
    caveat_hi: str = ""
    #: Always shown: the short reading is a VIEW, and a reader must be told the rest exists.
    more_en: str = ""
    more_hi: str = ""
    houses_used: tuple[int, ...] = field(default_factory=tuple)


def _month_year(jd: float) -> tuple[str, str]:
    import swisseph as swe
    y, m, _d, _h = swe.revjul(jd, swe.GREG_CAL)
    en, hi = _MONTH.get(int(m), ("", ""))
    return f"{en} {int(y)}", f"{hi} {int(y)}"


def _best_tier(activated: list[dict]) -> str:
    """The strongest grade any matter reaches in a stretch — how the stretch reads overall."""
    present = {str(a.get("tier") or "") for a in activated}
    for tier in _TIER_ORDER:
        if tier in present:
            return tier
    return ""


def _matters(activated: list[dict], tier: str, verdict: str) -> tuple[tuple[str, ...],
                                                                     tuple[str, ...]]:
    """The plain names of the matters lit at `tier` whose standing reading is `verdict`.

    Deduplicated and ordered by house so two runs of the same chart say the same thing in the
    same order — the report is a pure function of the chart and this is part of it.
    """
    houses = sorted({int(a["house"]) for a in activated
                     if a.get("tier") == tier and a.get("natal_verdict") == verdict
                     and int(a.get("house", 0)) in PLAIN_HOUSE})
    return (tuple(PLAIN_HOUSE[h][0] for h in houses),
            tuple(PLAIN_HOUSE[h][1] for h in houses))


def _periods(report: dict, *, ahead: int = 6) -> tuple[PlainPeriod, ...]:
    """The stretch running now and the ones after it, from the already-graded timeline.

    The grain is the sub-period, because that is the grain at which the timeline was graded;
    coarsening to the main period here would be a new judgment, which this module does not
    make. Bounded to `ahead` so a short reading stays short.
    """
    timeline = report.get("timeline") or []
    ref = float(((report.get("window") or {}).get("ref_jd")) or 0.0)
    if not timeline or not ref:
        return ()
    live = [p for p in timeline if float(p.get("end_jd", 0.0)) > ref]
    live.sort(key=lambda p: float(p.get("start_jd", 0.0)))
    out: list[PlainPeriod] = []
    for p in live[:ahead + 1]:
        activated = list(p.get("activated") or [])
        tier = _best_tier(activated)
        if not tier:
            continue
        sup_en, sup_hi = _matters(activated, tier, "favourable")
        str_en, str_hi = _matters(activated, tier, "afflicted")
        f_en, f_hi = _month_year(float(p["start_jd"]))
        t_en, t_hi = _month_year(float(p["end_jd"]))
        strength = _STRENGTH.get(tier, ("", ""))
        out.append(PlainPeriod(
            from_label_en=f_en, from_label_hi=f_hi, to_label_en=t_en, to_label_hi=t_hi,
            is_now=float(p.get("start_jd", 0.0)) <= ref < float(p.get("end_jd", 0.0)),
            strength_en=strength[0], strength_hi=strength[1],
            supportive_en=sup_en, supportive_hi=sup_hi,
            strained_en=str_en, strained_hi=str_hi))
    return tuple(out)


def _plain_name(name: str) -> str:
    """The combination's name with its technical qualifier removed.

    Several records disambiguate themselves in a parenthetical — "Raja Yoga (kendra-trikona
    lords associated)", "Raja Yoga (9th-10th lords exchanged or in each other's houses)" —
    and that parenthetical is exactly the vocabulary this reading exists to avoid. The name
    itself is a proper noun and stays; what it means is said underneath in plain words, so
    two rows sharing a label are still told apart by their own sentence.
    """
    return name.split(" (")[0].strip() or name


def _combinations(report: dict, *, limit: int = 8) -> tuple[PlainCombination, ...]:
    """The chart's named combinations in plain words, difficult ones first.

    Difficult first is deliberate and is NOT a scare tactic: a reader who skims a short
    reading should not have the one thing the method flags buried under six pleasant lines.
    The tone word is right there beside it, and the caveat closes the whole reading.
    """
    fired = list(report.get("yogas") or [])
    if not fired:
        return ()
    # when each combination's own lord next runs — the report already computed it
    when: dict[str, tuple[str, str]] = {}
    ref = float(((report.get("window") or {}).get("ref_jd")) or 0.0)
    for t in report.get("yoga_timing") or []:
        yid = str(t.get("yoga_id") or "")
        if not yid or yid in when or float(t.get("period_end_jd", 0.0)) <= ref:
            continue
        f_en, f_hi = _month_year(float(t["period_start_jd"]))
        t_en, t_hi = _month_year(float(t["period_end_jd"]))
        when[yid] = (f"its own stretch runs {f_en} to {t_en}",
                     f"इसका अपना दौर {f_hi} से {t_hi} तक चलता है")
    rank = {"difficult": 0, "mixed": 1, "supportive": 2}
    rows: list[PlainCombination] = []
    for y in fired:
        yid, kind = str(y.get("id") or ""), str(y.get("kind") or "other")
        tone, tone_en, tone_hi = _TONE.get(kind, _TONE["other"])
        plain = PLAIN_YOGA.get(yid) or _KIND_FALLBACK.get(kind) or _KIND_FALLBACK["other"]
        w_en, w_hi = when.get(yid, ("", ""))
        rows.append(PlainCombination(
            name=_plain_name(str(y.get("name") or yid)),
            tone=tone, tone_en=tone_en, tone_hi=tone_hi,
            plain_en=plain[0], plain_hi=plain[1], when_en=w_en, when_hi=w_hi))
    rows.sort(key=lambda r: (rank.get(r.tone, 1), r.name))
    return tuple(rows[:limit])


def build_short_reading(report: dict) -> Optional[ShortReading]:
    """The short reading, or None when the report is too sparse to summarise."""
    summary = build_simple_summary(report)
    if summary is None:
        return None
    periods = _periods(report)
    combinations = _combinations(report)

    ahead_en = ("What the method reads as coming, stretch by stretch. These are the parts of "
                "life it calls active in each — not a claim that any particular thing will "
                "happen:" if periods else "")
    ahead_hi = ("यह पद्धति आगे क्या पढ़ती है, दौर दर दौर। ये वे पक्ष हैं जिन्हें यह हर दौर में सक्रिय "
                "कहती है — यह दावा नहीं कि कोई विशेष बात होगी:" if periods else "")
    comb_en = ("The named combinations your chart carries. Each is a tendency the old method "
               "names, never a promise:" if combinations else "")
    comb_hi = ("आपकी कुंडली में उपस्थित नामित योग। हर एक पुरानी पद्धति द्वारा बताई गई प्रवृत्ति है, "
               "वादा नहीं:" if combinations else "")
    more_en = ("This is the short reading. The full reading says all of this at length, with "
               "the working shown and every source named — switch to it whenever you want "
               "more than the gist.")
    more_hi = ("यह संक्षिप्त फलादेश है। विस्तृत फलादेश यही सब पूरे विस्तार से कहता है — तर्क सहित और "
               "हर स्रोत के नाम के साथ। जब भी सार से अधिक चाहिए, उस पर चले जाइए।")

    # NOT summary.opening: that one says "everything below it is the same thing said in the
    # traditional way", which is true of a section sitting inside the full report and false
    # of a reading that IS the whole page. The wrong sentence would send a reader scrolling
    # for chapters that this view does not show.
    opening_en = ("The whole reading, in ordinary words. It says what this method makes of "
                  "your chart, what it reads as coming, and which of it is actually unusual "
                  "for you.")
    opening_hi = ("पूरा फलादेश, सामान्य शब्दों में। यह पद्धति आपकी कुंडली से क्या समझती है, आगे क्या "
                  "पढ़ती है, और उसमें से आपके लिए वास्तव में असामान्य क्या है।")

    return ShortReading(
        opening_en=opening_en, opening_hi=opening_hi,
        you_en=summary.you_en, you_hi=summary.you_hi,
        strengths_en=summary.good_items_en, strengths_hi=summary.good_items_hi,
        difficulties_en=summary.hard_items_en, difficulties_hi=summary.hard_items_hi,
        mixed_en=summary.mixed_items_en, mixed_hi=summary.mixed_items_hi,
        ahead_lead_en=ahead_en, ahead_lead_hi=ahead_hi,
        periods=periods,
        combinations_lead_en=comb_en, combinations_lead_hi=comb_hi,
        combinations=combinations,
        unusual_en=summary.unusual_en, unusual_hi=summary.unusual_hi,
        common_en=summary.common_en, common_hi=summary.common_hi,
        caveat_en=summary.caveat_en, caveat_hi=summary.caveat_hi,
        more_en=more_en, more_hi=more_hi,
        houses_used=tuple(sorted({*summary.good_houses, *summary.hard_houses,
                                  *summary.mixed_houses})),
    )


# ── renderers ───────────────────────────────────────────────────────────────────
# The short reading is a whole document in its own right, so it renders itself rather than
# borrowing the full report's section machinery. Both renderers take the LANGUAGE, because
# every string was composed in both and picking one is the only choice left to make.

def to_markdown(short: ShortReading, *, lang: str = "en") -> str:
    """The short reading as a standalone Markdown document."""
    hi = lang == "hi"

    def pick(en: str, h: str) -> str:
        return h if hi else en

    L: list[str] = [pick("# Your reading, in short", "# आपका फलादेश, संक्षेप में"), ""]
    L += [pick(short.opening_en, short.opening_hi), ""]
    if short.you_en:
        L += [pick(short.you_en, short.you_hi), ""]

    for title_en, title_hi, items in (
            ("What this reading calls favourable", "जिन्हें यह फलादेश अनुकूल कहता है",
             pick(short.strengths_en, short.strengths_hi)),
            ("What it calls difficult", "जिन्हें यह कठिन कहता है",
             pick(short.difficulties_en, short.difficulties_hi)),
            ("What it reads both ways", "जिन्हें यह दोनों तरह पढ़ता है",
             pick(short.mixed_en, short.mixed_hi))):
        if items:
            L += [f"## {pick(title_en, title_hi)}", ""]
            L += [f"- {x}" for x in items]
            L.append("")

    if short.periods:
        L += [f"## {pick('What is coming', 'आगे क्या है')}", "",
              pick(short.ahead_lead_en, short.ahead_lead_hi), ""]
        for p in short.periods:
            now = pick("  **— now**", "  **— अभी**") if p.is_now else ""
            L.append(f"### {pick(p.from_label_en, p.from_label_hi)} - "
                     f"{pick(p.to_label_en, p.to_label_hi)}{now}")
            L += ["", pick(p.strength_en, p.strength_hi).capitalize() + ".", ""]
            if p.supportive_en:
                L.append(pick("Running well:", "अच्छा चलता हुआ:"))
                L += [f"- {x}" for x in pick(p.supportive_en, p.supportive_hi)]
                L.append("")
            if p.strained_en:
                L.append(pick("Meeting friction:", "रुकावट का सामना:"))
                L += [f"- {x}" for x in pick(p.strained_en, p.strained_hi)]
                L.append("")

    if short.combinations:
        L += [f"## {pick('The combinations your chart carries', 'आपकी कुंडली के योग')}", "",
              pick(short.combinations_lead_en, short.combinations_lead_hi), ""]
        for c in short.combinations:
            L.append(f"- **{c.name}** ({pick(c.tone_en, c.tone_hi)}) - "
                     f"{pick(c.plain_en, c.plain_hi)}"
                     + (f"; {pick(c.when_en, c.when_hi)}" if c.when_en else ""))
        L.append("")

    for title_en, title_hi, en, h in (
            ("What is unusual here", "यहाँ असामान्य क्या है", short.unusual_en, short.unusual_hi),
            ("How much of this is true of everyone", "इसमें से कितना सबके लिए सच है",
             short.common_en, short.common_hi)):
        if en:
            L += [f"## {pick(title_en, title_hi)}", "", pick(en, h), ""]

    if short.caveat_en:
        L += ["---", "", f"_{pick(short.caveat_en, short.caveat_hi)}_", ""]
    if short.more_en:
        L += [f"_{pick(short.more_en, short.more_hi)}_", ""]
    return "\n".join(L)


def to_html(short: ShortReading, *, lang: str = "en", title: str = "") -> str:
    """The short reading as a self-contained HTML page — same content, same order."""
    import html as _html

    hi = lang == "hi"

    def pick(en, h):
        return h if hi else en

    def esc(text: str) -> str:
        return _html.escape(str(text))

    def ul(items) -> str:
        return "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"

    parts: list[str] = [
        f'<h1>{esc(title or pick("Your reading, in short", "आपका फलादेश, संक्षेप में"))}</h1>',
        f'<p class="lede">{esc(pick(short.opening_en, short.opening_hi))}</p>']
    if short.you_en:
        parts.append(f"<p>{esc(pick(short.you_en, short.you_hi))}</p>")

    for title_en, title_hi, items in (
            ("What this reading calls favourable", "जिन्हें यह फलादेश अनुकूल कहता है",
             pick(short.strengths_en, short.strengths_hi)),
            ("What it calls difficult", "जिन्हें यह कठिन कहता है",
             pick(short.difficulties_en, short.difficulties_hi)),
            ("What it reads both ways", "जिन्हें यह दोनों तरह पढ़ता है",
             pick(short.mixed_en, short.mixed_hi))):
        if items:
            parts.append(f"<h2>{esc(pick(title_en, title_hi))}</h2>{ul(items)}")

    if short.periods:
        parts.append(f'<h2>{esc(pick("What is coming", "आगे क्या है"))}</h2>'
                     f'<p class="lede">{esc(pick(short.ahead_lead_en, short.ahead_lead_hi))}</p>')
        for p in short.periods:
            badge = (f'<span class="now">{esc(pick("now", "अभी"))}</span>' if p.is_now else "")
            block = (f'<h3>{esc(pick(p.from_label_en, p.from_label_hi))} &ndash; '
                     f'{esc(pick(p.to_label_en, p.to_label_hi))}{badge}</h3>'
                     f'<p>{esc(pick(p.strength_en, p.strength_hi).capitalize())}.</p>')
            if p.supportive_en:
                block += (f'<p class="lede">{esc(pick("Running well:", "अच्छा चलता हुआ:"))}</p>'
                          + ul(pick(p.supportive_en, p.supportive_hi)))
            if p.strained_en:
                block += (f'<p class="lede">'
                          f'{esc(pick("Meeting friction:", "रुकावट का सामना:"))}</p>'
                          + ul(pick(p.strained_en, p.strained_hi)))
            parts.append(f'<div class="period">{block}</div>')

    if short.combinations:
        rows = "".join(
            f'<li><b>{esc(c.name)}</b> <span class="tone {esc(c.tone)}">'
            f'{esc(pick(c.tone_en, c.tone_hi))}</span> &mdash; '
            f'{esc(pick(c.plain_en, c.plain_hi))}'
            + (f'; {esc(pick(c.when_en, c.when_hi))}' if c.when_en else "")
            + "</li>" for c in short.combinations)
        parts.append(
            f'<h2>{esc(pick("The combinations your chart carries", "आपकी कुंडली के योग"))}</h2>'
            f'<p class="lede">'
            f'{esc(pick(short.combinations_lead_en, short.combinations_lead_hi))}</p>'
            f"<ul>{rows}</ul>")

    for title_en, title_hi, en, h in (
            ("What is unusual here", "यहाँ असामान्य क्या है", short.unusual_en, short.unusual_hi),
            ("How much of this is true of everyone", "इसमें से कितना सबके लिए सच है",
             short.common_en, short.common_hi)):
        if en:
            parts.append(f"<h2>{esc(pick(title_en, title_hi))}</h2><p>{esc(pick(en, h))}</p>")

    if short.caveat_en:
        parts.append(f'<hr><p class="caveat">{esc(pick(short.caveat_en, short.caveat_hi))}</p>')
    if short.more_en:
        parts.append(f'<p class="caveat">{esc(pick(short.more_en, short.more_hi))}</p>')

    body = "".join(parts)
    css = ("body{max-width:44rem;margin:2.5rem auto;padding:0 1.2rem;line-height:1.7;"
           "font-family:Georgia,'EB Garamond',serif;color:#2b2118;background:#fbf7ef}"
           "h1{font-size:1.7rem;margin-bottom:.2rem}h2{font-size:1.15rem;margin-top:2rem;"
           "border-bottom:1px solid #e0d5c2;padding-bottom:.2rem}h3{font-size:1rem;"
           "margin:1.2rem 0 .2rem}.lede{color:#6b5c48}.period{margin:.2rem 0 1rem}"
           ".now{background:#7a5c2e;color:#fbf7ef;font-size:.7rem;border-radius:3px;"
           "padding:.05rem .4rem;margin-left:.5rem;vertical-align:middle}"
           ".tone{font-size:.72rem;border-radius:3px;padding:0 .35rem;background:#efe6d6}"
           ".tone.difficult{background:#f0d8d2}.tone.supportive{background:#dbe8d8}"
           ".caveat{color:#6b5c48;font-size:.9rem;font-style:italic}"
           "ul{margin:.2rem 0 .6rem}"
           "@media(prefers-color-scheme:dark){body{background:#17130e;color:#e8ddcb}"
           "h2{border-color:#3a3026}.lede,.caveat{color:#a8977e}"
           ".tone{background:#2e2619}.tone.difficult{background:#442a24}"
           ".tone.supportive{background:#26361f}}")
    return (f'<!doctype html><html lang="{"hi" if hi else "en"}"><head>'
            f'<meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1">'
            f'<title>{esc(title or "Your reading, in short")}</title>'
            f"<style>{css}</style></head><body>{body}</body></html>")
