"""The Native Profile — "Who you are", before the life predictions.

Raman opens a judgement with the native's own make-up — temperament, mind, and
bent — and only then turns to events. This module builds that portrait as eight
concrete behavioural styles, each reasoned from the condition of its governing
graha (the exact `well_placed` rule and quality vocabulary the classical
narrative uses, shared via `_planet_lexicon`):

    decision_making   Sun   · will, resolve
    emotional         Moon  · mood, sensitivity
    leadership        Sun + Mars · authority, drive
    communication     Mercury · speech, reasoning
    risk_tolerance    Mars (+ Rahu) · daring vs caution
    learning          Mercury + Jupiter · intellect, wisdom
    financial         Jupiter + Venus · prudence vs indulgence
    relationship      Venus + Moon · warmth, harmony

Every line is a deterministic restatement of the planet's real condition
(dignity, composite, combustion) — nothing invented, no probability. A small
"clarity" figure reports how many of the governing grahas are well placed — an
internal-signal reading, honestly framed, never an outcome likelihood.
Fail-soft: any error yields an empty (or partial) profile.
"""
from __future__ import annotations

from typing import Any, Mapping

from app.reading._planet_lexicon import (
    PLANET_QUALITY,
    strength_index,
    well_placed,
)

_ORD = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th",
        7: "7th", 8: "8th", 9: "9th", 10: "10th", 11: "11th", 12: "12th"}

# Each style: its label, the governing graha(s), and three-way phrasings keyed
# on whether the primary graha is well placed / afflicted / mixed. {good} and
# {shadow} are the planet's own quality pair from the shared lexicon.
_STYLES: tuple[dict[str, Any], ...] = (
    {
        "key": "decision_making", "label": "Decision-making", "planet": "Sun",
        "well": "You decide with resolve and own the outcome — {good} lends a "
                "steady, self-directed will.",
        "afflicted": "Decisions can waver or over-assert; {shadow} intrudes, so "
                     "a deliberate pause before committing serves you.",
        "mixed": "You decide capably but not always firmly — a fair measure of "
                 "resolve, steadied by seeking a second view on the big calls.",
    },
    {
        "key": "emotional", "label": "Emotional style", "planet": "Moon",
        "well": "Emotionally you are settled and sympathetic — {good} gives an "
                "even keel others lean on.",
        "afflicted": "Moods run changeful; {shadow} can unsettle you, so "
                     "grounding routines and rest steady the inner weather.",
        "mixed": "Your feeling nature is responsive without being volatile — "
                 "generally contented, occasionally tender.",
    },
    {
        "key": "leadership", "label": "Leadership", "planet": "Sun",
        "second": "Mars",
        "well": "You lead naturally — {good}, carried by real drive, so people "
                "follow your direction.",
        "afflicted": "Authority is better earned than assumed here; {shadow} can "
                     "cost goodwill, so lead by example rather than command.",
        "mixed": "You can lead when it matters, blending initiative with "
                 "consultation rather than sheer command.",
    },
    {
        "key": "communication", "label": "Communication", "planet": "Mercury",
        "well": "You express yourself clearly and persuasively — {good} makes "
                "you articulate and quick on your feet.",
        "afflicted": "Thought and speech can outrun each other; {shadow} shows "
                     "as scattered expression — slow down and structure the point.",
        "mixed": "You communicate competently, sharp in your areas of interest "
                 "and more measured elsewhere.",
    },
    {
        "key": "risk_tolerance", "label": "Risk tolerance", "planet": "Mars",
        "second": "Rahu",
        "well": "You take bold, calculated risks — {good} gives the nerve to "
                "act while others hesitate.",
        "afflicted": "Risk-taking can turn rash or, in reaction, over-cautious; "
                     "{shadow} means pacing and clear limits pay off.",
        "mixed": "You are moderately venturesome — willing to move, but rarely "
                 "recklessly.",
    },
    {
        "key": "learning", "label": "Learning style", "planet": "Mercury",
        "second": "Jupiter",
        "well": "You learn quickly and connect ideas well — {good} suits study, "
                "analysis and self-teaching.",
        "afflicted": "Focus can wander; {shadow} means you learn best in short, "
                     "structured bursts with applied practice.",
        "mixed": "You learn steadily, strongest where curiosity and use meet.",
    },
    {
        "key": "financial", "label": "Financial behaviour", "planet": "Jupiter",
        "second": "Venus",
        "well": "You handle money with prudence and generosity — {good} favours "
                "steady building over speculation.",
        "afflicted": "Spending can run ahead of prudence; {shadow} means a "
                     "buffer and a plan protect you from the swings.",
        "mixed": "You manage money reasonably — prudent in the main, indulgent "
                 "in the areas you value.",
    },
    {
        "key": "relationship", "label": "Relationship style", "planet": "Venus",
        "second": "Moon",
        "well": "You bring warmth and harmony to close ties — {good} makes you "
                "affectionate and companionable.",
        "afflicted": "Closeness asks for care; {shadow} can strain harmony, so "
                     "clear, patient communication keeps bonds steady.",
        "mixed": "You relate warmly, valuing harmony while keeping your own "
                 "footing.",
    },
)


def _line(style: Mapping[str, Any],
          idx: Mapping[str, dict[str, Any]]) -> dict[str, Any] | None:
    """One behavioural-style line, reasoned from the governing graha's real
    condition. Returns None if the graha isn't in the strength table."""
    planet = style["planet"]
    row = idx.get(planet)
    if not row:
        return None
    good, shadow = PLANET_QUALITY.get(planet, ("", ""))
    w = well_placed(row.get("dignity"), row.get("composite"), bool(row.get("combust")))
    if w is True:
        text = style["well"].format(good=good, shadow=shadow)
        cond = "well placed"
    elif w is False:
        text = style["afflicted"].format(good=good, shadow=shadow)
        cond = "under strain"
    else:
        text = style["mixed"].format(good=good, shadow=shadow)
        cond = "mixed"
    house = row.get("house")
    gov = planet + (f" and {style['second']}" if style.get("second") else "")
    return {
        "key": style["key"],
        "label": style["label"],
        "governor": gov,
        "planet": planet,
        "planet_house": house,
        "planet_house_ord": _ORD.get(house) if house else None,
        "condition": cond,
        "well_placed": w,
        "text": text,
    }


def build_native_profile(reading: Mapping[str, Any],
                         extras: Mapping[str, Any]) -> dict[str, Any]:
    """The "Who you are" portrait — eight behavioural styles from the real
    planet-strength table, plus an honest internal-clarity figure. → {} on
    failure; a partial profile is preferred over none."""
    try:
        idx = strength_index(extras.get("planet_strength"))
        if not idx:
            return {}
        styles: list[dict[str, Any]] = []
        for spec in _STYLES:
            line = _line(spec, idx)
            if line:
                styles.append(line)
        if not styles:
            return {}
        # clarity = how many governing grahas show their higher nature — an
        # internal-signal reading, NOT a probability of any outcome.
        clear = sum(1 for s in styles if s["well_placed"] is True)
        strained = sum(1 for s in styles if s["well_placed"] is False)
        total = len(styles)
        pct = round(clear / total * 100) if total else 0
        return {
            "styles": styles,
            "clarity_pct": pct,
            "clear": clear,
            "strained": strained,
            "total": total,
            "note": (
                "Your make-up read from the governing grahas — how many express "
                "their higher nature. This is an internal reading of the chart's "
                "own signals (a doctrine assessment), not a probability of "
                "events."
            ),
        }
    except Exception:  # noqa: BLE001 — never block a reading
        return {}
