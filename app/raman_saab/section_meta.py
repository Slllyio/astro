"""Per-section plain-language metadata for the report's reader-facing surfaces.

Every section of the detailed report keeps its doctrine-first heading (the
SECTION_CONTRACT marker strings are test-frozen and load-bearing); this module
supplies the ADDITIVE layer beneath each heading: a plain-language subtitle, the
reader's question the section answers, the guided-reading step it belongs to
(``interpretation_guide.reading_order`` steps 1-5), and the ``/report/explain``
scope key. Sanskrit-first, plain-subtitle-underneath is a user decision
(2026-08-17); so is English+Hindi in the same pass.

Charter boundaries (do not blur):
- ``plain_terms.TERM_GLOSS`` stays the ONE vocabulary glossary every surface
  renders from — the page's canonical glossary. The older prose ``GLOSSARY`` in
  ``detailed_report.py`` remains a markdown/standalone-only reference; it is NOT
  shipped to the interactive page.
- This module carries NO astrology: subtitles describe what a section examines,
  never a verdict. Every English string must pass the report-explainer
  ``_FORBIDDEN_RE`` decree/forecast guard (pinned by test) — descriptive idiom
  only, no future life-event assertions, no dated indications. The maraka /
  longevity / arishta wording keeps the standing "method, not a prediction"
  framing.

Keys are SECTION_CONTRACT section ids, plus the small page-only set
(``_PAGE_ONLY_IDS``) for surfaces the interactive page renders that are not
contract rows (Muhurtha panel, plain-terms chip cloud, testimony-support meter).

Usage: chart-independent, like ``INTERPRETATION_GUIDE`` — shipped whole under the
``section_meta`` key of the report JSON (``report_json.to_report_dict``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional


@dataclass(frozen=True)
class SectionMeta:
    subtitle_en: str            # plain-language subtitle rendered UNDER the pinned heading
    subtitle_hi: str
    answers_en: str             # one line: the reader's question this section answers
    answers_hi: str
    step: int                   # 1..5 = interpretation_guide.reading_order; 0 = data/appendix
    explain_scope: Optional[str] = None   # /report/explain scope key, e.g. "section:marriage"


#: Interactive-page surfaces that are not SECTION_CONTRACT rows.
_PAGE_ONLY_IDS: Final[frozenset[str]] = frozenset(
    {"muhurtha", "plain_terms_panel", "testimony_support"})


SECTION_META: Final[dict[str, SectionMeta]] = {
    # ── Step 1 — "What does this chart say, in plain English?" ────────────────
    "title": SectionMeta(
        "Your birth details, and the two voices this report speaks in",
        "आपके जन्म-विवरण, और वे दो स्वर जिनमें यह रिपोर्ट बोलती है",
        "Whose chart is this, cast how?",
        "यह कुंडली किसकी है, और कैसे बनाई गई?",
        1),
    "plain_reading": SectionMeta(
        "The whole reading in everyday words — start here",
        "पूरा पाठ सरल शब्दों में — यहीं से शुरू करें",
        "What does this chart say, in plain English?",
        "यह कुंडली सीधी-सरल भाषा में क्या कहती है?",
        1, "summary"),
    "digest": SectionMeta(
        "The strongest signals in this chart, ranked — each links to its full section",
        "इस कुंडली के सबसे प्रबल संकेत, क्रमानुसार — हर एक अपने पूर्ण खंड से जुड़ा",
        "If I read only ten things, which ten?",
        "अगर मैं केवल दस बातें पढ़ूँ, तो कौन-सी दस?",
        1),
    "interpretation_guide": SectionMeta(
        "How the sections fit together, and which reading governs when two differ",
        "खंड आपस में कैसे जुड़ते हैं, और दो पाठ भिन्न हों तो कौन-सा मान्य है",
        "In what order should I read, and how do I reconcile differences?",
        "किस क्रम में पढ़ूँ, और अंतर दिखे तो कैसे मिलाऊँ?",
        1),
    "glossary": SectionMeta(
        "Every technical term used in this report, defined in plain words",
        "इस रिपोर्ट का हर पारिभाषिक शब्द, सरल शब्दों में परिभाषित",
        "What does this word mean?",
        "इस शब्द का अर्थ क्या है?",
        1),

    # ── Step 2 — "Is THIS matter favourable?" ─────────────────────────────────
    "dashboard": SectionMeta(
        "All twelve life-areas on one card — the verdict, and what testifies to it",
        "जीवन के बारहों क्षेत्र एक पत्रक पर — निर्णय, और उसके साक्ष्य",
        "Which of my life-areas read favourable, mixed, or afflicted?",
        "मेरे किन क्षेत्रों का पाठ शुभ, मिश्रित या पीड़ित है?",
        2, "section:dashboard"),
    "marriage": SectionMeta(
        "The marriage chapter: 7th house, Venus, Navamsa and Upapada read together",
        "विवाह अध्याय: सप्तम भाव, शुक्र, नवांश और उपपद का समग्र पाठ",
        "What does the chart examine for married life?",
        "विवाहित जीवन के लिए कुंडली क्या-क्या परखती है?",
        2, "section:marriage"),
    "children": SectionMeta(
        "The children chapter: 5th house, its lord, Jupiter and the Saptamsa (D-7)",
        "संतान अध्याय: पंचम भाव, उसका स्वामी, गुरु और सप्तांश (D-7)",
        "What does the chart examine about children?",
        "संतान के विषय में कुंडली क्या परखती है?",
        2, "section:children"),
    "profession": SectionMeta(
        "The work chapter: the 10th house family, its lords, and converging career signals",
        "कर्म अध्याय: दशम भाव परिवार, उसके स्वामी, और मिलते हुए करियर-संकेत",
        "Where do the career indications converge?",
        "करियर के संकेत कहाँ मिलते हैं?",
        2, "section:profession"),
    "career": SectionMeta(
        "Raman's specific career pointer: the navamsa-dispositor of the 10th lord",
        "रामन का विशेष करियर-सूत्र: दशमेश के नवांश-अधिपति से",
        "What single technique does Raman give for vocation?",
        "व्यवसाय के लिए रामन की एक विशिष्ट विधि क्या है?",
        2),
    "wealth": SectionMeta(
        "The wealth chapter: 2nd and 11th houses and every earning channel the chart shows",
        "धन अध्याय: द्वितीय व एकादश भाव, और अर्जन के सभी मार्ग जो कुंडली दिखाती है",
        "Through which channels does the chart show gains and holdings?",
        "लाभ और संचय किन मार्गों से दिखते हैं?",
        2, "section:wealth"),
    "aptitude": SectionMeta(
        "Aptitude and mind: intellect (Mercury), the Moon's mind, and working style",
        "योग्यता और मन: बुद्धि (बुध), चन्द्र-मन, और कार्यशैली",
        "How does this chart describe my thinking and working style?",
        "यह कुंडली मेरी सोच और कार्यशैली को कैसे पढ़ती है?",
        2, "section:aptitude"),
    "psych": SectionMeta(
        "The inner portrait: temperament woven from the Moon, Mercury and the Atmakaraka",
        "आंतरिक चित्र: चन्द्र, बुध और आत्मकारक से बुना स्वभाव",
        "What temperament does the chart describe?",
        "कुंडली किस स्वभाव का वर्णन करती है?",
        2, "section:psych"),
    "longevity": SectionMeta(
        "The classical span computation — a method Raman teaches, not a prediction",
        "आयु की शास्त्रीय गणना — रामन की सिखाई विधि, भविष्यवाणी नहीं",
        "How does the classical Ayurdaya method grade this chart's span class?",
        "शास्त्रीय आयुर्दाय विधि इस कुंडली का आयु-वर्ग कैसे आँकती है?",
        2),
    "maraka": SectionMeta(
        "Which planets classical doctrine designates as determinants — method, not a prediction",
        "शास्त्र किन ग्रहों को मारक-निर्धारक कहता है — विधि मात्र, भविष्यवाणी नहीं",
        "Which planets does the doctrine mark, and why?",
        "शास्त्र किन ग्रहों को चिह्नित करता है, और क्यों?",
        2),
    "maraka_saturn": SectionMeta(
        "Where the designated periods and Saturn's transit overlap — shown as method only",
        "निर्धारित दशाएँ और शनि-गोचर जहाँ मिलते हैं — केवल विधि रूप में",
        "Which period-transit overlaps does the doctrine flag?",
        "शास्त्र किन दशा-गोचर संयोगों को चिह्नित करता है?",
        2),
    "health_readout": SectionMeta(
        "Body areas the chart marks for care, from the 6th house and the D-30",
        "षष्ठ भाव और त्रिंशांश (D-30) से, देह के वे अंग जिन पर ध्यान कहा गया है",
        "Which body areas does the chart mark for attention?",
        "कुंडली किन अंगों पर ध्यान देने को कहती है?",
        2, "section:health_readout"),
    "arishta": SectionMeta(
        "Classical danger-combinations found — and the cancellations that answer them",
        "पाई गई शास्त्रीय अरिष्ट-योजनाएँ — और उनके उत्तर में भंग (निरसन)",
        "Which afflicting combinations fire, and what cancels them?",
        "कौन-से अरिष्ट सक्रिय हैं, और उन्हें क्या भंग करता है?",
        2, "section:arishta"),

    # ── Step 3 — "How much of that is about ME?" ──────────────────────────────
    "info_content": SectionMeta(
        "How specific this reading is to you, measured against thousands of charts",
        "हज़ारों कुंडलियों की तुलना में यह पाठ आपके लिए कितना विशिष्ट है",
        "How much of this reading is about me, not everyone?",
        "इस पाठ में कितना केवल मेरे लिए है, सबके लिए नहीं?",
        3, "section:info"),
    "stands_out": SectionMeta(
        "Where your chart is genuinely unusual against the population",
        "जनसमूह की तुलना में आपकी कुंडली वास्तव में कहाँ असामान्य है",
        "What is rare in my chart?",
        "मेरी कुंडली में दुर्लभ क्या है?",
        3, "section:distinctive"),
    "rect_confidence": SectionMeta(
        "How sensitive this reading is to small birth-time error, pillar by pillar",
        "जन्म-समय की थोड़ी त्रुटि से यह पाठ कितना बदलता है, स्तम्भ-दर-स्तम्भ",
        "If my birth time is slightly off, what still holds?",
        "यदि जन्म-समय थोड़ा भिन्न हो, तो क्या फिर भी टिकता है?",
        3, "section:rect_confidence"),

    # ── Step 4 — "WHY does it read that way?" ─────────────────────────────────
    "judgment_graph": SectionMeta(
        "Every planet-to-house influence in one picture — the reading's working parts",
        "हर ग्रह-भाव प्रभाव एक चित्र में — इस पाठ के कार्यरत पुर्ज़े",
        "What shapes each area of my life, mechanically?",
        "मेरे जीवन के हर क्षेत्र को यंत्रवत् क्या गढ़ता है?",
        4),
    "chart_signature": SectionMeta(
        "Your chart's identity card: ascendant, Moon's star, soul-planet, running period",
        "कुंडली का परिचय-पत्र: लग्न, चन्द्र-नक्षत्र, आत्मकारक, चालू दशा",
        "What are this chart's defining coordinates?",
        "इस कुंडली के निर्धारक बिंदु क्या हैं?",
        4, "section:synthesis"),
    "ruler": SectionMeta(
        "The planet that owns your ascendant — and the strongest planet, compared",
        "लग्न का स्वामी ग्रह — और बलतम ग्रह, तुलना सहित",
        "Which planet leads this nativity, and by what measure?",
        "इस जन्मपत्री का नेतृत्व कौन-सा ग्रह करता है, किस मापदंड से?",
        4, "section:ruler"),
    "planet_bios": SectionMeta(
        "A biography of each dominant planet: what it touches, quotes from Raman included",
        "प्रत्येक प्रमुख ग्रह की जीवनी: वह क्या-क्या छूता है, रामन के उद्धरण सहित",
        "What does each major planet do across my whole chart?",
        "प्रत्येक प्रमुख ग्रह मेरी पूरी कुंडली में क्या करता है?",
        4, "section:planet_bios"),
    "now_box": SectionMeta(
        "Where you are right now: the running major and sub-period",
        "आप अभी कहाँ हैं: चालू महादशा और अन्तर्दशा",
        "Which period am I in today?",
        "आज मैं किस दशा में हूँ?",
        5),
    "chart_grids": SectionMeta(
        "The charts themselves: birth chart (Rasi), the ninth division (Navamsa), today's sky",
        "स्वयं कुंडलियाँ: जन्म (राशि), नवम विभाजन (नवांश), आज का आकाश",
        "What do the actual chart diagrams look like?",
        "वास्तविक कुंडली-चित्र कैसे दिखते हैं?",
        4),
    "positions": SectionMeta(
        "Exact degrees, stars and divisional placements for every planet",
        "हर ग्रह के सटीक अंश, नक्षत्र और वर्ग-स्थितियाँ",
        "Where exactly does each planet sit?",
        "प्रत्येक ग्रह ठीक कहाँ बैठा है?",
        4),
    "shadbala": SectionMeta(
        "Six-fold strength: each planet's measured power in rupas, six components",
        "षड्बल: छह घटकों में, रूप में मापी गई प्रत्येक ग्रह की शक्ति",
        "How strong is each planet, by the classical measure?",
        "शास्त्रीय माप से प्रत्येक ग्रह कितना बलवान है?",
        4),
    "yogas": SectionMeta(
        "Named planetary combinations present in this chart, each with its source line",
        "इस कुंडली में विद्यमान नामांकित ग्रह-योग, प्रत्येक अपने स्रोत सहित",
        "Which classical combinations does my chart carry?",
        "मेरी कुंडली में कौन-से शास्त्रीय योग हैं?",
        4, "section:yogas"),
    "yoga_timing": SectionMeta(
        "When each combination's period arrives — a yoga delivers in its lords' dashas",
        "प्रत्येक योग की दशा कब आती है — योग अपने स्वामियों की दशा में फल देता है",
        "When does each yoga's operating period run?",
        "प्रत्येक योग की सक्रिय अवधि कब चलती है?",
        5),
    "yoga_deep": SectionMeta(
        "Each yoga studied in full: definition, your chart's version, cancellations",
        "हर योग का पूर्ण अध्ययन: परिभाषा, आपकी कुंडली का रूप, भंग-नियम",
        "What exactly does each of my yogas mean, per the texts?",
        "ग्रंथों के अनुसार मेरे प्रत्येक योग का ठीक अर्थ क्या है?",
        4),
    "ashtakavarga": SectionMeta(
        "The benefic-point grid: each sign's score out of 56, used to grade transits",
        "बिन्दु-सारणी: प्रत्येक राशि का 56 में स्कोर, गोचर आँकने के काम आता है",
        "Which signs are strong or lean for me, by points?",
        "बिन्दुओं के अनुसार मेरे लिए कौन-सी राशियाँ सबल या दुर्बल हैं?",
        4),
    "houses": SectionMeta(
        "All twelve houses judged one by one, with every testimony shown",
        "बारहों भावों का एक-एक कर निर्णय, प्रत्येक साक्ष्य सहित",
        "How is each house judged, and on what evidence?",
        "प्रत्येक भाव का निर्णय कैसे और किन प्रमाणों पर हुआ?",
        4, "section:proformas"),
    "house_strength": SectionMeta(
        "A second opinion on the houses from two independent strength measures",
        "दो स्वतंत्र बल-मापों से भावों पर दूसरा मत",
        "Do the strength numbers agree with the house verdicts?",
        "क्या बल-गणनाएँ भाव-निर्णयों से मेल खाती हैं?",
        4),
    "preponderance": SectionMeta(
        "Where the testimonies pile up — for, against, contested, or silent, per house",
        "साक्ष्य कहाँ इकट्ठा होते हैं — पक्ष, विपक्ष, विवादित या मौन, प्रति भाव",
        "Which houses have the weightiest evidence either way?",
        "किन भावों में किसी भी ओर सबसे भारी प्रमाण हैं?",
        4, "section:preponderance"),
    "deeptadi": SectionMeta(
        "Each planet's mood-state (radiant, dejected, …) and what that does to its results",
        "प्रत्येक ग्रह की अवस्था (दीप्त, दीन, …) और उसके फल पर प्रभाव",
        "In what state does each planet operate here?",
        "यहाँ प्रत्येक ग्रह किस अवस्था में कार्य करता है?",
        4),
    "divisional": SectionMeta(
        "The sixteen divisional charts, each read for its own domain of life",
        "सोलह वर्ग-कुंडलियाँ, प्रत्येक अपने जीवन-क्षेत्र के लिए पढ़ी गई",
        "What do the finer divisional charts add?",
        "सूक्ष्म वर्ग-कुंडलियाँ क्या जोड़ती हैं?",
        4, "section:divisional"),
    "karakamsa": SectionMeta(
        "The soul-planet's Navamsa seat — Jaimini's window on inclination",
        "आत्मकारक का नवांश-आसन — प्रवृत्ति पर जैमिनी की दृष्टि",
        "What does the soul-planet's seat incline this life toward?",
        "आत्मकारक का आसन इस जीवन को किस ओर झुकाता है?",
        4),
    "soul": SectionMeta(
        "The extended Jaimini reading: soul-planet, Karakamsa and Arudha in full",
        "विस्तृत जैमिनी पाठ: आत्मकारक, कारकांश और आरूढ़ सम्पूर्ण",
        "What does the Jaimini system say about purpose and image?",
        "उद्देश्य और छवि पर जैमिनी पद्धति क्या कहती है?",
        4, "section:soul"),
    "karmic": SectionMeta(
        "The karmic-evolution layer: where the soul has come from and is pointed",
        "कार्मिक-विकास परत: आत्मा कहाँ से आई और किस ओर उन्मुख है",
        "What karmic arc do the Jaimini points sketch?",
        "जैमिनी बिंदु कौन-सा कार्मिक चाप रेखांकित करते हैं?",
        4, "section:karmic"),
    "pitru": SectionMeta(
        "The classical ancestral-affliction screen — clearly labelled non-Raman doctrine",
        "शास्त्रीय पितृ-दोष जाँच — स्पष्टतः गैर-रामन स्रोत के रूप में अंकित",
        "Does the classical screen find ancestral-line afflictions?",
        "क्या शास्त्रीय जाँच में पितृ-रेखा दोष मिलते हैं?",
        4, "section:pitru"),
    "synthesis": SectionMeta(
        "Cross-cutting insights: where separate features of the chart reinforce each other",
        "आर-पार अंतर्दृष्टियाँ: कुंडली के अलग-अलग लक्षण जहाँ एक-दूसरे को पुष्ट करते हैं",
        "Which findings reinforce each other across sections?",
        "कौन-से निष्कर्ष खंडों के आर-पार एक-दूसरे को पुष्ट करते हैं?",
        4, "section:insights"),
    "life_synthesis": SectionMeta(
        "The whole chart woven into one continuous portrait, theme by theme",
        "पूरी कुंडली एक सतत चित्र में बुनी हुई, विषय-दर-विषय",
        "Read as one story, what portrait emerges?",
        "एक कथा की तरह पढ़ें तो कौन-सा चित्र उभरता है?",
        4, "section:life_synthesis"),

    # ── Step 5 — "WHEN?" ──────────────────────────────────────────────────────
    "timeline": SectionMeta(
        "Your period timeline: every major and sub-period, graded by Raman's four tiers",
        "आपकी दशा-रेखा: प्रत्येक महादशा व अन्तर्दशा, रामन के चार स्तरों से आँकी",
        "Which periods carry which indications, and how strongly?",
        "कौन-सी दशाएँ कौन-से संकेत रखती हैं, कितनी प्रबलता से?",
        5, "section:timeline"),
    "ishta_kashta": SectionMeta(
        "Each period-lord's benefic/malefic balance — a lean, not a verdict",
        "प्रत्येक दशेश का इष्ट/कष्ट संतुलन — झुकाव मात्र, निर्णय नहीं",
        "Which way does each period-lord lean by this measure?",
        "इस माप से प्रत्येक दशेश किस ओर झुकता है?",
        5),
    "md_condition": SectionMeta(
        "The condition each major-period lord is in — strength, division, state",
        "प्रत्येक महादशेश की स्थिति — बल, वर्ग, अवस्था",
        "How well-placed is each period's lord?",
        "प्रत्येक दशा का स्वामी कितनी अच्छी स्थिति में है?",
        5),
    "av_dasha_seat": SectionMeta(
        "Each period-lord's benefic-point seat — the sign score behind its period",
        "प्रत्येक दशेश का बिन्दु-आसन — उसकी दशा के पीछे का राशि-स्कोर",
        "What point-support does each period sit on?",
        "प्रत्येक दशा किस बिन्दु-आधार पर टिकी है?",
        5),
    "dasa_kakshya": SectionMeta(
        "The finest sub-division of the running period, interval by interval",
        "चालू दशा का सूक्ष्मतम विभाजन, अंतराल-दर-अंतराल",
        "How does the running period subdivide, precisely?",
        "चालू दशा सूक्ष्मतः कैसे विभाजित होती है?",
        5),
    "life_chapters": SectionMeta(
        "Each major period written as a chapter of the life it colours",
        "प्रत्येक महादशा, उस जीवन-अध्याय के रूप में जिसे वह रँगती है",
        "What does each era of my timeline emphasize?",
        "मेरी समय-रेखा का प्रत्येक युग किस पर बल देता है?",
        5),
    "decades": SectionMeta(
        "Decade by decade: the indications active in each ten-year span",
        "दशक-दर-दशक: प्रत्येक दस-वर्ष में सक्रिय संकेत",
        "Which indications colour each decade?",
        "प्रत्येक दशक को कौन-से संकेत रँगते हैं?",
        5, "section:decades"),
    "gochara": SectionMeta(
        "Today's sky against your chart: current transits with the classical veto check",
        "आपकी कुंडली पर आज का आकाश: वर्तमान गोचर, शास्त्रीय वेध-जाँच सहित",
        "What are the planets doing for me right now?",
        "ग्रह इस समय मेरे लिए क्या कर रहे हैं?",
        5, "section:gochara"),
    "dasha_transit": SectionMeta(
        "Where the running period and today's transits point the same way",
        "जहाँ चालू दशा और आज के गोचर एक ही दिशा में संकेत करते हैं",
        "Do period and transit agree anywhere right now?",
        "क्या दशा और गोचर अभी कहीं सहमत हैं?",
        5),

    # ── Colophon ──────────────────────────────────────────────────────────────
    "nichod": SectionMeta(
        "The essence — the whole reading distilled to its final paragraph",
        "निचोड़ — पूरा पाठ अपने अंतिम अनुच्छेद में सारित",
        "If everything above were one paragraph, what is it?",
        "ऊपर का सब कुछ एक अनुच्छेद हो, तो वह क्या है?",
        1, "section:nichod"),

    # ── Page-only surfaces ────────────────────────────────────────────────────
    "muhurtha": SectionMeta(
        "Electional method applied to today — quality of the day, as method only",
        "आज पर मुहूर्त-विधि — दिन की गुणवत्ता, केवल विधि रूप में",
        "How does the classical day-quality method read today?",
        "शास्त्रीय मुहूर्त-विधि आज को कैसे पढ़ती है?",
        5),
    "plain_terms_panel": SectionMeta(
        "Tap any term for its plain meaning, an analogy, and why it matters",
        "किसी भी शब्द को छुएँ — सरल अर्थ, उपमा, और महत्व",
        "What do the technical words mean?",
        "पारिभाषिक शब्दों का अर्थ क्या है?",
        1),
    "testimony_support": SectionMeta(
        "How much independent evidence backs each house's verdict",
        "प्रत्येक भाव-निर्णय के पीछे कितना स्वतंत्र प्रमाण है",
        "How well-supported is each verdict?",
        "प्रत्येक निर्णय कितना समर्थित है?",
        4),
}


def section_meta_json() -> dict[str, dict]:
    """The full metadata map as JSON-ready dicts (chart-independent)."""
    return {
        sid: {
            "subtitle_en": m.subtitle_en, "subtitle_hi": m.subtitle_hi,
            "answers_en": m.answers_en, "answers_hi": m.answers_hi,
            "step": m.step, "explain_scope": m.explain_scope,
        }
        for sid, m in SECTION_META.items()
    }
