"""Chart-specific feedback questions — derived from the engine's own ranked digest.

After a person reads their chart, we ask a handful of questions ABOUT THAT CHART — "your
chart points to a positive time for your income and friendships; does that match your
experience?" — and store the answers (`ChartFeedback` rows via POST /report/feedback). The
questions are a pure, deterministic re-read of the already-computed report JSON: the digest's
ranked items (convergence / timing / distinctive) plus one overall question. No LLM, no new
judgment.

Wording (locked 2026-07-29, after real feedback: "too complicated for common user to
understand even feedback question"): questions are built from a plain, everyday phrase per
house — never by quoting the digest's own technical title ("House 4 (home & mother) is the
most strongly corroborated favourable area") — so a reader with no astrology background can
answer without decoding jargon. `lang="hi"` renders the same questions in Hindi.

Honesty frame (Measured Truth): these are CALIBRATION questions about whether a reading
matched an experience — feedback for the project — never a claim that the engine predicts
lives. The wording keeps that explicit in both languages.

Usage:
    from app.raman_saab.feedback_questions import build_feedback_questions
    qs = build_feedback_questions(report_dict)             # English
    qs = build_feedback_questions(report_dict, lang="hi")  # Hindi
    # -> list[dict]: {qid, kind, text, houses, options, allow_free_text}
"""
from __future__ import annotations

from typing import Any, Literal

#: the fixed answer scale for every question (the frontend renders these as buttons, in
#: whichever language it's showing; the POST endpoint validates against these ENGLISH values
#: regardless of display language, so stored answers stay comparable across languages).
ANSWER_OPTIONS: tuple[str, ...] = ("agree", "partly", "disagree", "not sure")

#: digest kinds that make good askable questions. `tension` items are the engine explicitly
#: NOT resolving a direction, and `dominant_theme` insights are connective — neither maps to
#: a clean "does this match your experience?".
_ASKABLE_KINDS: frozenset[str] = frozenset({"convergence", "timing", "distinctive"})

#: leans a person can meaningfully confirm or deny. "mixed"/"neutral" readings do not assert
#: a direction, so asking "does this match?" would be unanswerable.
_ASKABLE_LEANS: frozenset[str] = frozenset({"favourable", "adverse"})

Lang = Literal["en", "hi"]

#: A plain, everyday phrase per house — what a common reader would actually call that part of
#: life, not the report's own technical shorthand ("home & mother", "loss & liberation").
#: Built FROM the house number alone so question text never has to quote (and thus never
#: leaks) the digest's denser technical title string.
_HOUSE_TOPIC_EN: dict[int, str] = {
    1: "your health and general energy",
    2: "your finances and family wealth",
    3: "your courage and relationship with siblings",
    4: "your home life and your mother",
    5: "your children and creative pursuits",
    6: "health troubles, debts, or rivals",
    7: "your marriage or a close partnership",
    8: "a major change or difficult transition in life",
    9: "your luck, higher learning, and your father",
    10: "your career and public standing",
    11: "your income, gains, and friendships",
    12: "expenses, losses, or your spiritual side",
}

_HOUSE_TOPIC_HI: dict[int, str] = {
    1: "आपके स्वास्थ्य और ऊर्जा",
    2: "आपके धन और पारिवारिक संपत्ति",
    3: "आपके साहस और भाई-बहनों से संबंध",
    4: "आपके घर-परिवार और माता से संबंध",
    5: "आपकी संतान और रचनात्मक रुचियों",
    6: "स्वास्थ्य संबंधी परेशानियों, कर्ज़, या शत्रुओं",
    7: "आपके विवाह या किसी करीबी साझेदारी",
    8: "जीवन में किसी बड़े बदलाव या कठिन दौर",
    9: "आपके भाग्य, उच्च शिक्षा, और पिता से संबंध",
    10: "आपके करियर और सामाजिक प्रतिष्ठा",
    11: "आपकी आय, लाभ, और मित्रता",
    12: "खर्च, हानि, या आपके आध्यात्मिक पक्ष",
}

#: A "timing" item can legitimately span most or all 12 houses at once — a broad dasha/bhukti
#: touching many life areas simultaneously is expected, not a bug (see CLAUDE.md's Measured
#: Truth note: "the median chart carries 19 afflicted AND 31 favourable significations
#: simultaneously"). Naming every one in a single sentence is unreadable, so past this many
#: houses we name the theme generically instead of chaining every topic (locked 2026-07-29,
#: same "too complicated" feedback pass that prompted this file's plain-language rewrite).
_MAX_NAMED_TIMING_TOPICS = 3

_GENERIC_TIMING_TOPIC: dict[Lang, str] = {
    "en": "many different areas of your life right now",
    "hi": "अभी आपके जीवन के कई अलग-अलग पहलुओं",
}

_STRINGS: dict[Lang, dict[str, str]] = {
    "en": {
        "timing": "Right now your chart points to a period touching {topic} — overall, has "
                  "this recent time felt {word}?",
        "direction_favourable": "Your chart points to a generally positive time for {topic}. "
                                "Does that match your experience?",
        "direction_adverse": "Your chart points to a difficult or challenging time for "
                            "{topic}. Does that match your experience?",
        "lean_favourable": "positive",
        "lean_adverse": "difficult",
        "overall": ("Overall, how well did this reading match your life? (This helps us "
                   "check how accurate the method really is — it's a traditional reading, "
                   "not a scientific prediction.)"),
    },
    "hi": {
        "timing": "आपकी कुंडली के अनुसार अभी {topic} से जुड़ा एक दौर चल रहा है — कुल मिलाकर, "
                  "क्या यह हाल का समय आपको {word} लगा है?",
        "direction_favourable": "आपकी कुंडली {topic} के लिए सामान्यतः अच्छे समय की ओर इशारा करती है। "
                                "क्या यह आपके अनुभव से मेल खाता है?",
        "direction_adverse": "आपकी कुंडली {topic} के लिए एक कठिन या चुनौतीपूर्ण समय की ओर इशारा करती है। "
                            "क्या यह आपके अनुभव से मेल खाता है?",
        "lean_favourable": "अच्छा",
        "lean_adverse": "कठिन",
        "overall": ("कुल मिलाकर, यह रीडिंग आपके जीवन से कितनी मेल खाती है? (इससे हमें यह जांचने में "
                   "मदद मिलती है कि यह पारंपरिक पद्धति वास्तव में कितनी सटीक है — यह कोई वैज्ञानिक "
                   "भविष्यवाणी नहीं, एक पारंपरिक रीडिंग है।)"),
    },
}


def _slug(*parts: Any) -> str:
    """A stable, readable question id from its defining parts (stable per chart because the
    digest itself is deterministic for a chart) — independent of display language."""
    out = "-".join(str(p) for p in parts if p not in (None, "", ()))
    return out.lower().replace(" ", "_")[:80]


def _topic_for(houses: tuple[int, ...], lang: Lang, *, max_named: int | None = None) -> str | None:
    """A plain phrase covering the item's houses (almost always exactly one). When `max_named`
    is given and the item spans more houses than that, name the theme generically instead of
    chaining every house's topic into one unreadable sentence."""
    table = _HOUSE_TOPIC_HI if lang == "hi" else _HOUSE_TOPIC_EN
    phrases = [table[h] for h in houses if h in table]
    if not phrases:
        return None
    if max_named is not None and len(phrases) > max_named:
        return _GENERIC_TIMING_TOPIC[lang]
    joiner = " और " if lang == "hi" else " and "
    return joiner.join(phrases)


def _item_question(item: dict, position: int, lang: Lang) -> dict | None:
    """One digest item -> one plain-language question dict, or None when not askable."""
    kind = item.get("kind", "")
    lean = item.get("lean", "")
    if kind not in _ASKABLE_KINDS or lean not in _ASKABLE_LEANS:
        return None
    houses = tuple(item.get("houses") or ())
    max_named = _MAX_NAMED_TIMING_TOPICS if kind == "timing" else None
    topic = _topic_for(houses, lang, max_named=max_named)
    if topic is None:
        return None
    s = _STRINGS[lang]
    if kind == "timing":
        word = s["lean_favourable"] if lean == "favourable" else s["lean_adverse"]
        text = s["timing"].format(topic=topic, word=word)
    else:
        key = "direction_favourable" if lean == "favourable" else "direction_adverse"
        text = s[key].format(topic=topic)
    return {
        "qid": _slug(kind, "h" + "_".join(map(str, houses)) if houses else "chart", lean,
                     position),
        "kind": kind,
        "text": text,
        "houses": list(houses),
        "options": list(ANSWER_OPTIONS),
        "allow_free_text": True,
    }


def build_feedback_questions(report: dict, *, max_questions: int = 5,
                             lang: Lang = "en") -> list[dict]:
    """The chart-specific feedback questions for one report dict (``to_report_dict`` output),
    in plain everyday language (English or Hindi).

    Deterministic: the digest's ranked order decides which items are asked (first askable
    items win), and the final slot is always the overall-fit question. Returns at most
    ``max_questions`` questions. `qid`s are language-independent (built from house/kind/lean),
    so the same chart's questions keep the same ids in either language.
    """
    digest = report.get("digest") or {}
    items = digest.get("items") or []
    lang = lang if lang in _STRINGS else "en"

    questions: list[dict] = []
    for pos, item in enumerate(items):
        if len(questions) >= max_questions - 1:        # reserve the last slot for "overall"
            break
        q = _item_question(item, pos, lang)
        if q is not None:
            questions.append(q)

    questions.append({
        "qid": "overall",
        "kind": "overall",
        "text": _STRINGS[lang]["overall"],
        "houses": [],
        "options": list(ANSWER_OPTIONS),
        "allow_free_text": True,
    })
    return questions
